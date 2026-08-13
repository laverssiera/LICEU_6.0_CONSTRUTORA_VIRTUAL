const EMIT_ENDPOINT = '/sdk/public/emit'
const PUBLIC_KEY = process.env.VITE_GROWTH_SDK_KEY || 'public-dev'
const SUMMARY_KEY = 'liceu_growth_summary_v1'
const VALID_EVENTS = new Set(['hero_view', 'cta_click', 'user_idle_hero', 'time_to_click'])
const MAX_STORAGE_SIZE = 100000 // ~100KB limit para localStorage

function createEmptySummary() {
  return {
    updated_at: Date.now(),
    totals: {
      hero_view: 0,
      cta_click: 0,
      user_idle_hero: 0,
      time_to_click_sum: 0,
      time_to_click_count: 0
    },
    variants: {}
  }
}

function ensureVariant(summary, variant) {
  // Validar variant: aceitar string nao-vazia, sanitizar
  const key = (variant && String(variant).trim()) || 'default'
  
  if (key.length > 50) {
    console.warn('[Growth] variant excede limite de 50 caracteres, truncado')
    key = key.substring(0, 50)
  }

  if (!summary.variants[key]) {
    summary.variants[key] = {
      hero_view: 0,
      cta_click: 0,
      user_idle_hero: 0,
      time_to_click_sum: 0,
      time_to_click_count: 0
    }
  }

  return summary.variants[key]
}

function loadSummary() {
  if (typeof window === 'undefined') return createEmptySummary()

  try {
    const raw = window.localStorage.getItem(SUMMARY_KEY)
    if (!raw) return createEmptySummary()

    const parsed = JSON.parse(raw)
    
    // Validar estrutura minima
    if (!parsed.totals || !parsed.variants) {
      console.warn('[Growth] localStorage corrompido, reset iniciado')
      return createEmptySummary()
    }

    return {
      ...createEmptySummary(),
      ...parsed
    }
  } catch (error) {
    console.error('[Growth] erro ao carregar summary:', error)
    return createEmptySummary()
  }
}

function saveSummary(summary) {
  if (typeof window === 'undefined') return

  try {
    const serialized = JSON.stringify(summary)
    
    // Verificar tamanho limite
    if (serialized.length > MAX_STORAGE_SIZE) {
      console.warn('[Growth] summary execeu limite de storage, truncando variants antigos')
      // Manter apenas as 5 variants mais recentes por contagem
      const topVariants = Object.entries(summary.variants)
        .sort(([, a], [, b]) => (b.hero_view + b.cta_click) - (a.hero_view + a.cta_click))
        .slice(0, 5)
      
      summary.variants = Object.fromEntries(topVariants)
    }

    window.localStorage.setItem(SUMMARY_KEY, JSON.stringify(summary))
  } catch (error) {
    console.error('[Growth] erro ao salvar summary:', error)
  }
}

function notifyUpdate(summary) {
  if (typeof window === 'undefined') return
  
  try {
    window.dispatchEvent(new CustomEvent('growth:summary-updated', { detail: summary }))
  } catch (error) {
    console.warn('[Growth] erro ao disparar evento:', error)
  }
}

function updateSummary(payload) {
  // Validar evento
  if (!VALID_EVENTS.has(payload.event)) {
    console.warn(`[Growth] evento invalido: ${payload.event}`)
    return
  }

  const summary = loadSummary()
  const variantBucket = ensureVariant(summary, payload.variant)
  const event = payload.event

  // Atualizar counter correspondente
  switch (event) {
    case 'hero_view':
      summary.totals.hero_view += 1
      variantBucket.hero_view += 1
      break

    case 'cta_click':
      summary.totals.cta_click += 1
      variantBucket.cta_click += 1
      break

    case 'user_idle_hero':
      summary.totals.user_idle_hero += 1
      variantBucket.user_idle_hero += 1
      break

    case 'time_to_click':
      if (!Number.isFinite(payload.ms) || payload.ms < 0) {
        console.warn('[Growth] time_to_click invalido:', payload.ms)
        break
      }
      summary.totals.time_to_click_sum += payload.ms
      summary.totals.time_to_click_count += 1
      variantBucket.time_to_click_sum += payload.ms
      variantBucket.time_to_click_count += 1
      break
  }

  summary.updated_at = Date.now()
  saveSummary(summary)
  notifyUpdate(summary)
}

export function readGrowthSummary() {
  const summary = loadSummary()
  
  // Calcular medias uteis
  const avgTimeToClick = summary.totals.time_to_click_count > 0
    ? Math.round(summary.totals.time_to_click_sum / summary.totals.time_to_click_count)
    : 0

  return {
    ...summary,
    derived: {
      avg_time_to_click_ms: avgTimeToClick,
      ctr: summary.totals.hero_view > 0
        ? (summary.totals.cta_click / summary.totals.hero_view * 100).toFixed(2) + '%'
        : '0%'
    }
  }
}

export function resetGrowthSummary() {
  if (typeof window === 'undefined') return

  try {
    const empty = createEmptySummary()
    window.localStorage.setItem(SUMMARY_KEY, JSON.stringify(empty))
    notifyUpdate(empty)
  } catch (error) {
    console.error('[Growth] erro ao resetar summary:', error)
  }
}

export function track(event, data = {}) {
  if (typeof window === 'undefined') return

  // Validar evento antes de processar
  if (!VALID_EVENTS.has(event)) {
    console.warn(`[Growth] tentativa de rastreamento de evento invalido: ${event}`)
    return
  }

  const payload = {
    event,
    ts: Date.now(),
    path: window.location.pathname,
    user_agent: navigator.userAgent,
    ...data
  }

  console.log('[Growth]', payload)

  // Atualizar localmente
  updateSummary(payload)

  // Enviar para backend (fire-and-forget, sem bloquear)
  if (navigator.sendBeacon) {
    // Preferir sendBeacon para melhor confiabilidade em unload
    navigator.sendBeacon(EMIT_ENDPOINT, JSON.stringify({
      type: 'growth.event',
      payload
    }))
  } else {
    // Fallback para fetch
    fetch(EMIT_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-John-SDK-Key': PUBLIC_KEY
      },
      body: JSON.stringify({
        type: 'growth.event',
        payload
      }),
      keepalive: true
    }).catch((error) => {
      console.warn('[Growth] falha ao emitir evento:', error.message)
    })
  }
}
