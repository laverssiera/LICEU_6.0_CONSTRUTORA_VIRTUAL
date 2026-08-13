<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createJohnEventsSocket, johnCRMChat, johnDispatch, johnDiscussPillar, johnWelcome } from '@/services/api'

const router = useRouter()
const isOpen = ref(false)
const isLoading = ref(false)
const message = ref('')
const feedback = ref('Olá! Sou o John Brasileiro. Posso despachar você para investimentos, obras, dados, academia e jurídico.')
const dispatchContext = ref('')
const holdingAnalysis = ref('')
const lastAction = ref(null)
const isRealtimeConnected = ref(false)
const liveEvents = ref([])
const leadReceipt = ref(null)
let johnSocket = null

const supportsVoice = computed(() => typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window))

const routeMap = {
  ARCHIMEDES_PORTAL: { path: '/archimedes', query: { portal: 'archimedes' }, pillar: 'archimedes' },
  CEA_INVESTIMENTOS_PORTAL: { path: '/investidores', query: { portal: 'cea-investimentos' }, pillar: 'cea-invest' },
  ACADEMIA_SABER_PORTAL: { path: '/escola', query: { portal: 'academia-saber' }, pillar: 'academia' },
  ERP_FORNECEDORES_PORTAL: { path: '/obras', query: { portal: 'fornecedores' }, pillar: 'fornecedores' }
}

const quickActions = [
  { intent: 'investir', label: 'Investir', emoji: '💰', path: '/investidores', query: { portal: 'cea-investimentos' }, pillar: 'cea-invest' },
  { intent: 'obra', label: 'Obra', emoji: '🏗️', path: '/archimedes', query: { portal: 'archimedes' }, pillar: 'archimedes' },
  { intent: 'dados', label: 'Dados', emoji: '📊', path: '/dados', query: { portal: 'cefeida' }, pillar: 'cefeida' },
  { intent: 'aprender', label: 'Aprender', emoji: '🎓', path: '/escola', query: { portal: 'academia-saber' }, pillar: 'academia' },
  { intent: 'juridico', label: 'Jurídico', emoji: '⚖️', path: '/juridico', query: { portal: 'juridico-tech' }, pillar: 'juridico-tech' }
]

function toggleOpen() {
  isOpen.value = !isOpen.value
}

function announceJourneyStarted(detail = {}) {
  if (typeof window === 'undefined') return
  window.localStorage.setItem('liceu_jornada_started', '1')
  window.dispatchEvent(new CustomEvent('liceu:jornada-iniciada', { detail }))
}

async function navigateTo(destination) {
  if (!destination?.path) return
  await router.push({ path: destination.path, query: destination.query || {} })
}

async function fetchHoldingInsight(pillar) {
  if (!pillar) return ''

  try {
    const { data } = await johnDiscussPillar(pillar)
    return data.analise_holding || ''
  } catch (error) {
    return 'Holding em monitoramento contínuo do seu fluxo.'
  }
}

async function handleQuickAction(action) {
  if (isLoading.value) return

  isLoading.value = true
  try {
    const { data } = await johnDispatch(action.intent)
    lastAction.value = { redirect_to: data.redirect, pilar: data.pilar }
    dispatchContext.value = data.contexto
    holdingAnalysis.value = await fetchHoldingInsight(action.pillar)
    feedback.value = `${data.contexto}. ${holdingAnalysis.value}`
    announceJourneyStarted({ origin: 'quick-action', intent: action.intent, redirect_to: data.redirect, pillar: action.pillar })
    await navigateTo(action)
  } catch (error) {
    feedback.value = 'John não conseguiu abrir este pilar agora. Tente novamente em instantes.'
  } finally {
    isLoading.value = false
  }
}

async function sendWelcomeRequest(text) {
  if (!text?.trim()) return

  isLoading.value = true
  try {
    const currentPage = typeof window !== 'undefined' ? window.location.pathname : 'Liceu-Home'

    let data
    try {
      const crmResponse = await johnCRMChat({
        message: text,
        source: 'site',
        current_page: currentPage,
        user_type: 'Guest'
      })
      data = crmResponse.data
    } catch (crmError) {
      // Compatibilidade com ambientes onde o endpoint novo ainda nao existe.
      const welcomeResponse = await johnWelcome({
        request: text,
        context: {
          current_page: currentPage,
          user_type: 'Guest'
        }
      })
      data = welcomeResponse.data
    }

    const johnAction = data.john_action || { redirect_to: 'ARCHIMEDES_PORTAL' }
    const destination = routeMap[johnAction.redirect_to] || { path: '/', query: {}, pillar: 'cefeida' }

    lastAction.value = johnAction
    dispatchContext.value = `Perfil identificado: ${data.profile}. Interesse ${data.thermometer?.band || 'médio'}.`
    holdingAnalysis.value = await fetchHoldingInsight(destination.pillar)
    feedback.value = `${data.reply || dispatchContext.value} ${holdingAnalysis.value}`

    // Create lead receipt for confirmation display
    if (data.lead_id) {
      leadReceipt.value = {
        lead_id: data.lead_id,
        profile: data.profile,
        thermometer: data.thermometer?.band || 'médio',
        timestamp: new Date().toLocaleTimeString('pt-BR'),
        message: data.reply
      }
    }

    announceJourneyStarted({
      origin: 'crm-chat',
      request: text,
      redirect_to: johnAction.redirect_to,
      profile: data.profile,
      lead_id: data.lead_id
    })

    await navigateTo(destination)
    message.value = ''
  } catch (error) {
    feedback.value = 'John não conseguiu concluir a triagem agora. Tente novamente em instantes.'
  } finally {
    isLoading.value = false
  }
}

async function handleSubmit() {
  await sendWelcomeRequest(message.value)
}

function activateVoice() {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition
  if (!Recognition) {
    feedback.value = 'Reconhecimento de voz não está disponível neste navegador.'
    return
  }

  const recognition = new Recognition()
  recognition.lang = 'pt-BR'
  recognition.start()
  feedback.value = 'Ouvindo sua intenção...'

  recognition.onresult = async (event) => {
    const transcript = event.results[0][0].transcript
    message.value = transcript
    await sendWelcomeRequest(transcript)
  }

  recognition.onerror = () => {
    feedback.value = 'Não foi possível captar a voz agora.'
  }
}

function connectRealtimeFeed() {
  if (typeof window === 'undefined') return

  try {
    johnSocket = createJohnEventsSocket()

    johnSocket.onopen = () => {
      isRealtimeConnected.value = true
    }

    johnSocket.onmessage = (rawEvent) => {
      try {
        const packet = JSON.parse(rawEvent.data)
        const event = packet.event || {}
        liveEvents.value = [packet, ...liveEvents.value].slice(0, 5)

        if (event.event_type === 'john.welcome') {
          dispatchContext.value = 'John identificou um novo fluxo ao vivo.'
          lastAction.value = { redirect_to: event.redirect_to }
          feedback.value = `John recebeu a solicitação e direcionou para ${event.redirect_to || 'um pilar do ecossistema'}.`
          announceJourneyStarted({ origin: 'realtime', redirect_to: event.redirect_to })
        } else if (event.event_type === 'crm.lead.created') {
          const redirectTo = event.payload?.redirect_to || 'ARCHIMEDES_PORTAL'
          lastAction.value = { redirect_to: redirectTo }
          feedback.value = `Lead registrado em tempo real (${event.payload?.id || 'sem-id'}).`
        } else if (event.event_type === 'brain.sync') {
          feedback.value = 'John recebeu um pulso cognitivo e atualizou a central instantaneamente.'
        } else if (event.event_type) {
          feedback.value = `Evento ao vivo: ${event.event_type}`
        }
      } catch (error) {
        feedback.value = 'Evento em tempo real recebido pelo John.'
      }
    }

    johnSocket.onclose = () => {
      isRealtimeConnected.value = false
    }

    johnSocket.onerror = () => {
      isRealtimeConnected.value = false
    }
  } catch (error) {
    isRealtimeConnected.value = false
  }
}

onMounted(() => {
  connectRealtimeFeed()
})

onBeforeUnmount(() => {
  if (johnSocket) {
    johnSocket.close()
    johnSocket = null
  }
})
</script>

<template>
  <div class="john-concierge">
    <button class="john-trigger" @click="toggleOpen">
      🧠 John
    </button>

    <div v-if="isOpen" class="john-panel">
      <h3>John Brasileiro</h3>
      <p>{{ feedback }}</p>
      <div class="john-live-status" :class="{ online: isRealtimeConnected }">
        {{ isRealtimeConnected ? '● Conectado ao vivo com John' : '○ Modo local' }}
      </div>

      <div class="john-shortcuts">
        <button
          v-for="action in quickActions"
          :key="action.intent"
          class="shortcut-chip"
          :disabled="isLoading"
          @click="handleQuickAction(action)"
        >
          <span>{{ action.emoji }}</span>
          {{ action.label }}
        </button>
      </div>

      <textarea
        v-model="message"
        rows="3"
        placeholder="Ex: Quero investir, acompanhar obra, ver dados ou estudar na Academia"
      />

      <div class="john-actions">
        <button :disabled="isLoading" @click="handleSubmit">
          {{ isLoading ? 'Analisando...' : 'Enviar' }}
        </button>
        <button v-if="supportsVoice" class="secondary" @click="activateVoice">
          Voz
        </button>
      </div>

      <div v-if="leadReceipt" class="john-lead-receipt">
        <div class="receipt-header">✓ Lead Registrado</div>
        <div class="receipt-content">
          <div class="receipt-row">
            <span class="receipt-label">Protocolo:</span>
            <span class="receipt-value mono">{{ leadReceipt.lead_id.substring(0, 8) }}...</span>
          </div>
          <div class="receipt-row">
            <span class="receipt-label">Perfil:</span>
            <span class="receipt-value">{{ leadReceipt.profile }}</span>
          </div>
          <div class="receipt-row">
            <span class="receipt-label">Interesse:</span>
            <span class="receipt-value">{{ leadReceipt.thermometer }}</span>
          </div>
          <div class="receipt-row">
            <span class="receipt-label">Registro:</span>
            <span class="receipt-value">{{ leadReceipt.timestamp }}</span>
          </div>
        </div>
        <p class="receipt-message">{{ leadReceipt.message }}</p>
        <button class="receipt-close" @click="leadReceipt = null">Fechar</button>
      </div>

      <div v-else-if="dispatchContext || holdingAnalysis || lastAction" class="john-result">
        <div v-if="dispatchContext"><strong>Despacho:</strong> {{ dispatchContext }}</div>
        <div v-if="holdingAnalysis"><strong>Holding:</strong> {{ holdingAnalysis }}</div>
        <div v-if="lastAction"><strong>Destino:</strong> {{ lastAction.redirect_to || lastAction.pilar }}</div>
      </div>

      <div v-if="liveEvents.length" class="john-live-feed">
        <strong>Eventos ao vivo</strong>
        <ul>
          <li v-for="(item, index) in liveEvents" :key="`${item.event?.event_type || 'evt'}-${index}`">
            {{ item.event?.event_type || 'evento' }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.john-concierge {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 9999;
}

.john-trigger {
  background: linear-gradient(135deg, #0f2e4d, #1d6fa5);
  color: #fff;
  border: none;
  border-radius: 999px;
  padding: 14px 18px;
  cursor: pointer;
  font-weight: 700;
  box-shadow: 0 10px 25px rgba(0,0,0,0.25);
}

.john-panel {
  width: 340px;
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  margin-top: 12px;
  box-shadow: 0 12px 30px rgba(0,0,0,0.18);
}

.john-panel h3 {
  margin-bottom: 8px;
  color: #133a5e;
}

.john-panel p {
  font-size: 0.92rem;
  color: #405466;
  margin-bottom: 10px;
}

.john-live-status {
  font-size: 0.8rem;
  margin-bottom: 10px;
  color: #64748b;
}

.john-live-status.online {
  color: #0f8a5f;
  font-weight: 700;
}

.john-shortcuts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.shortcut-chip {
  border: 1px solid #d9e2ec;
  border-radius: 999px;
  background: #f8fafc;
  color: #133a5e;
  padding: 8px 10px;
  font-size: 0.8rem;
  cursor: pointer;
}

textarea {
  width: 100%;
  border: 1px solid #d9e2ec;
  border-radius: 10px;
  padding: 10px;
  resize: none;
}

.john-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.john-actions button {
  flex: 1;
  border: none;
  border-radius: 10px;
  padding: 10px;
  cursor: pointer;
  background: #133a5e;
  color: #fff;
}

.john-actions .secondary {
  background: #7c3aed;
}

.john-result {
  margin-top: 10px;
  font-size: 0.9rem;
  color: #133a5e;
  display: grid;
  gap: 6px;
}

.john-lead-receipt {
  margin-top: 10px;
  padding: 12px;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border-left: 4px solid #22c55e;
  border-radius: 8px;
}

.receipt-header {
  font-weight: 700;
  color: #166534;
  margin-bottom: 10px;
  font-size: 0.95rem;
}

.receipt-content {
  display: grid;
  gap: 6px;
  margin-bottom: 10px;
  font-size: 0.85rem;
}

.receipt-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.receipt-label {
  color: #5a6b6e;
  font-weight: 600;
}

.receipt-value {
  color: #166534;
  font-weight: 500;
}

.receipt-value.mono {
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 0.8rem;
  background: rgba(34, 197, 94, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

.receipt-message {
  font-size: 0.85rem;
  color: #166534;
  margin: 8px 0;
  font-style: italic;
}

.receipt-close {
  width: 100%;
  border: 1px solid #22c55e;
  background: #fff;
  color: #166534;
  border-radius: 6px;
  padding: 6px;
  font-size: 0.8rem;
  cursor: pointer;
  font-weight: 600;
}

.john-live-feed {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid #e2e8f0;
  font-size: 0.85rem;
  color: #133a5e;
}

.john-live-feed ul {
  margin: 6px 0 0;
  padding-left: 18px;
}
</style>
