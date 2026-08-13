export default function Card({ title, desc }) {
  return (
    <article className="tech-card">
      <h3>{title}</h3>
      <p style={{ marginBottom: 0 }}>{desc}</p>
    </article>
  );
}
