export default function LeadForm() {
  return (
    <form style={{ maxWidth: 420, marginTop: 20, marginBottom: 24 }}>
      <input className="form-field" placeholder="Nome" />
      <input className="form-field" placeholder="Email" />
      <input className="form-field" placeholder="Empresa" />

      <button className="btn-primary" type="submit">
        Continuar
      </button>
    </form>
  );
}
