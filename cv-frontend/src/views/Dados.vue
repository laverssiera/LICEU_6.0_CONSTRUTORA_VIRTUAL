<template>
  <div class="portal-page data-page">
    <header class="page-header">
      <button class="back-btn" @click="$router.push('/archimedes')">← Voltar para a jornada</button>
      <span class="eyebrow">3C273 CEFEIDA</span>
      <h1>Dados, inteligência e leitura estratégica</h1>
      <p>
        Acesse indicadores, insights e sinais operacionais que ajudam o John a orientar a jornada do cliente.
      </p>
    </header>

    <section class="dashboard-grid">
      <article v-for="card in cards" :key="card.title" class="data-card">
        <div class="icon">{{ card.icon }}</div>
        <h2>{{ card.title }}</h2>
        <p>{{ card.text }}</p>
      </article>
    </section>
  </div>
</template>

<script setup>
const cards = [
  { icon: '📊', title: 'Radar de demanda', text: 'Leitura contínua de interesse do mercado por localização, perfil e produto.' },
  { icon: '🧠', title: 'Insights do John', text: 'Eventos e decisões assistidas com contexto operacional consolidado.' },
  { icon: '📍', title: 'Viabilidade territorial', text: 'Consolidação de sinais de terrenos, acesso urbano e potencial de retorno.' },
  { icon: '⚡', title: 'Telemetria ao vivo', text: 'Acompanhamento instantâneo do ecossistema LICEU 6.0 e dos fluxos ativos.' }
]
</script>

<style scoped>
.portal-page {
  min-height: 100vh;
  padding: 32px 5%;
  background: linear-gradient(180deg, #eff6ff, #f8fafc);
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
.data-card p {
  color: #556476;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.data-card {
  background: white;
  border-radius: 18px;
  border: 1px solid #dbe4ee;
  padding: 20px;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);
}

.icon {
  font-size: 2rem;
  margin-bottom: 10px;
}

.data-card h2 {
  color: #133a5e;
  margin-bottom: 8px;
}
</style>
