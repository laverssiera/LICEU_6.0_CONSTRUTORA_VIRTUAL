<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  johnLeads,
  johnLeadsMetrics,
  johnRetrainScoring,
  johnUpdateLeadStatus,
  johnWhatsAppSend,
} from '@/services/api'

const isLoading = ref(false)
const isActionLoading = ref(false)
const errorMessage = ref('')
const metrics = ref({ kpis: {}, funnel: [], by_profile: [], by_source: [] })
const leads = ref([])
const lookbackDays = ref(30)
const whatsappMessage = ref('Olá! John da LICEU aqui. Obrigado pelo seu interesse.')
const whatsappTo = ref('5511977601855')
const actionFeedback = ref('')

const topProfiles = computed(() => (metrics.value.by_profile || []).slice(0, 5))
const topSources = computed(() => (metrics.value.by_source || []).slice(0, 5))

async function loadDashboard() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const [metricsResponse, leadsResponse] = await Promise.all([
      johnLeadsMetrics(lookbackDays.value),
      johnLeads(),
    ])
    metrics.value = metricsResponse.data || { kpis: {}, funnel: [] }
    leads.value = (leadsResponse.data?.items || []).slice(0, 30)
  } catch (error) {
    errorMessage.value = 'Nao foi possivel carregar o CRM Dashboard no momento.'
  } finally {
    isLoading.value = false
  }
}

async function updateStatus(leadId, status) {
  isActionLoading.value = true
  actionFeedback.value = ''
  try {
    await johnUpdateLeadStatus(leadId, status)
    actionFeedback.value = `Lead #${leadId} atualizado para ${status}.`
    await loadDashboard()
  } catch (error) {
    actionFeedback.value = 'Falha ao atualizar status do lead.'
  } finally {
    isActionLoading.value = false
  }
}

async function retrainScoring() {
  isActionLoading.value = true
  actionFeedback.value = ''
  try {
    const { data } = await johnRetrainScoring(180, 8)
    actionFeedback.value = `Treinamento concluido: ${data.status}.`
    await loadDashboard()
  } catch (error) {
    actionFeedback.value = 'Falha ao executar retraining do scoring.'
  } finally {
    isActionLoading.value = false
  }
}

async function sendWhatsApp() {
  isActionLoading.value = true
  actionFeedback.value = ''
  try {
    const { data } = await johnWhatsAppSend(whatsappMessage.value, whatsappTo.value)
    actionFeedback.value = `WhatsApp ${data.status} para ${data.to}.`
  } catch (error) {
    actionFeedback.value = 'Falha no envio WhatsApp.'
  } finally {
    isActionLoading.value = false
  }
}

onMounted(loadDashboard)
</script>

<template>
  <section class="crm-dashboard">
    <header class="hero">
      <div>
        <h1>CRM Dashboard do John</h1>
        <p>Monitoramento de leads reais, conversao, retraining de score e envio WhatsApp Business.</p>
      </div>
      <div class="hero-actions">
        <label>
          Janela (dias)
          <select v-model.number="lookbackDays" @change="loadDashboard">
            <option :value="7">7</option>
            <option :value="30">30</option>
            <option :value="90">90</option>
            <option :value="180">180</option>
          </select>
        </label>
        <button :disabled="isLoading" @click="loadDashboard">Atualizar</button>
      </div>
    </header>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
    <p v-if="actionFeedback" class="feedback">{{ actionFeedback }}</p>

    <div class="kpis">
      <article class="card"><h3>Total Leads</h3><strong>{{ metrics.kpis?.total || 0 }}</strong></article>
      <article class="card"><h3>Qualificados</h3><strong>{{ metrics.kpis?.qualified || 0 }}</strong></article>
      <article class="card"><h3>Convertidos</h3><strong>{{ metrics.kpis?.converted || 0 }}</strong></article>
      <article class="card"><h3>Taxa Conversao</h3><strong>{{ metrics.kpis?.conversion_rate || 0 }}%</strong></article>
      <article class="card"><h3>Score Medio</h3><strong>{{ metrics.kpis?.avg_score || 0 }}</strong></article>
    </div>

    <div class="grid">
      <section class="panel">
        <h2>Funnel</h2>
        <ul class="funnel">
          <li v-for="item in metrics.funnel || []" :key="item.stage">
            <span>{{ item.stage }}</span>
            <strong>{{ item.count }}</strong>
          </li>
        </ul>
      </section>

      <section class="panel">
        <h2>Top Perfis</h2>
        <ul>
          <li v-for="item in topProfiles" :key="item.profile">{{ item.profile }}: {{ item.count }}</li>
        </ul>
        <h2>Top Origens</h2>
        <ul>
          <li v-for="item in topSources" :key="item.source">{{ item.source }}: {{ item.count }}</li>
        </ul>
      </section>

      <section class="panel actions">
        <h2>Operacoes</h2>
        <button :disabled="isActionLoading" @click="retrainScoring">Retrain Scoring ML</button>

        <label>
          Numero WhatsApp
          <input v-model="whatsappTo" placeholder="5511977601855" />
        </label>
        <label>
          Mensagem
          <textarea v-model="whatsappMessage" rows="4" />
        </label>
        <button :disabled="isActionLoading" @click="sendWhatsApp">Enviar WhatsApp</button>
      </section>
    </div>

    <section class="panel table-panel">
      <h2>Leads Recentes</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Nome</th>
            <th>Perfil</th>
            <th>Score</th>
            <th>Status</th>
            <th>Acoes</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="lead in leads" :key="lead.id">
            <td>{{ lead.id }}</td>
            <td>{{ lead.name }}</td>
            <td>{{ lead.profile }}</td>
            <td>{{ Number(lead.score || 0).toFixed(2) }}</td>
            <td>{{ lead.status }}</td>
            <td class="actions-cell">
              <button :disabled="isActionLoading" @click="updateStatus(lead.id, 'converted')">Converter</button>
              <button :disabled="isActionLoading" class="ghost" @click="updateStatus(lead.id, 'lost')">Perdido</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </section>
</template>

<style scoped>
.crm-dashboard {
  min-height: 100vh;
  padding: 24px;
  color: #1f2937;
  background: radial-gradient(circle at top right, #e0f2fe 0%, #f8fafc 38%, #f3f4f6 100%);
}

.hero {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 18px;
}

.hero h1 {
  margin: 0;
  font-size: 1.9rem;
  color: #0f172a;
}

.hero p {
  margin-top: 8px;
  max-width: 680px;
  color: #334155;
}

.hero-actions {
  display: flex;
  gap: 10px;
  align-items: end;
}

.kpis {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  margin-bottom: 16px;
}

.card,
.panel {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #dbeafe;
  border-radius: 12px;
  padding: 14px;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
}

.card h3 {
  margin: 0;
  font-size: 0.84rem;
  color: #64748b;
}

.card strong {
  display: block;
  margin-top: 6px;
  font-size: 1.5rem;
  color: #0f172a;
}

.grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 14px;
  margin-bottom: 14px;
}

.funnel {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 8px;
}

.funnel li {
  display: flex;
  justify-content: space-between;
  background: #eff6ff;
  padding: 8px 10px;
  border-radius: 8px;
}

.actions {
  display: grid;
  gap: 8px;
}

.table-panel {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
  padding: 10px;
  font-size: 0.92rem;
}

button {
  border: 0;
  border-radius: 8px;
  padding: 8px 10px;
  background: #0ea5e9;
  color: #fff;
  cursor: pointer;
}

button.ghost {
  background: #64748b;
}

label {
  display: grid;
  gap: 4px;
  color: #334155;
  font-size: 0.84rem;
}

input,
select,
textarea {
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  padding: 8px;
}

.actions-cell {
  display: flex;
  gap: 8px;
}

.error {
  color: #b91c1c;
}

.feedback {
  color: #0369a1;
}

@media (max-width: 980px) {
  .grid {
    grid-template-columns: 1fr;
  }

  .hero {
    flex-direction: column;
  }
}
</style>
