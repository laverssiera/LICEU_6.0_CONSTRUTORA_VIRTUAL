<template>
  <div class="portal-page legal-page">
    <header class="page-header">
      <button class="back-btn" @click="$router.push('/archimedes')">← Voltar para a jornada</button>
      <span class="eyebrow">JURIDICOTECH</span>
      <h1>Jurídico, contratos e compliance</h1>
      <p>
        O cliente acompanha aprovações, documentos e marcos regulatórios com segurança e clareza.
      </p>
    </header>

    <section class="timeline-grid">
      <article v-for="step in steps" :key="step.title" class="timeline-card">
        <strong>{{ step.title }}</strong>
        <p>{{ step.text }}</p>
      </article>
    </section>
  </div>
</template>

<script setup>
const steps = [
  { title: 'Documentação inicial', text: 'Checklist de titularidade, matrícula e conformidade cadastral.' },
  { title: 'Validação contratual', text: 'Aprovação dos documentos da jornada e assinatura orientada.' },
  { title: 'Compliance da operação', text: 'Acompanhamento dos controles e requisitos do projeto.' },
  { title: 'Entrega regulatória', text: 'Fechamento da etapa com rastreabilidade e segurança jurídica.' }
]
</script>

<style scoped>
.portal-page {
  min-height: 100vh;
  padding: 32px 5%;
  background: linear-gradient(180deg, #fff7ed, #f8fafc);
}

.page-header {
  max-width: 860px;
  display: grid;
  gap: 10px;
  margin-bottom: 24px;
}

.back-btn {
  width: fit-content;
  border: none;
  background: transparent;
  color: #133a5e;
  font-weight: 800;
  cursor: pointer;
}

.eyebrow {
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: #c53030;
}

h1 {
  font-size: clamp(2rem, 4vw, 3rem);
  color: #133a5e;
}

.page-header p,
.timeline-card p {
  color: #5f6d7d;
}

.timeline-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.timeline-card {
  background: white;
  border-radius: 18px;
  border: 1px solid #f1d6bc;
  padding: 20px;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);
}

.timeline-card strong {
  color: #133a5e;
  display: block;
  margin-bottom: 8px;
}
</style>
