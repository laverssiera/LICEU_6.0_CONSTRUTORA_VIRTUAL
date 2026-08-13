<script setup>
import KanbanColumn from '@/components/kanban/KanbanColumn.vue'

defineProps({
  columns: {
    type: Array,
    required: true,
  },
})
</script>

<template>
  <div class="kanban-board">
    <KanbanColumn v-for="column in columns" :key="column.id" :column="column" />
  </div>
</template>

<style scoped>
.kanban-board {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: minmax(300px, 1fr);
  gap: 1rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
}

.kanban-board::-webkit-scrollbar {
  height: 10px;
}

.kanban-board::-webkit-scrollbar-thumb {
  background: rgba(124, 92, 59, 0.35);
  border-radius: 999px;
}
</style>