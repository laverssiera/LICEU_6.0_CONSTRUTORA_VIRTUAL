import Link from "next/link";

const LINKS = [
  { href: "/", label: "Home" },
  { href: "/clientes", label: "Clientes" },
  { href: "/fornecedores", label: "Fornecedores" },
  { href: "/carreiras", label: "Carreiras" },
  { href: "/esg", label: "ESG" },
  { href: "/academia-do-saber", label: "Academia do Saber" },
  { href: "/sobre-a-liceu", label: "Sobre a LICEU" },
  { href: "/acessar-plataforma", label: "Acessar Plataforma" },
];

export default function PublicLayout({ title, subtitle, children }) {
  return (
    <main
      style={{
        minHeight: "100vh",
        color: "#f8fafc",
        background:
          "radial-gradient(circle at 20% 20%, #14532d 0%, #0b1220 35%), radial-gradient(circle at 80% 10%, #1d4ed8 0%, rgba(11,18,32,1) 30%), linear-gradient(120deg, #020617, #0f172a)",
        fontFamily: "'Space Grotesk', 'IBM Plex Sans', 'Trebuchet MS', sans-serif",
      }}
    >
      <header style={{ position: "sticky", top: 0, zIndex: 10, backdropFilter: "blur(8px)", background: "rgba(2,6,23,0.7)", borderBottom: "1px solid #1e293b" }}>
        <div style={{ maxWidth: 1140, margin: "0 auto", padding: "14px 20px", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
          <Link href="/" style={{ color: "#ecfeff", textDecoration: "none", fontWeight: 800, letterSpacing: 0.5 }}>
            LICEU 6.0
          </Link>
          <nav style={{ display: "flex", gap: 14, flexWrap: "wrap", justifyContent: "flex-end" }}>
            {LINKS.map((link) => (
              <Link key={link.href} href={link.href} style={{ color: "#cbd5e1", textDecoration: "none", fontSize: 14 }}>
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      <section style={{ maxWidth: 1140, margin: "0 auto", padding: "28px 20px 10px" }}>
        <h1 style={{ margin: 0, fontSize: "clamp(2rem, 4vw, 3.2rem)", lineHeight: 1.1 }}>{title}</h1>
        {subtitle && <p style={{ marginTop: 10, color: "#cbd5e1", maxWidth: 820 }}>{subtitle}</p>}
      </section>

      <section style={{ maxWidth: 1140, margin: "0 auto", padding: "10px 20px 34px" }}>{children}</section>
    </main>
  );
}
