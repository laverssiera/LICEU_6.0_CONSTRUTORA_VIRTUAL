<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { readGrowthSummary, resetGrowthSummary, track } from '@/core/growthTracker'

const router = useRouter()

const videoRef = ref(null)
const videoSrc = ref('')
const videoReady = ref(false)
const videoFailed = ref(false)
const showJohn = ref(false)
const variant = ref('institutional')
const variantSource = ref('time')
const abGroup = ref('A')
const johnPrompt = ref('Bem-vindo ao LICEU 6.0. Aqui, comportamento vira inteligência. E inteligência vira decisão.')
const growthSummary = ref(readGrowthSummary())
const serverSummary = ref(null)
const serverSyncing = ref(false)
const serverSyncError = ref('')
const serverUpdatedAt = ref('--')
const serverSyncMode = ref('idle')
const serverNextRetrySeconds = ref(0)

let autoplayTimer = null
let johnTimer = null
let idleTimer = null
let serverSyncTimer = null
let serverCountdownTimer = null
let serverRetryDelayMs = 10000

const SERVER_SYNC_MIN_MS = 10000
const SERVER_SYNC_MAX_MS = 120000
const DRIFT_THRESHOLD_PCT = 5

let mountedAt = 0
let hasAction = false
let idleTriggered = false
let videoReadyTracked = false

const variantContent = {
  institutional: {
    title: 'LICEU 6.0',
    body: 'O sistema vivo que transforma comportamento em inteligência econômica.',
    arenaLabel: 'Entrar na Arena',
    ecosystemLabel: 'Ecossistema',
    johnLine: 'Posso te mostrar como isso funciona na prática. Quer entrar na Arena?'
  },
  finance: {
    title: 'Inteligência que gera valor econômico',
    body: 'Decisão imobiliária orientada por dados, risco e retorno para acelerar crescimento com governança.',
    arenaLabel: 'Simular na Arena',
    ecosystemLabel: 'Ver capital',
    johnLine: 'Se quiser, começo pela leitura financeira e te mostro o melhor próximo passo.'
  },
  social: {
    title: 'Tecnologia com impacto social real',
    body: 'Construção, educação e inclusão conectadas em um ecossistema de progresso mensurável.',
    arenaLabel: 'Ver impacto',
    ecosystemLabel: 'Explorar frentes',
    johnLine: 'Posso abrir a trilha de impacto e mostrar os indicadores sociais em tempo real.'
  },
  product: {
    title: 'Entre na Arena do futuro',
    body: 'Conheça o fluxo completo do produto: descoberta, viabilidade, execução e acompanhamento contínuo.',
    arenaLabel: 'Começar jornada',
    ecosystemLabel: 'Ver módulos',
    johnLine: 'Vamos para a Arena agora e eu te guio etapa por etapa.'
  },
  intent: {
    title: 'Transforme intenção em decisão',
    body: 'Quando há intenção de compra, a plataforma responde com análise, prioridade e ação coordenada.',
    arenaLabel: 'Ativar intenção',
    ecosystemLabel: 'Ver estratégia',
    johnLine: 'Identifiquei alta intenção. Posso acelerar seu caminho para decisão com segurança.'
  }
}

const heroClasses = computed(() => ({
  'video-ready': videoReady.value,
  'video-failed': videoFailed.value
}))

const heroCopy = computed(() => variantContent[variant.value] || variantContent.institutional)

const variantLabel = computed(() => `${variant.value.toUpperCase()} | AB ${abGroup.value}`)

const growthRows = computed(() => {
  const rows = Object.entries(growthSummary.value.variants || {}).map(([name, bucket]) => {
    const views = bucket.hero_view || 0
    const clicks = bucket.cta_click || 0
    const ctr = views > 0 ? ((clicks / views) * 100) : 0
    const avgMs = bucket.time_to_click_count > 0
      ? Math.round(bucket.time_to_click_sum / bucket.time_to_click_count)
      : 0

    return {
      name,
      views,
      clicks,
      ctr,
      avgMs,
      idle: bucket.user_idle_hero || 0
    }
  })

  return rows.sort((a, b) => b.ctr - a.ctr)
})

const growthKpis = computed(() => {
  const totals = growthSummary.value.totals || {}
  const views = totals.hero_view || 0
  const clicks = totals.cta_click || 0
  const ctr = views > 0 ? ((clicks / views) * 100) : 0
  const avgMs = totals.time_to_click_count > 0
    ? Math.round(totals.time_to_click_sum / totals.time_to_click_count)
    : 0

  return {
    views,
    clicks,
    ctr,
    avgMs,
    idle: totals.user_idle_hero || 0
  }
})

const serverKpis = computed(() => {
  const totals = serverSummary.value?.summary?.totals || {}
  const views = totals.hero_view || 0
  const clicks = totals.cta_click || 0
  const ctr = views > 0 ? ((clicks / views) * 100) : 0
  const avgMs = totals.time_to_click_count > 0
    ? Math.round(totals.time_to_click_sum / totals.time_to_click_count)
    : 0

  return {
    views,
    clicks,
    ctr,
    avgMs,
    idle: totals.user_idle_hero || 0
  }
})

function pctDiff(localValue, serverValue) {
  const a = Number(localValue) || 0
  const b = Number(serverValue) || 0

  if (a === 0 && b === 0) return 0
  if (b === 0) return 100

  return Math.abs(((a - b) / b) * 100)
}

const driftReport = computed(() => {
  const viewsDiff = pctDiff(growthKpis.value.views, serverKpis.value.views)
  const clicksDiff = pctDiff(growthKpis.value.clicks, serverKpis.value.clicks)
  const ctrDiff = pctDiff(growthKpis.value.ctr, serverKpis.value.ctr)

  const maxDiff = Math.max(viewsDiff, clicksDiff, ctrDiff)
  const hasDrift = maxDiff > DRIFT_THRESHOLD_PCT

  return {
    threshold: DRIFT_THRESHOLD_PCT,
    hasDrift,
    maxDiff,
    viewsDiff,
    clicksDiff,
    ctrDiff,
    statusLabel: hasDrift ? 'DRIFT DETECTADO' : 'SINCRONIA ESTÁVEL'
  }
})

const summaryUpdatedAt = computed(() => {
  const ts = growthSummary.value.updated_at
  if (!ts) return '--'

  return new Date(ts).toLocaleTimeString('pt-BR')
})

function refreshGrowthSummary() {
  growthSummary.value = readGrowthSummary()
}

function clearGrowthSummary() {
  resetGrowthSummary()
  refreshGrowthSummary()
}

function clearServerSyncTimers() {
  if (serverSyncTimer) {
    window.clearTimeout(serverSyncTimer)
    serverSyncTimer = null
  }

  if (serverCountdownTimer) {
    window.clearInterval(serverCountdownTimer)
    serverCountdownTimer = null
  }

  serverNextRetrySeconds.value = 0
}

function scheduleServerSync(delayMs) {
  if (typeof window === 'undefined') return
  if (typeof document !== 'undefined' && document.hidden) {
    serverSyncMode.value = 'paused'
    return
  }

  clearServerSyncTimers()

  const safeDelay = Math.max(1000, delayMs)
  const deadline = Date.now() + safeDelay
  serverSyncMode.value = 'scheduled'

  serverCountdownTimer = window.setInterval(() => {
    const left = Math.max(0, Math.ceil((deadline - Date.now()) / 1000))
    serverNextRetrySeconds.value = left
    if (left <= 0) {
      window.clearInterval(serverCountdownTimer)
      serverCountdownTimer = null
    }
  }, 250)

  serverSyncTimer = window.setTimeout(() => {
    syncServerSummary({ manual: false })
  }, safeDelay)
}

function handleVisibilityChange() {
  if (typeof document === 'undefined') return

  if (document.hidden) {
    clearServerSyncTimers()
    serverSyncMode.value = 'paused'
    return
  }

  syncServerSummary({ manual: false })
}

async function syncServerSummary({ manual = false } = {}) {
  if (serverSyncing.value && !manual) return

  serverSyncing.value = true
  serverSyncError.value = ''
  serverSyncMode.value = manual ? 'manual' : 'syncing'

  if (manual) {
    clearServerSyncTimers()
  }

  try {
    const response = await fetch('/sdk/public/growth-summary', {
      headers: {
        'X-John-SDK-Key': 'public-dev'
      }
    })

    if (!response.ok) {
      throw new Error(`status ${response.status}`)
    }

    const payload = await response.json()
    serverSummary.value = payload
    serverUpdatedAt.value = payload.updated_at || '--'
    serverRetryDelayMs = SERVER_SYNC_MIN_MS
    serverSyncMode.value = 'online'

    scheduleServerSync(serverRetryDelayMs)
  } catch (error) {
    serverSyncError.value = 'Falha ao ler resumo do servidor.'
    console.warn('[Growth] server_summary_failed', error)
    serverRetryDelayMs = Math.min(serverRetryDelayMs * 2, SERVER_SYNC_MAX_MS)
    serverSyncMode.value = 'retrying'

    scheduleServerSync(serverRetryDelayMs)
  } finally {
    serverSyncing.value = false
  }
}

const serverSyncStatusText = computed(() => {
  if (serverSyncMode.value === 'paused') return 'Auto-sync pausado (aba em segundo plano).'
  if (serverSyncMode.value === 'retrying') return `Tentando novamente em ${serverNextRetrySeconds.value}s (backoff).`
  if (serverSyncMode.value === 'scheduled') return `Próxima sincronização em ${serverNextRetrySeconds.value}s.`
  if (serverSyncMode.value === 'syncing' || serverSyncMode.value === 'manual') return 'Sincronizando com servidor...'
  if (serverSyncMode.value === 'online') return `Servidor online. Próxima atualização em ${serverNextRetrySeconds.value}s.`
  return 'Auto-sync inicializando...'
})

function isMobile() {
  if (typeof navigator === 'undefined') return false
  return /Android|iPhone|iPad|iPod/i.test(navigator.userAgent)
}

function scheduleIdle(callback) {
  if (typeof window === 'undefined') return

  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(callback)
    return
  }

  window.setTimeout(callback, 120)
}

function decideVariantByTime() {
  const hour = new Date().getHours()

  if (hour < 12) return 'finance'
  if (hour < 18) return 'product'
  return 'institutional'
}

function decideVariantContextual() {
  if (typeof document === 'undefined') return ''

  const referrer = document.referrer.toLowerCase()

  if (referrer.includes('instagram') || referrer.includes('facebook') || referrer.includes('tiktok')) {
    return 'social'
  }

  if (referrer.includes('google') || referrer.includes('bing')) {
    return 'intent'
  }

  return ''
}

function decideVariantAB() {
  if (typeof window === 'undefined') return 'A'

  const stored = window.sessionStorage.getItem('liceu_growth_ab_group')
  if (stored === 'A' || stored === 'B') return stored

  const selected = Math.random() < 0.5 ? 'A' : 'B'
  window.sessionStorage.setItem('liceu_growth_ab_group', selected)
  return selected
}

function applyAB(baseVariant, group) {
  if (group === 'A') return baseVariant

  const bMap = {
    institutional: 'product',
    finance: 'institutional',
    social: 'finance',
    product: 'social',
    intent: 'product'
  }

  return bMap[baseVariant] || 'institutional'
}

function decideVariant() {
  const contextual = decideVariantContextual()
  const timeBased = decideVariantByTime()
  const base = contextual || timeBased

  variantSource.value = contextual ? 'context' : 'time'
  abGroup.value = decideVariantAB()
  variant.value = applyAB(base, abGroup.value)
}

function loadVideo() {
  videoSrc.value = isMobile()
    ? '/videos/liceu-hero-mobile.mp4'
    : '/videos/liceu-hero.mp4'

  scheduleIdle(() => {
    videoRef.value?.load()
  })
}

function tryAutoplay() {
  const video = videoRef.value

  if (!video) return

  video.play().catch(() => {
    console.warn('[Institucional] autoplay_blocked')
    track('video_autoplay_blocked', {
      variant: variant.value,
      ab_group: abGroup.value
    })
  })
}

function handleVideoReady() {
  videoReady.value = true

  if (!videoReadyTracked) {
    videoReadyTracked = true
    track('video_ready', {
      variant: variant.value,
      ab_group: abGroup.value
    })
  }
}

function handleVideoError() {
  videoFailed.value = true
  console.warn('[Institucional] video_failed')
  track('video_error', {
    variant: variant.value,
    ab_group: abGroup.value
  })
}

function registerFirstAction(action) {
  if (hasAction) return

  hasAction = true
  const elapsed = Date.now() - mountedAt

  track('time_to_click', {
    ms: elapsed,
    action,
    variant: variant.value,
    ab_group: abGroup.value
  })

  track('idle_before_action', {
    ms: elapsed,
    idle_triggered: idleTriggered,
    variant: variant.value,
    ab_group: abGroup.value
  })
}

function goArena() {
  registerFirstAction('cta_arena')
  track('cta_click', {
    target: 'arena',
    route: '/archimedes',
    variant: variant.value,
    ab_group: abGroup.value,
    source: variantSource.value
  })

  if (typeof window !== 'undefined') {
    window.localStorage.setItem('liceu_last_cta_target', 'arena')
  }

  router.push('/archimedes')
}

function goDashboard() {
  registerFirstAction('cta_ecossistema')
  track('cta_click', {
    target: 'ecossistema',
    route: '/investidores',
    variant: variant.value,
    ab_group: abGroup.value,
    source: variantSource.value
  })

  if (typeof window !== 'undefined') {
    window.localStorage.setItem('liceu_last_cta_target', 'ecossistema')
  }

  router.push('/investidores')
}

onMounted(() => {
  mountedAt = Date.now()

  if (typeof window !== 'undefined') {
    window.addEventListener('growth:summary-updated', refreshGrowthSummary)
    document.addEventListener('visibilitychange', handleVisibilityChange)
  }

  syncServerSummary()

  decideVariant()
  johnPrompt.value = heroCopy.value.johnLine

  track('hero_variant_assigned', {
    variant: variant.value,
    ab_group: abGroup.value,
    source: variantSource.value
  })

  track('hero_view', {
    variant: variant.value,
    ab_group: abGroup.value,
    source: variantSource.value
  })

  loadVideo()

  autoplayTimer = window.setTimeout(() => {
    tryAutoplay()
  }, 300)

  johnTimer = window.setTimeout(() => {
    showJohn.value = true
    track('john_prompt_visible', {
      variant: variant.value,
      ab_group: abGroup.value
    })
  }, 5000)

  idleTimer = window.setTimeout(() => {
    if (hasAction) return

    idleTriggered = true
    johnPrompt.value = 'Posso te mostrar como isso funciona na prática. Quer entrar na Arena?'

    track('user_idle_hero', {
      ms: Date.now() - mountedAt,
      variant: variant.value,
      ab_group: abGroup.value
    })
  }, 6000)
})

onBeforeUnmount(() => {
  if (autoplayTimer) window.clearTimeout(autoplayTimer)
  if (johnTimer) window.clearTimeout(johnTimer)
  if (idleTimer) window.clearTimeout(idleTimer)
  clearServerSyncTimers()

  if (typeof window !== 'undefined') {
    window.removeEventListener('growth:summary-updated', refreshGrowthSummary)
    document.removeEventListener('visibilitychange', handleVisibilityChange)
  }
})
</script>

<template>
  <div class="institucional">
    <section class="hero" :class="heroClasses">
      <img
        class="hero-poster"
        src="/images/liceu-poster.jpg"
        alt="LICEU 6.0"
        loading="eager"
      />

      <video
        ref="videoRef"
        class="hero-video"
        autoplay
        muted
        loop
        playsinline
        preload="none"
        @canplay="handleVideoReady"
        @playing="handleVideoReady"
        @error="handleVideoError"
      >
        <source :src="videoSrc" type="video/mp4" />
      </video>

      <div class="hero-shade"></div>

      <div class="overlay">
        <span class="eyebrow">LICEU 6.0 INSTITUCIONAL</span>
        <div class="variant-chip">{{ variantLabel }}</div>
        <h1>{{ heroCopy.title }}</h1>

        <p>
          {{ heroCopy.body }}
        </p>

        <div class="cta">
          <button class="cta-primary" @click="goArena">{{ heroCopy.arenaLabel }}</button>
          <button class="cta-secondary" @click="goDashboard">{{ heroCopy.ecosystemLabel }}</button>
        </div>

        <transition name="john-fade">
          <div v-if="showJohn" class="john-lite" aria-live="polite">
            <div class="john-badge">JOHN</div>
            <strong>Bem-vindo ao LICEU 6.0.</strong>
            <p>{{ johnPrompt }}</p>
          </div>
        </transition>
      </div>
    </section>

    <section class="institutional-grid">
      <article class="info-card">
        <span>Infra viva</span>
        <h2>Construção, capital e operação conectados</h2>
        <p>
          Uma fachada pública que explica o ecossistema sem interferir nas jornadas existentes do app.
        </p>
      </article>

      <article class="info-card">
        <span>Performance</span>
        <h2>Poster primeiro, vídeo depois</h2>
        <p>
          O carregamento prioriza o poster para LCP rápido e ativa o vídeo apenas quando o navegador estiver livre.
        </p>
      </article>

      <article class="info-card">
        <span>Compatibilidade</span>
        <h2>Sem store novo, sem event bus</h2>
        <p>
          A integração com o John nesta página é local e leve, sem websocket nem dependência do fluxo da Arena.
        </p>
      </article>

      <article class="info-card growth-card">
        <div class="growth-head">
          <div>
            <span>Growth real-time</span>
            <h2>Painel por variante</h2>
          </div>
          <button class="growth-reset" @click="clearGrowthSummary">Resetar métricas</button>
        </div>

        <p class="growth-updated">Atualizado às {{ summaryUpdatedAt }}</p>

        <div class="growth-kpis">
          <div class="kpi-pill">
            <strong>{{ growthKpis.views }}</strong>
            <small>Views</small>
          </div>
          <div class="kpi-pill">
            <strong>{{ growthKpis.clicks }}</strong>
            <small>CTAs</small>
          </div>
          <div class="kpi-pill">
            <strong>{{ growthKpis.ctr.toFixed(1) }}%</strong>
            <small>CTR</small>
          </div>
          <div class="kpi-pill">
            <strong>{{ growthKpis.avgMs }}ms</strong>
            <small>Tempo até clique</small>
          </div>
        </div>

        <div class="growth-table-wrap">
          <table class="growth-table">
            <thead>
              <tr>
                <th>Variante</th>
                <th>Views</th>
                <th>CTA</th>
                <th>CTR</th>
                <th>Tempo médio</th>
                <th>Idle</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in growthRows" :key="row.name">
                <td>{{ row.name }}</td>
                <td>{{ row.views }}</td>
                <td>{{ row.clicks }}</td>
                <td>{{ row.ctr.toFixed(1) }}%</td>
                <td>{{ row.avgMs }}ms</td>
                <td>{{ row.idle }}</td>
              </tr>
              <tr v-if="growthRows.length === 0">
                <td colspan="6">Sem dados ainda. Interaja com o hero para popular as métricas.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="server-growth">
          <div class="server-growth-head">
            <h3>Resumo servidor</h3>
            <button class="growth-reset" :disabled="serverSyncing" @click="syncServerSummary">
              {{ serverSyncing ? 'Sincronizando...' : 'Sincronizar servidor' }}
            </button>
          </div>

          <p class="growth-updated">Atualizado no servidor: {{ serverUpdatedAt }}</p>
          <p class="growth-updated">{{ serverSyncStatusText }}</p>
          <p v-if="serverSyncError" class="server-error">{{ serverSyncError }}</p>

          <div class="growth-kpis">
            <div class="kpi-pill">
              <strong>{{ serverKpis.views }}</strong>
              <small>Views servidor</small>
            </div>
            <div class="kpi-pill">
              <strong>{{ serverKpis.clicks }}</strong>
              <small>CTAs servidor</small>
            </div>
            <div class="kpi-pill">
              <strong>{{ serverKpis.ctr.toFixed(1) }}%</strong>
              <small>CTR servidor</small>
            </div>
            <div class="kpi-pill">
              <strong>{{ serverKpis.avgMs }}ms</strong>
              <small>Tempo médio servidor</small>
            </div>
          </div>

          <div class="drift-detector" :class="driftReport.hasDrift ? 'is-alert' : 'is-ok'">
            <div class="drift-head">
              <strong>{{ driftReport.statusLabel }}</strong>
              <span>Limiar: {{ driftReport.threshold }}%</span>
            </div>

            <div class="drift-grid">
              <div>
                <small>Views</small>
                <b>{{ driftReport.viewsDiff.toFixed(1) }}%</b>
              </div>
              <div>
                <small>CTA</small>
                <b>{{ driftReport.clicksDiff.toFixed(1) }}%</b>
              </div>
              <div>
                <small>CTR</small>
                <b>{{ driftReport.ctrDiff.toFixed(1) }}%</b>
              </div>
              <div>
                <small>Pico</small>
                <b>{{ driftReport.maxDiff.toFixed(1) }}%</b>
              </div>
            </div>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>

<style scoped>
.institucional {
  min-height: 100vh;
  background: #000;
  color: #fff;
}

.hero {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at top right, rgba(179, 143, 0, 0.3), transparent 28%),
    linear-gradient(135deg, #02060c 0%, #08172f 48%, #000 100%);
}

.hero-poster,
.hero-video,
.hero-shade {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.hero-poster,
.hero-video {
  object-fit: cover;
}

.hero-poster {
  z-index: 1;
}

.hero-video {
  z-index: 2;
  opacity: 0;
  transition: opacity 1.2s ease;
}

.hero.video-ready .hero-video {
  opacity: 1;
}

.hero.video-ready .hero-poster {
  opacity: 0.5;
}

.hero.video-failed .hero-poster {
  opacity: 1;
}

.hero-shade {
  z-index: 3;
  background:
    linear-gradient(90deg, rgba(0, 0, 0, 0.78) 0%, rgba(0, 0, 0, 0.25) 52%, rgba(0, 0, 0, 0.72) 100%),
    linear-gradient(180deg, rgba(1, 6, 12, 0.4) 0%, rgba(1, 6, 12, 0.78) 100%);
}

.overlay {
  position: relative;
  z-index: 4;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 100vh;
  max-width: 680px;
  padding: 80px;
}

.eyebrow {
  display: inline-flex;
  width: fit-content;
  padding: 8px 14px;
  margin-bottom: 22px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 999px;
  font-size: 0.74rem;
  font-weight: 700;
  letter-spacing: 0.18em;
  background: rgba(255, 255, 255, 0.06);
}

.variant-chip {
  width: fit-content;
  margin-bottom: 14px;
  padding: 6px 12px;
  border-radius: 10px;
  border: 1px solid rgba(204, 176, 108, 0.45);
  color: #dcc182;
  background: rgba(204, 176, 108, 0.08);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.overlay h1 {
  font-size: clamp(3rem, 8vw, 5.2rem);
  line-height: 0.95;
  font-weight: 800;
  letter-spacing: -0.04em;
}

.overlay p {
  margin-top: 24px;
  max-width: 560px;
  font-size: 1.1rem;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.84);
}

.cta {
  margin-top: 32px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.cta button {
  padding: 14px 24px;
  border: none;
  border-radius: 999px;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 700;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.cta-primary {
  background: #fff;
  color: #000;
  box-shadow: 0 16px 40px rgba(255, 255, 255, 0.14);
}

.cta-secondary {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.cta button:hover {
  transform: translateY(-2px);
}

.john-lite {
  width: min(420px, 100%);
  margin-top: 36px;
  padding: 18px 20px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 18px;
  background: rgba(5, 13, 28, 0.58);
  backdrop-filter: blur(14px);
  box-shadow: 0 20px 45px rgba(0, 0, 0, 0.35);
}

.john-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: fit-content;
  padding: 5px 10px;
  margin-bottom: 12px;
  border-radius: 999px;
  background: linear-gradient(135deg, #8f7420, #d2b459);
  color: #0a0a0a;
  font-size: 0.72rem;
  font-weight: 800;
}

.john-lite strong {
  display: block;
  margin-bottom: 8px;
  font-size: 1rem;
}

.john-lite p {
  margin: 0;
  font-size: 0.95rem;
}

.institutional-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
  padding: 32px 40px 60px;
  background: linear-gradient(180deg, rgba(6, 12, 24, 0.96) 0%, #040404 100%);
}

.info-card {
  padding: 24px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.03);
}

.info-card span {
  display: block;
  margin-bottom: 10px;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.16em;
  color: #ccb06c;
  text-transform: uppercase;
}

.info-card h2 {
  margin-bottom: 12px;
  font-size: 1.5rem;
  line-height: 1.15;
}

.info-card p {
  margin: 0;
  color: rgba(255, 255, 255, 0.76);
}

.growth-card {
  grid-column: 1 / -1;
}

.growth-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.growth-reset {
  border: 1px solid rgba(255, 255, 255, 0.22);
  background: rgba(255, 255, 255, 0.04);
  color: #fff;
  border-radius: 999px;
  padding: 8px 14px;
  cursor: pointer;
  font-weight: 600;
}

.growth-updated {
  margin-top: 10px;
  font-size: 0.88rem;
  color: rgba(255, 255, 255, 0.62);
}

.growth-kpis {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.kpi-pill {
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
}

.kpi-pill strong {
  display: block;
  font-size: 1.1rem;
}

.kpi-pill small {
  color: rgba(255, 255, 255, 0.66);
}

.growth-table-wrap {
  margin-top: 16px;
  overflow-x: auto;
}

.growth-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 620px;
}

.growth-table th,
.growth-table td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 0.9rem;
}

.growth-table thead th {
  color: #ccb06c;
  font-weight: 700;
}

.server-growth {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.server-growth-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.server-growth-head h3 {
  margin: 0;
  font-size: 1rem;
}

.server-error {
  margin-top: 8px;
  color: #ff9b8e;
}

.drift-detector {
  margin-top: 16px;
  border-radius: 14px;
  padding: 12px;
  border: 1px solid transparent;
}

.drift-detector.is-ok {
  border-color: rgba(54, 197, 129, 0.36);
  background: rgba(54, 197, 129, 0.08);
}

.drift-detector.is-alert {
  border-color: rgba(255, 155, 142, 0.48);
  background: rgba(255, 155, 142, 0.1);
}

.drift-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.drift-head strong {
  font-size: 0.9rem;
}

.drift-head span {
  font-size: 0.8rem;
  opacity: 0.8;
}

.drift-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.drift-grid div {
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 10px;
  padding: 8px;
  background: rgba(0, 0, 0, 0.16);
}

.drift-grid small {
  display: block;
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.72);
}

.drift-grid b {
  font-size: 0.92rem;
}

.john-fade-enter-active,
.john-fade-leave-active {
  transition: opacity 0.5s ease, transform 0.5s ease;
}

.john-fade-enter-from,
.john-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@media (max-width: 900px) {
  .institutional-grid {
    grid-template-columns: 1fr;
  }

  .growth-kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .drift-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .overlay {
    padding: 32px 24px 48px;
  }

  .overlay h1 {
    font-size: 2.6rem;
  }

  .overlay p {
    font-size: 1rem;
  }

  .cta {
    flex-direction: column;
  }

  .cta button {
    width: 100%;
  }

  .institutional-grid {
    padding: 24px 24px 40px;
  }
}
</style>