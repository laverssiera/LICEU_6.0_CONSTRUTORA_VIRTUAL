import { useMemo, useState } from "react";
import { useRouter } from "next/router";

export default function LeadForm({ modulePath = "/workspace", intent = "Quero evoluir com a LICEU" }) {
  const router = useRouter();
  const [form, setForm] = useState({ nome: "", email: "", empresa: "" });
  const [loading, setLoading] = useState(false);

  const disabled = useMemo(() => !form.nome || !form.email || !form.empresa || loading, [form, loading]);

  const onSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    router.push(modulePath);
  };

  return (
    <form onSubmit={onSubmit} style={{ background: "rgba(15,23,42,0.86)", border: "1px solid #334155", borderRadius: 16, padding: 16, display: "grid", gap: 10 }}>
      <div style={{ fontWeight: 700 }}>{intent}</div>
      <input placeholder="Nome" value={form.nome} onChange={(e) => setForm({ ...form, nome: e.target.value })} style={inputStyle} />
      <input placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} style={inputStyle} />
      <input placeholder="Empresa" value={form.empresa} onChange={(e) => setForm({ ...form, empresa: e.target.value })} style={inputStyle} />
      <button type="submit" disabled={disabled} style={{ ...buttonStyle, opacity: disabled ? 0.65 : 1 }}>
        {loading ? "Redirecionando..." : "Continuar"}
      </button>
    </form>
  );
}

const inputStyle = {
  border: "1px solid #475569",
  borderRadius: 10,
  padding: "10px 12px",
  background: "#0f172a",
  color: "#f8fafc",
};

const buttonStyle = {
  border: "1px solid #0369a1",
  borderRadius: 10,
  padding: "10px 12px",
  background: "linear-gradient(90deg, #0284c7, #0ea5e9)",
  color: "#f8fafc",
  fontWeight: 700,
  cursor: "pointer",
};
