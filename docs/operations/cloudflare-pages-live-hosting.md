# Cloudflare Pages Live Hosting

## Purpose

This runbook explains how to publish the frontend to Cloudflare Pages at
`icecoastnicecoast.com`, how to expose `preview.icecoastnicecoast.com` through
Cloudflare Access, and how to block non-approved countries on the production
hostname.

## Pages Project

- Project name: `icecoastnicecoast-frontend`
- Framework preset: `Vite`
- Root directory: `src/frontend`
- Build command: `npm run build`
- Build output directory: `dist`

## Custom Domains

- Production: `icecoastnicecoast.com`
- Preview: `preview.icecoastnicecoast.com`

## Country Allowlist

The production hostname must allow only explicit ISO country codes. The final
rule should include:

- `US`
- `CA`
- `AD`, `AL`, `AT`, `BA`, `BE`, `BG`, `CH`, `CY`, `CZ`, `DE`, `DK`, `EE`,
  `ES`, `FI`, `FR`, `GB`, `GR`, `HR`, `HU`, `IE`, `IS`, `IT`, `LI`, `LT`,
  `LU`, `LV`, `MC`, `ME`, `MK`, `MT`, `NL`, `NO`, `PL`, `PT`, `RO`, `RS`,
  `SE`, `SI`, `SK`, `SM`, `UA`, `VA`

## WAF Rule Shape

Apply the rule only to `icecoastnicecoast.com`. Do not apply it to the preview
hostname.

Example expression shape:

```text
(http.host eq "icecoastnicecoast.com" and ip.geoip.country ne "US" and ip.geoip.country ne "CA" ...)
```

Exact launch allowlist expression:

```text
(http.host eq "icecoastnicecoast.com" and not ip.geoip.country in {"US" "CA" "AD" "AL" "AT" "BA" "BE" "BG" "CH" "CY" "CZ" "DE" "DK" "EE" "ES" "FI" "FR" "GB" "GR" "HR" "HU" "IE" "IS" "IT" "LI" "LT" "LU" "LV" "MC" "ME" "MK" "MT" "NL" "NO" "PL" "PT" "RO" "RS" "SE" "SI" "SK" "SM" "UA" "VA"})
```

Action: `Block`

## Access Application

- Application type: self-hosted
- Domain: `preview.icecoastnicecoast.com`
- Policy: allow only the operator identity allowlist

## Verification Checklist

1. `npm run build` succeeds in `src/frontend`
2. Production hostname loads from an allowed region
3. Production hostname is blocked from a disallowed region
4. Preview hostname prompts for Access login
5. Preview hostname is reachable after successful login from a disallowed region

## Manual Launch Checklist

- Pages project created
- Production domain attached
- Preview domain attached
- Production WAF country rule enabled
- Preview Access application enabled
- Allowed-region test passed
- Blocked-region test passed
- Access bypass test passed
