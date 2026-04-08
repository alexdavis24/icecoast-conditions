export default function App() {
  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">icecoastnicecoast.com</p>
        <h1>Ice Coast conditions, without the noise.</h1>
        <p className="lede">
          A public landing page for Northeast ski conditions is coming online.
          The first live release is intentionally small: fast static hosting,
          Cloudflare edge protection, and a private preview path for operators.
        </p>
      </section>

      <section className="panel">
        <h2>What is live now</h2>
        <ul>
          <li>Public frontend delivery through Cloudflare Pages</li>
          <li>Country-based edge blocking on the production hostname</li>
          <li>Cloudflare Access on the preview hostname</li>
        </ul>
      </section>

      <section className="panel">
        <h2>What comes next</h2>
        <ul>
          <li>Condition summaries for core Northeast mountains</li>
          <li>Operational monitoring and launch validation</li>
          <li>Future dynamic features as a separate project</li>
        </ul>
      </section>
    </main>
  );
}
