<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import KanbanBoard from '@/components/kanban/KanbanBoard.vue'
import { createKanbanEventsSocket, getKanbanBoard } from '@/services/api'

const board = ref([])
const kpis = ref({ total_cards: 0, closed_cards: 0, conversion_rate: 0, high_risk_cards: 0 })
const isLoading = ref(false)
const lastSync = ref(null)
const filters = reactive({
  monolith_view: 'john',
  stage: '',
  risk: '',
  assigned_to: '',
  min_value: '',
})

let socket = null

const activeFilters = computed(() => ({
  monolith_view: filters.monolith_view || undefined,
  stage: filters.stage || undefined,
  risk: filters.risk || undefined,
  assigned_to: filters.assigned_to || undefined,
  min_value: filters.min_value || undefined,
}))

async function loadBoard() {
  isLoading.value = true
  try {
    const { data } = await getKanbanBoard(activeFilters.value)
    board.value = data.columns || []
    kpis.value = data.kpis || kpis.value
    lastSync.value = new Date().toLocaleTimeString('pt-BR')
  } finally {
    isLoading.value = false
  }
}

function connectSocket() {
  socket = createKanbanEventsSocket()
  socket.onmessage = async () => {
    await loadBoard()
  }
}

function resetFilters() {
  filters.monolith_view = 'john'
  filters.stage = ''
  filters.risk = ''
  filters.assigned_to = ''
  filters.min_value = ''
  loadBoard()
}

onMounted(async () => {
  await loadBoard()
  connectSocket()
})

onBeforeUnmount(() => {
  if (socket) {
    socket.close()
  }
})
</script>

<template>
  <div class="kanban-page">
    <section class="hero-shell">
      <div>
        <p class="eyebrow">LICEU KANBAN GLOBAL</p>
        <h1>O board nasce dos eventos do ecossistema.</h1>
        <p class="hero-copy">
          Sem arrastar card para simular processo. Lead, negociação, proposta, jurídico e fechado refletem o estado real do fluxo multi-monólito.
        </p>
      </div>

      <div class="kpi-grid">
        <article>
          <span>Total</span>
          <strong>{{ kpis.total_cards }}</strong>
        </article>
        <article>
          <span>Fechados</span>
          <strong>{{ kpis.closed_cards }}</strong>
        </article>
        <article>
          <span>Conversão</span>
          <strong>{{ kpis.conversion_rate }}%</strong>
        </article>
        <article>
          <span>Risco alto</span>
          <strong>{{ kpis.high_risk_cards }}</strong>
        </article>
      </div>
    </section>

    <section class="filters-shell">
      <label>
        Visão
        <select v-model="filters.monolith_view" @change="loadBoard">
          <option value="john">John</option>
          <option value="archimedes">Archimedes</option>
          <option value="juridicotech">JuridicoTech</option>
          <option value="hubbackoffice">HubBackoffice</option>
        </select>
      </label>

      <label>
        Estágio
        <select v-model="filters.stage" @change="loadBoard">
          <option value="">Todos</option>
          <option value="leads">Leads</option>
          <option value="negotiation">Negociação</option>
          <option value="proposal">Proposta</option>
          <option value="juridico">Jurídico</option>
          <option value="closed">Fechado</option>
        </select>
      </label>

      <label>
        Risco
        <select v-model="filters.risk" @change="loadBoard">
          <option value="">Todos</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="unknown">Unknown</option>
        </select>
      </label>

      <label>
        Responsável
        <input v-model="filters.assigned_to" type="text" placeholder="corretor_1" @change="loadBoard" />
      </label>

      <label>
        Valor mínimo
        <input v-model="filters.min_value" type="number" min="0" step="1000" placeholder="1000000" @change="loadBoard" />
      </label>

      <button class="reset-btn" @click="resetFilters">Limpar filtros</button>
    </section>

    <section class="sync-shell">
      <span>{{ isLoading ? 'Sincronizando board...' : 'Board sincronizado em tempo real' }}</span>
      <span v-if="lastSync">Última leitura {{ lastSync }}</span>
    </section>

    <KanbanBoard :columns="board" />
  </div>
</template>

<style scoped>
.kanban-page {
  min-height: 100vh;
  padding: 2rem;
  background:
    radial-gradient(circle at top left, rgba(250, 204, 21, 0.24), transparent 30%),
    radial-gradient(circle at bottom right, rgba(14, 165, 233, 0.16), transparent 25%),
    linear-gradient(180deg, #f7efe3 0%, #f8fafc 60%, #eef2ff 100%);
  color: #0f172a;
  display: grid;
  gap: 1.4rem;
}

.hero-shell {
  display: grid;
  gap: 1.25rem;
}

.eyebrow {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-size: 0.78rem;
  color: #7c5c3b;
}

.hero-shell h1 {
  margin: 0.35rem 0 0.6rem;
  font-size: clamp(2rem, 4vw, 3.8rem);
  line-height: 0.95;
  font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
}

.hero-copy {
  max-width: 68ch;
  color: #334155;
  line-height: 1.6;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.9rem;
}

.kpi-grid article,
.filters-shell,
.sync-shell {
  border-radius: 24px;
  background: rgba(255,255,255,0.72);
  border: 1px solid rgba(124, 92, 59, 0.14);
  backdrop-filter: blur(14px);
}

.kpi-grid article {
  padding: 1rem;
  display: grid;
  gap: 0.35rem;
}

.kpi-grid span {
  font-size: 0.82rem;
  color: #7c5c3b;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.kpi-grid strong {
  font-size: 1.7rem;
}

.filters-shell {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 0.9rem;
  padding: 1rem;
}

.filters-shell label {
  display: grid;
  gap: 0.35rem;
  font-size: 0.82rem;
  color: #334155;
}

.filters-shell input,
.filters-shell select,
.reset-btn {
  min-height: 44px;
  border-radius: 14px;
  border: 1px solid rgba(15, 23, 42, 0.1);
  background: rgba(255,255,255,0.92);
  padding: 0 0.85rem;
}

.reset-btn {
  align-self: end;
  background: #0f172a;
  color: #f8fafc;
  cursor: pointer;
}

.sync-shell {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  padding: 0.85rem 1rem;
  color: #475569;
  font-size: 0.88rem;
}

@media (max-width: 1100px) {
  .kpi-grid,
  .filters-shell {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .kanban-page {
    padding: 1rem;
  }

  .kpi-grid,
  .filters-shell {
    grid-template-columns: 1fr;
  }

  .sync-shell {
    flex-direction: column;
  }
}
</style>