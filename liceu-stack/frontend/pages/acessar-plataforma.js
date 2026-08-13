import { useRouter } from "next/router";

import PublicLayout from "../components/PublicLayout";

export default function AcessarPlataforma() {
  const router = useRouter();

  return (
    <PublicLayout title="Acessar Plataforma" subtitle="Entrada oficial para o workspace interno LICEU 6.0.">
      <section style={{ display: "grid", gap: 12, maxWidth: 560 }}>
        <button
          onClick={() => router.push("/workspace")}
          style={{ border: "1px solid #0ea5e9", borderRadius: 10, padding: "12px 14px", background: "linear-gradient(90deg, #0369a1, #0ea5e9)", color: "#f8fafc", fontWeight: 700, cursor: "pointer" }}
        >
          Entrar no Workspace
        </button>
      </section>
    </PublicLayout>
  );
}
