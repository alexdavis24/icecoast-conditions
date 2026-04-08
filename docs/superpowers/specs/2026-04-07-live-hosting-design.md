# Live Hosting Design

## Goal

Expose the frontend at `icecoastnicecoast.com` on the public internet using Cloudflare, while dropping traffic from non-approved geographies by default and preserving a private operator access path through Cloudflare Access.

## Scope

This design covers:

- Public hosting for the frontend website only
- Edge-layer traffic controls in Cloudflare
- A private Access-protected hostname for operator access
- Deployment and verification requirements for the initial launch

This design does not cover:

- Public API exposure
- Backend hosting for public traffic
- Application-layer geolocation logic
- Full infrastructure-as-code automation for Cloudflare resources

## Recommended Approach

Use Cloudflare Pages to host the Vite frontend from `src/frontend`, bind the production custom domain `icecoastnicecoast.com` to that Pages project, and enforce geography-based access with Cloudflare edge rules. Add a second hostname, `preview.icecoastnicecoast.com`, backed by the same Pages project but protected by Cloudflare Access. The public hostname will allow only explicitly listed countries and block the rest. The preview hostname will be exempt from the country block and require successful Access authentication.

This is the lowest-complexity option because the current public requirement is a frontend website only. It avoids running and securing an origin server, keeps TLS and DNS inside Cloudflare, and places the access policy where it belongs: at the edge.

## Architecture

### Public Site

- Build the frontend in `src/frontend`
- Deploy the build output to a Cloudflare Pages project
- Attach `icecoastnicecoast.com` as the production custom domain
- Serve only static frontend assets on the public hostname

### Private Access Path

- Create `preview.icecoastnicecoast.com` as a second custom domain on the same Pages project
- Protect that hostname with a Cloudflare Access application
- Require successful login before serving the site on that hostname
- Do not apply the country block rule to the preview hostname

### Backend Posture

- Keep the existing FastAPI backend out of the public internet path for this launch
- Do not publish `api.icecoastnicecoast.com`
- Treat any backend deployment as a separate future project with its own design and plan

## Traffic Policy

### Public Hostname Policy

The production hostname `icecoastnicecoast.com` should be reachable only from approved countries. Cloudflare should enforce this before any request is served.

Allowlist contents:

- United States (`US`)
- Canada (`CA`)
- European countries, listed explicitly in the final Cloudflare rule rather than described loosely as "Europe"

Action:

- Block disallowed countries at the Cloudflare edge
- Do not implement an application-level fallback page
- Do not expose a bypass on the public hostname

The final implementation should use exact country codes in the Cloudflare rule. This avoids ambiguity around partial-European geographies and makes the policy auditable.

### Preview Hostname Policy

The preview hostname `preview.icecoastnicecoast.com` exists to provide operator access from anywhere, including blocked geographies.

Requirements:

- Protected by Cloudflare Access
- Exempt from the production country block rule
- Restricted to the operator identity policy configured in Cloudflare Access

Recommended initial Access policy:

- Allow only the owner email identity or an explicitly defined small allowlist

## Cloudflare Configuration Model

### Pages

- Create one Cloudflare Pages project for the frontend
- Build command: `npm run build`
- Output directory: `dist`
- Root directory: `src/frontend`

### DNS and Domains

- Keep authoritative DNS in Cloudflare
- Configure `icecoastnicecoast.com` as the production domain
- Configure `preview.icecoastnicecoast.com` as the private preview domain

### Security Controls

- Add a hostname-scoped WAF or custom rule for `icecoastnicecoast.com`
- Rule logic should allow only the configured country code allowlist
- Rule action should block the rest
- Exclude `preview.icecoastnicecoast.com` from that rule

### Access

- Create a Cloudflare Access self-hosted application for `preview.icecoastnicecoast.com`
- Require login before access is granted
- Use a narrow identity allowlist for the initial launch

## Deployment Shape

### Initial Delivery

The first working version should include:

- Frontend deployment to Cloudflare Pages
- Production custom domain binding
- Preview custom domain binding
- Country-based edge block rule for production
- Cloudflare Access protection for preview
- Documentation in the repo that explains how the Cloudflare setup is configured and verified

### Deployment Workflow

Two acceptable deployment models:

1. Git-connected Pages deployment from the repository
2. CI-driven deployment from GitHub Actions

The initial implementation should choose one and document it clearly. The key requirement is repeatable deployment, not full infrastructure automation on day one.

## Verification Requirements

### Build Verification

- Confirm the frontend builds successfully from `src/frontend`
- Confirm the Pages deployment serves the expected static site

### Access Verification

- From an allowed geography, verify `icecoastnicecoast.com` loads normally
- From a blocked geography or equivalent VPN exit node, verify the public hostname is blocked
- From a blocked geography or equivalent VPN exit node, verify `preview.icecoastnicecoast.com` allows entry after successful Cloudflare Access authentication

### Exposure Verification

- Confirm there is no public API hostname for launch
- Confirm the backend is not part of the public request path

### Monitoring Verification

- Review Cloudflare analytics and security events after launch
- Confirm blocked traffic appears in Cloudflare telemetry
- Adjust the country allowlist only if legitimate traffic is being denied

## Risks and Decisions

### Explicit Country List Maintenance

The phrase "Europe" is not a valid Cloudflare rule primitive. The implementation must convert that policy into a concrete list of ISO country codes. That list becomes part of the repo documentation and should be reviewed deliberately.

### Access Bypass Scope

The Access-protected preview hostname is the only approved bypass. The public hostname should not gain special exceptions for operator travel, VPN endpoints, or ad hoc IP allowlists unless a future design explicitly adds them.

### Backend Deferral

If the product later requires dynamic features, a separate design should determine whether to use Workers, a private API behind Cloudflare, or another hosting model. That is intentionally deferred here to keep the initial launch small and defensible.

## Implementation Notes

The implementation plan should cover:

- Frontend build and deploy readiness for Cloudflare Pages
- Any repo changes needed for Pages build configuration
- Operations documentation for Cloudflare Pages, DNS, WAF rule creation, and Access application setup
- Verification steps for allowed-country access, blocked-country denial, and Access-protected preview access

The implementation plan should not include backend feature work or application-layer geofencing logic.
