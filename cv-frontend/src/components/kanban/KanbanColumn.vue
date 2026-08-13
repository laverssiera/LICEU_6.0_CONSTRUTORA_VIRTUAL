<script setup>
import KanbanCard from '@/components/kanban/KanbanCard.vue'

defineProps({
  column: {
    type: Object,
    required: true,
  },
})
</script>

<template>
  <section class="kanban-column">
    <header class="column-head">
      <div>
        <p>{{ column.title }}</p>
        <strong>{{ column.items.length }} cards</strong>
      </div>
    </header>

    <div class="column-body">
      <KanbanCard v-for="card in column.items" :key="card.id" :card="card" />
      <div v-if="!column.items.length" class="empty-state">Sem cards nesta etapa.</div>
    </div>
  </section>
</template>

<style scoped>
.kanban-column {
  min-width: 300px;
  display: grid;
  gap: 1rem;
  padding: 1rem;
  border-radius: 28px;
  background: rgba(255, 250, 240, 0.74);
  border: 1px solid rgba(124, 92, 59, 0.15);
  backdrop-filter: blur(18px);
}

.column-head p {
  margin: 0;
  font-size: 0.76rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #7c5c3b;
}

.column-head strong {
  color: #0f172a;
  font-size: 1rem;
}

.column-body {
  display: grid;
  gap: 0.9rem;
}

.empty-state {
  border-radius: 18px;
  padding: 1rem;
  background: rgba(255,255,255,0.65);
  color: #64748b;
  font-size: 0.88rem;
}
</style>