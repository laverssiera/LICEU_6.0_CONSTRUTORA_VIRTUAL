import PublicLayout from "../components/PublicLayout";

export default function SobreLiceu() {
  return (
    <PublicLayout title="Sobre a LICEU" subtitle="A LICEU 6.0 integra engenharia, financeiro e dados em escala industrial.">
      <section style={boxStyle}>
        <p style={{ marginTop: 0, color: "#cbd5e1" }}>
          Nosso papel e transformar operacao fragmentada em execucao integrada: da estrategia de portfolio a entrega em obra,
          com simulacao previa, aprovacao humana e rastreabilidade total.
        </p>
      </section>
    </PublicLayout>
  );
}

const boxStyle = {
  border: "1px solid #334155",
  borderRadius: 14,
  padding: 14,
  background: "rgba(15,23,42,0.92)",
};
