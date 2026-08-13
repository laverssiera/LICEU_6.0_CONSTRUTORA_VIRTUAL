<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { getStrategicKanbanBoard, getStrategicSuggestion, moveStrategicKanbanCardStage } from '@/services/api'

const isLoading = ref(false)
const isMovingCard = ref(false)
const board = ref({ columns: [], totals: {}, kpis: {} })
const lastSync = ref('')
const errorMessage = ref('')
const movingMessage = ref('')
const dragging = ref({ cardId: null, fromStage: null })
const isLoadingSuggestion = ref(false)
const suggestionError = ref('')
const selectedCardId = ref('')
const suggestionPanel = ref(null)

const filters = reactive({
  portfolio: 'strategic_planning',
  monolith: '',
  actor: '',
  stage: '',
})

const activeFilters = computed(() => ({
  portfolio: filters.portfolio || undefined,
  monolith: filters.monolith || undefined,
  actor: filters.actor || undefined,
  stage: filters.stage || undefined,
}))

const strategicSummary = computed(() => {
  const kpis = board.value.kpis || {}
  const totals = board.value.totals || {}
  const total = Number(kpis.total_cards || 0)
  const done = Number(kpis.done_cards || 0)
  const executing = Number(kpis.executing_cards || 0)
  const validating = Number(totals.validating || 0)
  const planning = Number(totals.planning || 0)
  const completionRate = total === 0 ? 0 : Math.round((done / total) * 100)

  return {
    total,
    done,
    executing,
    validating,
    planning,
    completionRate,
  }
})

const alerts = computed(() => {
  const items = []
  const summary = strategicSummary.value

  if (summary.executing > summary.done) {
    items.push({
      level: 'attention',
      title: 'Execucao acima da finalizacao',
      description: 'Existem mais iniciativas executando do que concluídas. Reforce checkpoints de validacao.',
    })
  }

  if (summary.validating === 0 && summary.executing > 0) {
    items.push({
      level: 'risk',
      title: 'Fila de validacao vazia',
      description: 'Fluxos em execucao ainda nao migraram para validating. Pode haver gargalo de qualidade.',
    })
  }

  if (summary.planning > summary.executing + summary.done) {
    items.push({
      level: 'info',
      title: 'Planejamento acima da capacidade atual',
      description: 'Priorize as iniciativas de maior impacto para reduzir backlog de planejamento.',
    })
  }

  if (items.length === 0) {
    items.push({
      level: 'ok',
      title: 'Operacao estrategica equilibrada',
      description: 'Os indicadores estao consistentes com o ritmo de entrega planejado.',
    })
  }

  return items
})

function normalizeStrategicEntityType(item) {
  if (item?.context?.entity_type) return String(item.context.entity_type)
  return String(item?.entity_type || '').replace(/^strategic_/, '')
}

function resolveSuggestionCandidate(columns) {
  const preferredOrder = ['executing', 'planning', 'validating', 'backlog', 'done']
  for (const stage of preferredOrder) {
    const column = (columns || []).find((entry) => entry.id === stage)
    if (column?.items?.length) {
      return column.items[0]
    }
  }
  return null
}

async function loadJohnSuggestionForItem(item, options = {}) {
  if (!item) {
    suggestionPanel.value = null
    selectedCardId.value = ''
    return
  }

  const entityType = normalizeStrategicEntityType(item)
  const entityId = item?.context?.entity_id
  if (!entityType || entityId === undefined || entityId === null) {
    suggestionPanel.value = null
    selectedCardId.value = ''
    return
  }

  selectedCardId.value = item.id
  isLoadingSuggestion.value = true
  suggestionError.value = ''

  try {
    const { data } = await getStrategicSuggestion(entityType, entityId, {
      focus: options.focus || 'priorizacao e proximo passo',
    })
    suggestionPanel.value = {
      ...data,
      card: item,
      entityType,
      entityId,
    }
  } catch (error) {
    if (!options.silent) {
      suggestionError.value = 'Nao foi possivel carregar a recomendacao do John para este item.'
    }
  } finally {
    isLoadingSuggestion.value = false
  }
}

async function loadStrategicBoard() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const { data } = await getStrategicKanbanBoard(activeFilters.value)
    board.value = {
      columns: data.columns || [],
      totals: data.totals || {},
      kpis: data.kpis || {},
    }
    await loadJohnSuggestionForItem(resolveSuggestionCandidate(data.columns || []), {
      silent: true,
      focus: 'priorizacao executiva',
    })
    lastSync.value = new Date().toLocaleTimeString('pt-BR')
  } catch (error) {
    errorMessage.value = 'Nao foi possivel carregar o dashboard estrategico agora.'
  } finally {
    isLoading.value = false
  }
}

function cloneBoardState() {
  return JSON.parse(JSON.stringify(board.value))
}

function findColumnByStage(columns, stage) {
  return columns.find((column) => column.id === stage)
}

function recomputeBoardMetrics(columns) {
  const totals = {}
  for (const column of columns) {
    totals[column.id] = Array.isArray(column.items) ? column.items.length : 0
  }

  const totalCards = Object.values(totals).reduce((acc, value) => acc + Number(value || 0), 0)
  board.value.totals = totals
  board.value.kpis = {
    ...board.value.kpis,
    total_cards: totalCards,
    done_cards: Number(totals.done || 0),
    executing_cards: Number(totals.executing || 0),
  }
}

function applyOptimisticMove(cardId, fromStage, targetStage) {
  const columns = board.value.columns || []
  const source = findColumnByStage(columns, fromStage)
  const target = findColumnByStage(columns, targetStage)
  if (!source || !target) return false

  const index = source.items.findIndex((item) => item.id === cardId)
  if (index < 0) return false

  const [card] = source.items.splice(index, 1)
  card.stage = targetStage
  target.items.unshift(card)
  recomputeBoardMetrics(columns)
  return true
}

function onDragStart(event, card, stage) {
  dragging.value = { cardId: card.id, fromStage: stage }
  if (event?.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(card.id))
  }
}

function onDragOver(event) {
  event.preventDefault()
}

async function onDrop(stage) {
  if (!dragging.value.cardId || !dragging.value.fromStage) return
  if (dragging.value.fromStage === stage || isMovingCard.value) {
    dragging.value = { cardId: null, fromStage: null }
    return
  }

  const backup = cloneBoardState()
  const moved = applyOptimisticMove(dragging.value.cardId, dragging.value.fromStage, stage)
  if (!moved) {
    dragging.value = { cardId: null, fromStage: null }
    return
  }

  isMovingCard.value = true
  movingMessage.value = 'Persistindo mudanca de estagio...'
  errorMessage.value = ''

  try {
    await moveStrategicKanbanCardStage(dragging.value.cardId, stage)
    const movedCard = (board.value.columns || []).flatMap((column) => column.items || []).find((item) => item.id === dragging.value.cardId)
    await loadJohnSuggestionForItem(movedCard, { silent: true, focus: 'impacto da mudanca de estagio' })
    lastSync.value = new Date().toLocaleTimeString('pt-BR')
  } catch (error) {
    board.value = backup
    errorMessage.value = 'Nao foi possivel mover o card. O board voltou ao estado anterior.'
  } finally {
    isMovingCard.value = false
    movingMessage.value = ''
    dragging.value = { cardId: null, fromStage: null }
  }
}

function selectCard(item) {
  loadJohnSuggestionForItem(item)
}

function resetFilters() {
  filters.portfolio = 'strategic_planning'
  filters.monolith = ''
  filters.actor = ''
  filters.stage = ''
  loadStrategicBoard()
}

onMounted(() => {
  loadStrategicBoard()
})
</script>

<template>
  <section class="strategic-page">
    <header class="hero">
      <div>
        <p class="eyebrow">Planejamento Estrategico</p>
        <h1>Painel estrategico com pulso de execucao em tempo real.</h1>
        <p class="subtitle">
          Uma leitura unica de portfolio, monolitos e atores com foco em entrega real, nao apenas em atividade.
        </p>
      </div>
      <button class="refresh-btn" :disabled="isLoading" @click="loadStrategicBoard">
        {{ isLoading ? 'Atualizando...' : 'Atualizar dashboard' }}
      </button>
    </header>

    <section class="kpi-grid">
      <article>
        <span>Total de cards</span>
        <strong>{{ strategicSummary.total }}</strong>
      </article>
      <article>
        <span>Concluidos</span>
        <strong>{{ strategicSummary.done }}</strong>
      </article>
      <article>
        <span>Executando</span>
        <strong>{{ strategicSummary.executing }}</strong>
      </article>
      <article>
        <span>Taxa de conclusao</span>
        <strong>{{ strategicSummary.completionRate }}%</strong>
      </article>
    </section>

    <section class="filters-shell">
      <label>
        Portfolio
        <input v-model="filters.portfolio" type="text" placeholder="strategic_planning" @change="loadStrategicBoard" />
      </label>

      <label>
        Monolito
        <select v-model="filters.monolith" @change="loadStrategicBoard">
          <option value="">Todos</option>
          <option value="opera">OPERA</option>
          <option value="pdi_ia">P&D</option>
          <option value="academia_saber">Academia</option>
          <option value="hub_contabil">HUB</option>
          <option value="cefeida">CEFEIDA</option>
        </select>
      </label>

      <label>
        Ator
        <input v-model="filters.actor" type="text" placeholder="owner ou assigned_to" @change="loadStrategicBoard" />
      </label>

      <label>
        Estagio
        <select v-model="filters.stage" @change="loadStrategicBoard">
          <option value="">Todos</option>
          <option value="backlog">Backlog</option>
          <option value="planning">Planning</option>
          <option value="executing">Executing</option>
          <option value="validating">Validating</option>
          <option value="done">Done</option>
        </select>
      </label>

      <button class="reset-btn" @click="resetFilters">Limpar filtros</button>
    </section>

    <section class="alerts-shell">
      <header>
        <h2>Alertas estrategicos</h2>
        <small v-if="lastSync">Ultima leitura: {{ lastSync }}</small>
      </header>
      <article
        v-for="alert in alerts"
        :key="alert.title"
        :class="['alert-card', `level-${alert.level}`]"
      >
        <h3>{{ alert.title }}</h3>
        <p>{{ alert.description }}</p>
      </article>
    </section>

    <p v-if="errorMessage" class="error-box">{{ errorMessage }}</p>
    <p v-if="movingMessage" class="info-box">{{ movingMessage }}</p>

    <section class="john-shell">
      <header>
        <div>
          <p class="eyebrow">John Estrategico</p>
          <h2>Recomendacao contextual por card</h2>
        </div>
        <small v-if="suggestionPanel?.suggestion?.target_monolith">
          Monolito: {{ suggestionPanel.suggestion.target_monolith }}
        </small>
      </header>

      <p v-if="isLoadingSuggestion" class="info-box">Consultando recomendacao do John...</p>
      <p v-else-if="suggestionError" class="error-box">{{ suggestionError }}</p>

      <article v-else-if="suggestionPanel" class="john-card">
        <div class="john-headline">
          <strong>{{ suggestionPanel.card?.title || suggestionPanel.entity?.name || 'Item estrategico' }}</strong>
          <span>{{ suggestionPanel.suggestion.entity_type }} #{{ suggestionPanel.suggestion.entity_id }}</span>
        </div>

        <p class="john-summary">{{ suggestionPanel.suggestion.summary }}</p>

        <div class="john-metrics">
          <span>Acao: {{ suggestionPanel.suggestion.recommended_action }}</span>
          <span>Risco: {{ suggestionPanel.suggestion.risk }}</span>
          <span>Confianca: {{ Math.round((suggestionPanel.suggestion.confidence || 0) * 100) }}%</span>
          <span>John alvo: {{ suggestionPanel.suggestion.target_john }}</span>
        </div>

        <small>
          Foco: {{ suggestionPanel.suggestion.focus }} • Tenant: {{ suggestionPanel.suggestion.context?.tenant }}
        </small>
      </article>

      <div v-else class="column-empty">
        Selecione um card do board para consultar a recomendacao do John.
      </div>
    </section>

    <section class="board-shell">
      <article
        v-for="column in board.columns"
        :key="column.id"
        class="column-card"
        @dragover="onDragOver"
        @drop="onDrop(column.id)"
      >
        <header>
          <h3>{{ column.title }}</h3>
          <span>{{ column.items.length }}</span>
        </header>

        <div v-if="column.items.length === 0" class="column-empty">
          Sem itens neste estagio.
        </div>

        <ul v-else>
          <li
            v-for="item in column.items"
            :key="item.id"
            :class="['work-item', { selected: selectedCardId === item.id }]"
            draggable="true"
            @dragstart="onDragStart($event, item, column.id)"
            @click="selectCard(item)"
          >
            <strong>{{ item.title }}</strong>
            <small>{{ item.entity_type }}</small>
            <small>owner: {{ item.owner || '-' }}</small>
            <small>ator: {{ item.assigned_to || '-' }}</small>
            <small v-if="item.john?.action">john: {{ item.john.action }}</small>
          </li>
        </ul>
      </article>
    </section>
  </section>
</template>

<style scoped>
.strategic-page {
  min-height: 100vh;
  padding: 1.5rem;
  display: grid;
  gap: 1rem;
  color: #111827;
  background:
    radial-gradient(circle at 12% 12%, rgba(180, 83, 9, 0.16), transparent 30%),
    radial-gradient(circle at 88% 20%, rgba(15, 118, 110, 0.16), transparent 32%),
    linear-gradient(180deg, #fefaf3 0%, #f8fafc 50%, #f2f7ff 100%);
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-size: 0.72rem;
  color: #92400e;
  margin: 0;
}

.hero h1 {
  margin: 0.35rem 0;
  font-size: clamp(1.8rem, 4vw, 3.1rem);
  line-height: 1;
  font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
}

.subtitle {
  margin: 0;
  max-width: 66ch;
  color: #374151;
}

.refresh-btn,
.reset-btn {
  border: 1px solid rgba(17, 24, 39, 0.2);
  background: #111827;
  color: #f9fafb;
  border-radius: 14px;
  min-height: 44px;
  padding: 0 0.95rem;
  cursor: pointer;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.8rem;
}

.kpi-grid article,
.filters-shell,
.alerts-shell,
.column-card {
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(146, 64, 14, 0.16);
  backdrop-filter: blur(8px);
  border-radius: 18px;
}

.kpi-grid article {
  padding: 0.9rem;
  display: grid;
  gap: 0.4rem;
}

.kpi-grid span {
  font-size: 0.82rem;
  text-transform: uppercase;
  color: #92400e;
}

.kpi-grid strong {
  font-size: 1.6rem;
}

.filters-shell {
  padding: 0.9rem;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.7rem;
}

.filters-shell label {
  display: grid;
  gap: 0.3rem;
  font-size: 0.78rem;
  color: #374151;
}

.filters-shell input,
.filters-shell select {
  min-height: 42px;
  border-radius: 12px;
  border: 1px solid rgba(17, 24, 39, 0.2);
  background: #fff;
  padding: 0 0.7rem;
}

.alerts-shell {
  padding: 0.9rem;
  display: grid;
  gap: 0.55rem;
}

.alerts-shell header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.alerts-shell h2 {
  margin: 0;
}

.alert-card {
  border-radius: 14px;
  padding: 0.75rem;
}

.alert-card h3 {
  margin: 0 0 0.2rem;
  font-size: 0.95rem;
}

.alert-card p {
  margin: 0;
  font-size: 0.88rem;
}

.level-risk { background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.3); }
.level-attention { background: rgba(245, 158, 11, 0.14); border: 1px solid rgba(245, 158, 11, 0.35); }
.level-info { background: rgba(59, 130, 246, 0.13); border: 1px solid rgba(59, 130, 246, 0.3); }
.level-ok { background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3); }

.error-box {
  margin: 0;
  padding: 0.8rem;
  border-radius: 12px;
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.info-box {
  margin: 0;
  padding: 0.8rem;
  border-radius: 12px;
  background: rgba(59, 130, 246, 0.12);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.john-shell {
  padding: 0.95rem;
  display: grid;
  gap: 0.8rem;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(30, 64, 175, 0.16);
  border-radius: 18px;
  backdrop-filter: blur(8px);
}

.john-shell header {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  align-items: flex-start;
}

.john-shell h2 {
  margin: 0.2rem 0 0;
}

.john-card {
  display: grid;
  gap: 0.75rem;
  padding: 1rem;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(30, 64, 175, 0.94), rgba(15, 23, 42, 0.9));
  color: #eff6ff;
}

.john-headline {
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
  flex-wrap: wrap;
}

.john-summary {
  margin: 0;
  line-height: 1.5;
}

.john-metrics {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.john-metrics span {
  padding: 0.42rem 0.7rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  font-size: 0.85rem;
}

.board-shell {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.7rem;
}

.column-card {
  padding: 0.8rem;
  min-height: 240px;
}

.column-card header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.6rem;
}

.column-card h3 {
  margin: 0;
  font-size: 0.95rem;
}

.column-card ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 0.45rem;
}

.work-item {
  border: 1px solid rgba(17, 24, 39, 0.12);
  border-radius: 10px;
  background: #fff;
  padding: 0.55rem;
  display: grid;
  gap: 0.15rem;
  cursor: grab;
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.work-item.selected {
  border-color: rgba(37, 99, 235, 0.55);
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.12);
  transform: translateY(-1px);
}

.work-item:active {
  cursor: grabbing;
}

.work-item strong {
  font-size: 0.9rem;
}

.work-item small {
  color: #4b5563;
}

.column-empty {
  color: #6b7280;
  font-size: 0.85rem;
}

@media (max-width: 1024px) {
  .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .filters-shell { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .board-shell { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 720px) {
  .strategic-page { padding: 1rem; }
  .hero { flex-direction: column; }
  .john-shell header { flex-direction: column; }
  .filters-shell { grid-template-columns: 1fr; }
  .board-shell { grid-template-columns: 1fr; }
}
</style>
