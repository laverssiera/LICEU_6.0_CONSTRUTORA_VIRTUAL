<script setup>
const props = defineProps({
  card: {
    type: Object,
    required: true,
  },
})

function money(value) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    maximumFractionDigits: 0,
  }).format(Number(value || 0))
}

</script>

<template>
  <article class="kanban-card">
    <header class="card-head">
      <div>
        <p class="card-eyebrow">{{ card.entity_type }} · {{ card.source }}</p>
        <h3>{{ card.title }}</h3>
      </div>
      <span class="risk-pill" :data-risk="card.risk">{{ card.risk }}</span>
    </header>

    <div class="card-meta">
      <span>{{ money(card.value) }}</span>
      <span v-if="card.assigned_to">Responsável: {{ card.assigned_to }}</span>
      <span v-else>Sem responsável</span>
    </div>

    <div class="status-grid">
      <span>Jurídico: {{ card.status.juridico || 'pending' }}</span>
      <span>Financeiro: {{ card.status.financeiro || 'pending' }}</span>
      <span>Marketing: {{ card.status.marketing || 'idle' }}</span>
    </div>

    <div v-if="card.alerts?.length" class="alerts-row">
      <span v-for="alert in card.alerts" :key="alert" class="alert-pill">{{ alert }}</span>
    </div>

    <section class="john-box">
      <strong>John</strong>
      <p>{{ card.john.action }}</p>
      <small>Confiança {{ Math.round((card.john.confidence || 0) * 100) }}%</small>
    </section>

    <section class="actors-box">
      <strong>Atores</strong>
      <div class="actors-list">
        <span v-for="actor in card.actors" :key="actor.monolith" class="actor-chip">
          {{ actor.monolith }} · {{ actor.status }}
        </span>
      </div>
    </section>

    <section class="timeline-box">
      <strong>Timeline</strong>
      <ol>
        <li v-for="item in card.timeline" :key="item.id">
          <span>{{ item.event_type }}</span>
        </li>
      </ol>
    </section>
  </article>
</template>

<style scoped>
.kanban-card {
  display: grid;
  gap: 0.9rem;
  padding: 1rem;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(244,242,237,0.95));
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
}

.card-head {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.card-head h3 {
  margin: 0.2rem 0 0;
  font-size: 1.02rem;
  line-height: 1.2;
}

.card-eyebrow {
  margin: 0;
  font-size: 0.74rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #7c5c3b;
}

.risk-pill,
.alert-pill,
.actor-chip {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.28rem 0.62rem;
  font-size: 0.75rem;
}

.risk-pill {
  background: #efe4d4;
  color: #7a4b1f;
  text-transform: uppercase;
}

.risk-pill[data-risk='high'] {
  background: #ffe0d7;
  color: #a33b21;
}

.risk-pill[data-risk='medium'] {
  background: #fff0c2;
  color: #8a6800;
}

.card-meta,
.status-grid {
  display: grid;
  gap: 0.35rem;
  font-size: 0.83rem;
  color: #334155;
}

.status-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.alerts-row,
.actors-list {
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.alert-pill {
  background: #fee2e2;
  color: #991b1b;
}

.actor-chip {
  background: #e2e8f0;
  color: #1e293b;
}

.john-box,
.actors-box,
.timeline-box {
  display: grid;
  gap: 0.35rem;
}

.john-box strong,
.actors-box strong,
.timeline-box strong {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #0f172a;
}

.john-box p,
.timeline-box ol {
  margin: 0;
}

.timeline-box ol {
  padding-left: 1.1rem;
  display: grid;
  gap: 0.2rem;
  color: #475569;
  font-size: 0.82rem;
}
</style>