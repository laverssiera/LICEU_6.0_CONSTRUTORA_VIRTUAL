import Link from "next/link";

export default function Navbar() {
  return (
    <nav className="site-nav">
      <div className="site-nav-inner">
        <div className="site-brand">LICEU 6.0</div>

        <div className="site-nav-links">
          <Link href="/">Home</Link>
          <Link href="/clientes">Clientes</Link>
          <Link href="/investidores">Investidores</Link>
          <Link href="/fornecedores">Fornecedores</Link>
          <Link href="/carreiras">Carreiras</Link>
          <Link href="/tecnologia">Tecnologia</Link>
          <Link href="/workspace">Plataforma</Link>
        </div>
      </div>
    </nav>
  );
}
