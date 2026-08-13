<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import {
  createStrategy,
  getInitiatives,
  getObjectives,
  getPlans,
  getStrategicSuggestion,
  getStrategies,
  getTasks,
} from '@/services/api'

const isLoading = ref(false)
const isSubmitting = ref(false)
const loadError = ref('')
const submitMessage = ref('')
const lastSync = ref('')
const isLoadingSuggestion = ref(false)
const suggestionError = ref('')
const suggestionPanel = ref(null)

const filters = reactive({
  status: '',
  priority: '',
  search: '',
})

const createForm = reactive({
  name: '',
  description: '',
  priority: 'normal',
  status: 'backlog',
})

const dataset = reactive({
  strategies: [],
  objectives: [],
  initiatives: [],
  plans: [],
  tasks: [],
})

const statusOptions = ['backlog', 'planning', 'executing', 'validating', 'done']
const priorityOptions = ['low', 'normal', 'high', 'critical']

const hierarchy = computed(() => {
  const byStrategy = new Map()
  const byObjective = new Map()
  const byInitiative = new Map()
  const byPlan = new Map()

  for (const strategy of dataset.strategies) {
    byStrategy.set(strategy.id, {
      ...strategy,
      objectives: [],
    })
  }

  for (const objective of dataset.objectives) {
    const container = {
      ...objective,
      initiatives: [],
    }
    byObjective.set(objective.id, container)
    const strategyRef = byStrategy.get(objective.strategy_id)
    if (strategyRef) {
      strategyRef.objectives.push(container)
    }
  }

  for (const initiative of dataset.initiatives) {
    const container = {
      ...initiative,
      plans: [],
    }
    byInitiative.set(initiative.id, container)
    const objectiveRef = byObjective.get(initiative.objective_id)
    if (objectiveRef) {
      objectiveRef.initiatives.push(container)
    }
  }

  for (const plan of dataset.plans) {
    const container = {
      ...plan,
      tasks: [],
    }
    byPlan.set(plan.id, container)
    const initiativeRef = byInitiative.get(plan.initiative_id)
    if (initiativeRef) {
      initiativeRef.plans.push(container)
    }
  }

  for (const task of dataset.tasks) {
    const planRef = byPlan.get(task.plan_id)
    if (planRef) {
      planRef.tasks.push(task)
    }
  }

  const text = filters.search.trim().toLowerCase()
  const status = filters.status
  const priority = filters.priority

  const tree = [...byStrategy.values()].filter((strategy) => {
    const strategyMatchText = !text || `${strategy.name} ${strategy.description}`.toLowerCase().includes(text)
    const strategyMatchStatus = !status || strategy.status === status
    const strategyMatchPriority = !priority || strategy.priority === priority

    if (strategyMatchText && strategyMatchStatus && strategyMatchPriority) {
      return true
    }

    const foundInChildren = strategy.objectives.some((objective) => {
      const objectiveText = `${objective.metric}`.toLowerCase()
      if (text && objectiveText.includes(text)) return true

      return objective.initiatives.some((initiative) => {
        const initiativeText = `${initiative.name} ${initiative.description}`.toLowerCase()
        if (text && initiativeText.includes(text)) return true

        return initiative.plans.some((plan) => {
          const planText = `${plan.title} ${plan.description}`.toLowerCase()
          if (text && planText.includes(text)) return true

          return plan.tasks.some((task) => {
            const taskText = `${task.title} ${task.description}`.toLowerCase()
            return text && taskText.includes(text)
          })
        })
      })
    })

    return foundInChildren
  })

  return tree
})

const counters = computed(() => ({
  strategies: dataset.strategies.length,
  objectives: dataset.objectives.length,
  initiatives: dataset.initiatives.length,
  plans: dataset.plans.length,
  tasks: dataset.tasks.length,
}))

async function loadHierarchy() {
  isLoading.value = true
  loadError.value = ''

  try {
    const [strategiesRes, objectivesRes, initiativesRes, plansRes, tasksRes] = await Promise.all([
      getStrategies({ limit: 500 }),
      getObjectives({ limit: 1000 }),
      getInitiatives({ limit: 1000 }),
      getPlans({ limit: 1000 }),
      getTasks({ limit: 2000 }),
    ])

    dataset.strategies = strategiesRes.data.items || []
    dataset.objectives = objectivesRes.data.items || []
    dataset.initiatives = initiativesRes.data.items || []
    dataset.plans = plansRes.data.items || []
    dataset.tasks = tasksRes.data.items || []
    lastSync.value = new Date().toLocaleTimeString('pt-BR')
  } catch (error) {
    loadError.value = 'Nao foi possivel carregar a hierarquia estrategica.'
  } finally {
    isLoading.value = false
  }
}

async function submitStrategy() {
  if (!createForm.name.trim()) {
    submitMessage.value = 'Informe o nome da estrategia.'
    return
  }

  isSubmitting.value = true
  submitMessage.value = ''

  try {
    await createStrategy({
      name: createForm.name.trim(),
      description: createForm.description.trim(),
      priority: createForm.priority,
      status: createForm.status,
    })

    createForm.name = ''
    createForm.description = ''
    createForm.priority = 'normal'
    createForm.status = 'backlog'
    submitMessage.value = 'Estrategia criada com sucesso.'
    await loadHierarchy()
  } catch (error) {
    submitMessage.value = 'Falha ao criar estrategia.'
  } finally {
    isSubmitting.value = false
  }
}

async function loadSuggestion(entityType, entityId, label, focus = 'priorizacao e proximo passo') {
  isLoadingSuggestion.value = true
  suggestionError.value = ''

  try {
    const { data } = await getStrategicSuggestion(entityType, entityId, { focus })
    suggestionPanel.value = {
      ...data,
      label,
      entityType,
      entityId,
    }
  } catch (error) {
    suggestionError.value = 'Nao foi possivel consultar a recomendacao do John para este item.'
  } finally {
    isLoadingSuggestion.value = false
  }
}

onMounted(() => {
  loadHierarchy()
})
</script>

<template>
  <section class="studio-page">
    <header class="studio-hero">
      <div>
        <p class="eyebrow">Estrategia LICEU 6.0</p>
        <h1>Crie estrategias e acompanhe a hierarquia completa em um unico painel.</h1>
        <p class="subtitle">
          O fluxo conecta estrategia, objetivo, iniciativa, plano e task com leitura operacional continua.
        </p>
      </div>
      <button class="refresh-btn" :disabled="isLoading" @click="loadHierarchy">
        {{ isLoading ? 'Sincronizando...' : 'Atualizar hierarquia' }}
      </button>
    </header>

    <section class="counter-grid">
      <article>
        <span>Strategies</span>
        <strong>{{ counters.strategies }}</strong>
      </article>
      <article>
        <span>Objectives</span>
        <strong>{{ counters.objectives }}</strong>
      </article>
      <article>
        <span>Initiatives</span>
        <strong>{{ counters.initiatives }}</strong>
      </article>
      <article>
        <span>Plans</span>
        <strong>{{ counters.plans }}</strong>
      </article>
      <article>
        <span>Tasks</span>
        <strong>{{ counters.tasks }}</strong>
      </article>
    </section>

    <section class="layout-grid">
      <article class="create-shell">
        <header>
          <h2>Criar estrategia</h2>
          <small>Issue 016 • Entrada de estrategia</small>
        </header>

        <label>
          Nome
          <input v-model="createForm.name" type="text" placeholder="Ex: Expansao nacional 2027" />
        </label>

        <label>
          Descricao
          <textarea v-model="createForm.description" rows="4" placeholder="Contexto macro da estrategia" />
        </label>

        <div class="inline-grid">
          <label>
            Prioridade
            <select v-model="createForm.priority">
              <option v-for="priority in priorityOptions" :key="priority" :value="priority">
                {{ priority }}
              </option>
            </select>
          </label>

          <label>
            Status
            <select v-model="createForm.status">
              <option v-for="status in statusOptions" :key="status" :value="status">
                {{ status }}
              </option>
            </select>
          </label>
        </div>

        <button class="submit-btn" :disabled="isSubmitting" @click="submitStrategy">
          {{ isSubmitting ? 'Criando...' : 'Criar estrategia' }}
        </button>

        <p v-if="submitMessage" class="submit-msg">{{ submitMessage }}</p>
        <p v-if="lastSync" class="sync-msg">Ultima sincronizacao: {{ lastSync }}</p>

        <section class="john-shell">
          <header>
            <div>
              <p class="eyebrow">John Estrategico</p>
              <h3>Leitura cognitiva da hierarquia</h3>
            </div>
            <small v-if="suggestionPanel?.suggestion?.target_monolith">
              {{ suggestionPanel.suggestion.target_monolith }}
            </small>
          </header>

          <p v-if="isLoadingSuggestion" class="sync-msg">Consultando recomendacao do John...</p>
          <p v-else-if="suggestionError" class="error-box">{{ suggestionError }}</p>

          <article v-else-if="suggestionPanel" class="john-card">
            <strong>{{ suggestionPanel.label }}</strong>
            <p>{{ suggestionPanel.suggestion.summary }}</p>
            <div class="john-tags">
              <span>{{ suggestionPanel.suggestion.recommended_action }}</span>
              <span>risco {{ suggestionPanel.suggestion.risk }}</span>
              <span>{{ Math.round((suggestionPanel.suggestion.confidence || 0) * 100) }}% confianca</span>
              <span>{{ suggestionPanel.suggestion.target_john }}</span>
            </div>
          </article>

          <div v-else class="empty-box">
            Clique em John dentro da hierarquia para carregar a recomendacao contextual.
          </div>
        </section>
      </article>

      <article class="tree-shell">
        <header>
          <h2>Hierarquia estrategica</h2>
          <small>Strategy > Objective > Initiative > Plan > Task</small>
        </header>

        <section class="filter-grid">
          <label>
            Busca
            <input v-model="filters.search" type="text" placeholder="Nome, metrica, plano ou task" />
          </label>

          <label>
            Status da strategy
            <select v-model="filters.status">
              <option value="">Todos</option>
              <option v-for="status in statusOptions" :key="status" :value="status">
                {{ status }}
              </option>
            </select>
          </label>

          <label>
            Prioridade da strategy
            <select v-model="filters.priority">
              <option value="">Todas</option>
              <option v-for="priority in priorityOptions" :key="priority" :value="priority">
                {{ priority }}
              </option>
            </select>
          </label>
        </section>

        <p v-if="loadError" class="error-box">{{ loadError }}</p>

        <div v-if="hierarchy.length === 0" class="empty-box">
          Nenhuma estrategia encontrada para os filtros atuais.
        </div>

        <div v-else class="tree-list">
          <details v-for="strategy in hierarchy" :key="strategy.id" class="tree-level strategy-level" open>
            <summary>
              <strong>{{ strategy.name }}</strong>
              <small>#{{ strategy.id }} • {{ strategy.status }} • {{ strategy.priority }}</small>
              <button class="john-trigger" @click.stop.prevent="loadSuggestion('strategy', strategy.id, strategy.name, 'visao executiva da estrategia')">
                John
              </button>
            </summary>

            <p class="description" v-if="strategy.description">{{ strategy.description }}</p>

            <details v-for="objective in strategy.objectives" :key="objective.id" class="tree-level objective-level" open>
              <summary>
                <strong>Objective: {{ objective.metric }}</strong>
                <small>#{{ objective.id }} • target {{ objective.target }} • {{ objective.status }}</small>
                <button class="john-trigger" @click.stop.prevent="loadSuggestion('objective', objective.id, `Objective ${objective.metric}`, 'desdobramento do objetivo')">
                  John
                </button>
              </summary>

              <details v-for="initiative in objective.initiatives" :key="initiative.id" class="tree-level initiative-level" open>
                <summary>
                  <strong>Initiative: {{ initiative.name }}</strong>
                  <small>#{{ initiative.id }} • {{ initiative.initiative_type }} • owner {{ initiative.owner }}</small>
                  <button class="john-trigger" @click.stop.prevent="loadSuggestion('initiative', initiative.id, `Initiative ${initiative.name}`, 'proximo passo da iniciativa')">
                    John
                  </button>
                </summary>

                <details v-for="plan in initiative.plans" :key="plan.id" class="tree-level plan-level" open>
                  <summary>
                    <strong>Plan: {{ plan.title }}</strong>
                    <small>#{{ plan.id }} • {{ plan.status }} • {{ plan.priority }}</small>
                    <button class="john-trigger" @click.stop.prevent="loadSuggestion('plan', plan.id, `Plan ${plan.title}`, 'ajuste do plano tatico')">
                      John
                    </button>
                  </summary>

                  <ul class="task-list">
                    <li v-for="task in plan.tasks" :key="task.id">
                      <strong>Task {{ task.id }}</strong>
                      <span>{{ task.title }}</span>
                      <small>{{ task.status }} • {{ task.priority }} • {{ task.assigned_to }}</small>
                      <button class="john-trigger inline" @click.stop.prevent="loadSuggestion('task', task.id, `Task ${task.title}`, 'acao operacional imediata')">
                        John
                      </button>
                    </li>
                    <li v-if="plan.tasks.length === 0" class="task-empty">Sem tasks vinculadas.</li>
                  </ul>
                </details>
              </details>
            </details>
          </details>
        </div>
      </article>
    </section>
  </section>
</template>

<style scoped>
.studio-page {
  min-height: 100vh;
  padding: 1.5rem;
  color: #111827;
  display: grid;
  gap: 0.95rem;
  background:
    radial-gradient(circle at 14% 16%, rgba(3, 105, 161, 0.16), transparent 30%),
    radial-gradient(circle at 84% 22%, rgba(180, 83, 9, 0.16), transparent 30%),
    linear-gradient(180deg, #f8fbff 0%, #f9fafb 45%, #fff8f1 100%);
}

.studio-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.eyebrow {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.13em;
  font-size: 0.72rem;
  color: #9a3412;
}

.studio-hero h1 {
  margin: 0.35rem 0;
  font-size: clamp(1.8rem, 4vw, 3rem);
  line-height: 1.02;
  font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
}

.subtitle {
  margin: 0;
  color: #374151;
  max-width: 72ch;
}

.refresh-btn,
.submit-btn {
  border: 1px solid rgba(17, 24, 39, 0.2);
  background: #111827;
  color: #f9fafb;
  border-radius: 14px;
  min-height: 44px;
  padding: 0 1rem;
  cursor: pointer;
}

.counter-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 0.75rem;
}

.counter-grid article,
.create-shell,
.tree-shell {
  border-radius: 18px;
  border: 1px solid rgba(17, 24, 39, 0.12);
  background: rgba(255, 255, 255, 0.84);
  backdrop-filter: blur(9px);
}

.counter-grid article {
  padding: 0.85rem;
  display: grid;
  gap: 0.3rem;
}

.counter-grid span {
  font-size: 0.78rem;
  text-transform: uppercase;
  color: #9a3412;
}

.counter-grid strong {
  font-size: 1.45rem;
}

.layout-grid {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 0.85rem;
}

.create-shell,
.tree-shell {
  padding: 0.95rem;
  display: grid;
  gap: 0.75rem;
}

.create-shell header,
.tree-shell header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.create-shell h2,
.tree-shell h2 {
  margin: 0;
}

.create-shell label,
.filter-grid label {
  display: grid;
  gap: 0.28rem;
  font-size: 0.78rem;
  color: #374151;
}

.create-shell input,
.create-shell textarea,
.create-shell select,
.filter-grid input,
.filter-grid select {
  border: 1px solid rgba(17, 24, 39, 0.2);
  border-radius: 12px;
  min-height: 42px;
  padding: 0.55rem 0.7rem;
  background: #fff;
}

.inline-grid,
.filter-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.6rem;
}

.filter-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.submit-msg,
.sync-msg,
.error-box,
.empty-box {
  margin: 0;
  padding: 0.7rem;
  border-radius: 12px;
}

.submit-msg {
  background: rgba(16, 185, 129, 0.14);
  border: 1px solid rgba(16, 185, 129, 0.32);
}

.sync-msg {
  background: rgba(59, 130, 246, 0.12);
  border: 1px solid rgba(59, 130, 246, 0.28);
}

.error-box {
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.empty-box {
  background: rgba(15, 23, 42, 0.05);
  border: 1px dashed rgba(15, 23, 42, 0.25);
}

.john-shell {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(17, 24, 39, 0.08);
  display: grid;
  gap: 0.8rem;
}

.john-shell header {
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
  align-items: flex-start;
}

.john-shell h3 {
  margin: 0.2rem 0 0;
}

.john-card {
  display: grid;
  gap: 0.7rem;
  padding: 0.95rem;
  border-radius: 16px;
  color: #ecfeff;
  background: linear-gradient(145deg, rgba(15, 118, 110, 0.96), rgba(8, 47, 73, 0.92));
}

.john-card p {
  margin: 0;
  line-height: 1.5;
}

.john-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.john-tags span {
  padding: 0.38rem 0.68rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  font-size: 0.82rem;
}

.tree-list {
  display: grid;
  gap: 0.55rem;
}

.tree-level {
  border-radius: 12px;
  border: 1px solid rgba(17, 24, 39, 0.14);
  background: #fff;
  padding: 0.45rem 0.55rem;
}

.tree-level summary {
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  align-items: baseline;
  flex-wrap: wrap;
}

.tree-level summary strong {
  font-size: 0.9rem;
}

.tree-level summary small {
  color: #4b5563;
}

.description {
  margin: 0.45rem 0 0;
  color: #374151;
}

.objective-level {
  margin-top: 0.5rem;
  background: #f8fbff;
}

.initiative-level {
  margin-top: 0.45rem;
  background: #fff8ed;
}

.plan-level {
  margin-top: 0.4rem;
  background: #f8fafc;
}

.task-list {
  list-style: none;
  margin: 0.4rem 0 0;
  padding: 0;
  display: grid;
  gap: 0.35rem;
}

.task-list li {
  border: 1px solid rgba(17, 24, 39, 0.12);
  border-radius: 10px;
  padding: 0.45rem;
  display: grid;
  gap: 0.12rem;
  background: #fff;
}

.task-list li span {
  color: #1f2937;
}

.task-list li small,
.task-empty {
  color: #6b7280;
}

.john-trigger {
  margin-left: auto;
  border: 1px solid rgba(14, 116, 144, 0.25);
  background: rgba(14, 116, 144, 0.08);
  color: #0f172a;
  border-radius: 999px;
  min-height: 30px;
  padding: 0 0.7rem;
  cursor: pointer;
  font-size: 0.78rem;
}

.john-trigger.inline {
  margin-left: 0;
  margin-top: 0.35rem;
  width: fit-content;
}

@media (max-width: 1120px) {
  .counter-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .layout-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .studio-page {
    padding: 1rem;
  }

  .studio-hero {
    flex-direction: column;
  }

  .counter-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .inline-grid,
  .filter-grid {
    grid-template-columns: 1fr;
  }

  .john-shell header {
    flex-direction: column;
  }
}
</style>
