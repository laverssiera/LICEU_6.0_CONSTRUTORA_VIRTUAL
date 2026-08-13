<template>
  <div class="portal-page investors-page">
    <header class="page-header">
      <button class="back-btn" @click="$router.push('/archimedes')">← Voltar para a jornada</button>
      <span class="eyebrow">SMART CAPITAL</span>
      <h1>Investidores e capital inteligente</h1>
      <p>
        Acompanhe oportunidades, governança e o avanço dos projetos com visão orientada por dados.
      </p>
    </header>

    <p v-if="isLoading" class="status status-loading">Carregando dados de investor relations...</p>
    <p v-else-if="errorMessage" class="status status-error">{{ errorMessage }}</p>

    <section class="stats-grid">
      <article v-for="item in stats" :key="item.title" class="stat-card">
        <strong>{{ item.value }}</strong>
        <span>{{ item.title }}</span>
      </article>
    </section>

    <section class="quant-panel">
      <h2>Carteira Quantitativa</h2>
      <p>Tamanho da carteira: {{ quantSummary.portfolioSize }} ativos</p>
      <p>Retorno esperado (ponderado): {{ quantSummary.expectedReturn }}</p>
      <p>Eventos QUANT publicados: {{ quantSummary.eventsPublished }}</p>
      <div class="quant-actions">
        <button class="action-btn" :disabled="isRebalancing" @click="rebalancePortfolio">
          {{ isRebalancing ? 'Rebalanceando...' : 'Rebalancear carteira' }}
        </button>
        <p v-if="rebalanceFeedback" class="rebalance-feedback">{{ rebalanceFeedback }}</p>
      </div>
    </section>

    <section class="lex-panel">
      <h2>Mercado Secundario (LEX)</h2>
      <p>P&L consolidado: {{ lexSummary.pnl }}</p>
      <p>Ordens abertas: {{ lexSummary.openOrders }}</p>
      <p>Trades executados: {{ lexSummary.executedTrades }}</p>
      <p>Eventos LEX publicados: {{ lexSummary.eventsPublished }}</p>
      <div class="lex-fair-box">
        <strong>Preco justo de referencia:</strong>
        <span>{{ lexFairSnapshot.fairPrice }}</span>
        <small>Mercado: {{ lexFairSnapshot.marketPrice }} | John: {{ lexFairSnapshot.recommendation }}</small>
      </div>
    </section>

    <section class="content-grid">
      <article class="panel-card" v-for="item in opportunities" :key="item.id">
        <h2>{{ item.title }}</h2>
        <p>{{ item.text }}</p>
        <button class="action-btn" @click="openOpportunity(item)">Abrir oportunidade</button>
      </article>
    </section>

    <section v-if="selectedOpportunity" class="opportunity-modal-backdrop" @click="closeOpportunityModal">
      <article class="opportunity-modal" @click.stop>
        <header class="opportunity-modal-head">
          <h2>Analise de oportunidade</h2>
          <div class="modal-head-actions">
            <span v-if="isSafeDemoRunning" class="presentation-badge">MODO APRESENTACAO ATIVO</span>
            <button class="modal-close" @click="closeOpportunityModal">Fechar</button>
          </div>
        </header>

        <div class="modal-grid">
          <p><strong>Projeto:</strong> {{ selectedOpportunity.projectId }}</p>
          <p><strong>Risco:</strong> {{ selectedOpportunity.riskLevel }}</p>
          <p><strong>Retorno esperado:</strong> {{ selectedOpportunity.expectedReturn }}%</p>
          <p><strong>Eventos IR publicados:</strong> {{ publishedTopics.length }}</p>
        </div>

        <section class="modal-block">
          <h3>Explicacao John</h3>
          <p>{{ dashboardPayload.john_pitch || 'Pitch indisponivel no momento.' }}</p>
        </section>

        <section class="modal-block">
          <h3>Historico de rebalanceamento</h3>
          <ul v-if="recentRebalances.length" class="rebalance-list">
            <li v-for="(item, idx) in recentRebalances" :key="`${item.project_id}-${idx}`">
              Projeto {{ item.project_id }} -> {{ item.action }} ({{ item.reason }})
            </li>
          </ul>
          <p v-else>Nenhuma acao de rebalance registrada.</p>
        </section>

        <section class="modal-block">
          <h3>Preco justo da oportunidade (LEX)</h3>
          <p>Preco justo: {{ selectedFairSnapshot.fairPrice }}</p>
          <p>Preco de mercado: {{ selectedFairSnapshot.marketPrice }}</p>
          <p>Recomendacao John: {{ selectedFairSnapshot.recommendation }}</p>
        </section>

        <section class="modal-block">
          <h3>Trading (LEX)</h3>
          <p v-if="isSafeDemoRunning" class="presentation-lock-note">
            Controles manuais bloqueados durante a Demo Segura.
          </p>
          <div class="trade-grid">
            <label>
              Investidor
              <input v-model="tradeForm.investorId" type="text" :disabled="manualInputLocked" />
            </label>
            <label>
              Lado
              <select v-model="tradeForm.side" :disabled="manualInputLocked">
                <option value="buy">buy</option>
                <option value="sell">sell</option>
              </select>
            </label>
            <label>
              Tipo
              <select v-model="tradeForm.orderType" :disabled="manualInputLocked">
                <option value="limit">limit</option>
                <option value="market">market</option>
                <option value="stop">stop</option>
                <option value="iceberg">iceberg</option>
              </select>
            </label>
            <label>
              Preco
              <input v-model.number="tradeForm.price" type="number" min="0" step="0.01" :disabled="manualInputLocked" />
            </label>
            <label v-if="tradeForm.orderType === 'stop'">
              Stop
              <input v-model.number="tradeForm.stopPrice" type="number" min="0" step="0.01" :disabled="manualInputLocked" />
            </label>
            <label v-if="tradeForm.orderType === 'iceberg'">
              Visivel
              <input v-model.number="tradeForm.visibleQuantity" type="number" min="1" step="1" :disabled="manualInputLocked" />
            </label>
            <label>
              Quantidade
              <input v-model.number="tradeForm.quantity" type="number" min="1" step="1" :disabled="manualInputLocked" />
            </label>
          </div>
          <div class="trade-grid trade-grid-secondary">
            <label>
              Deposito (R$)
              <input v-model.number="tradeForm.cashDeposit" type="number" min="0" step="100" :disabled="manualInputLocked" />
            </label>
            <label>
              Inventario SELL
              <input v-model.number="tradeForm.inventoryQuantity" type="number" min="0" step="1" :disabled="manualInputLocked" />
            </label>
            <label>
              Market maker conf.
              <input v-model.number="tradeForm.mmConfidence" type="number" min="0" max="1" step="0.05" :disabled="manualInputLocked" />
            </label>
            <label>
              Subscricao fundo (R$)
              <input v-model.number="tradeForm.fundSubscriptionAmount" type="number" min="0" step="100" :disabled="manualInputLocked" />
            </label>
          </div>
          <div class="trade-actions">
            <button class="action-btn" :disabled="isTrading || manualInputLocked" @click="submitLexOrder">
              {{ isTrading ? 'Enviando...' : 'Enviar ordem' }}
            </button>
            <button class="action-btn ghost" :disabled="isTrading || manualInputLocked" @click="executeLexMatching">
              {{ isTrading ? 'Processando...' : 'Rodar matching' }}
            </button>
            <button class="action-btn executive" :disabled="isTrading || manualInputLocked" @click="runExecutiveLexDemoFlow">
              {{ isTrading ? 'Executando...' : 'Demo executiva 1 clique' }}
            </button>
            <button class="action-btn safe" :disabled="isTrading" @click="runSafeLexDemoFlow">
              {{ isTrading ? 'Executando...' : 'Demo segura' }}
            </button>
            <button class="action-btn ghost" :disabled="isTrading || manualInputLocked" @click="runLexSetupFlow">
              {{ isTrading ? 'Processando...' : 'Preparar clearing' }}
            </button>
            <button class="action-btn ghost" :disabled="isTrading || manualInputLocked" @click="loadLexMarketData">
              {{ isTrading ? 'Consultando...' : 'Atualizar mercado' }}
            </button>
            <button class="action-btn ghost" :disabled="isTrading || manualInputLocked" @click="subscribeDefaultFund">
              {{ isTrading ? 'Processando...' : 'Subscrever fundo' }}
            </button>
          </div>
          <p v-if="tradeFeedback" class="trade-feedback">{{ tradeFeedback }}</p>

          <div class="lex-insights-grid">
            <article class="lex-insight-card">
              <strong>Market maker</strong>
              <p>Bid {{ marketMakerSnapshot.bid }} | Ask {{ marketMakerSnapshot.ask }}</p>
              <small>Spread {{ marketMakerSnapshot.spread }} | Depth {{ marketMakerSnapshot.depth }}</small>
            </article>
            <article class="lex-insight-card">
              <strong>Indices</strong>
              <p>{{ indexSnapshot.summary }}</p>
            </article>
            <article class="lex-insight-card">
              <strong>Fundos</strong>
              <p>{{ fundsSnapshot.summary }}</p>
            </article>
            <article class="lex-insight-card">
              <strong>John (gestor)</strong>
              <p>{{ johnMarketBrief }}</p>
            </article>
          </div>
        </section>
      </article>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

import {
  getIRDashboard,
  getIREventsPublished,
  getLexDashboard,
  getLexEventsPublished,
  getLexFairPrice,
  getLexMarketMakerQuote,
  recalculateLexIndices,
  getLexFunds,
  subscribeLexFund,
  getLexJohnMarketBrief,
  approveLexKyc,
  depositLexCash,
  grantLexInventory,
  createLexOrder,
  runLexMatching,
  getQuantDashboard,
  getQuantEventsPublished,
  runQuantRebalance,
} from '@/services/api'

const isLoading = ref(false)
const errorMessage = ref('')
const dashboardPayload = ref({ metrics: {}, open_opportunities: [], john_pitch: '' })
const publishedTopics = ref([])
const quantDashboardPayload = ref({ portfolio_size: 0, expected_return_weighted: 0, allocations: [], rebalances: [] })
const quantPublishedTopics = ref([])
const lexDashboardPayload = ref({ assets: [], positions: [], order_book: [], trades: [], pnl: 0 })
const lexPublishedTopics = ref([])
const lexFairPayload = ref({ fair_price: 0, market_price: 0, john_recommendation: 'manter' })
const isRebalancing = ref(false)
const rebalanceFeedback = ref('')
const selectedOpportunity = ref(null)
const selectedFairPayload = ref({ fair_price: 0, market_price: 0, john_recommendation: 'manter' })
const isTrading = ref(false)
const tradeFeedback = ref('')
const selectedAssetId = ref('')
const lexIndicesPayload = ref({ indices: [] })
const lexFundsPayload = ref({ funds: [] })
const marketMakerPayload = ref({ bid: 0, ask: 0, spread: 0, depth: 0 })
const johnMarketBrief = ref('Sem briefing no momento.')
const isSafeDemoRunning = ref(false)
const DEMO_SAFE_BUYER_ID = 'INVESTOR_DEMO_SAFE_BUYER'
const DEMO_SAFE_SELLER_ID = 'INVESTOR_DEMO_SAFE_SELLER'
const tradeForm = ref({
  investorId: 'INVESTOR_DEMO_1',
  side: 'buy',
  orderType: 'limit',
  price: 100,
  stopPrice: 0,
  visibleQuantity: 25,
  quantity: 100,
  cashDeposit: 20000,
  inventoryQuantity: 200,
  mmConfidence: 0.65,
  fundSubscriptionAmount: 5000,
})

const stats = computed(() => {
  const metrics = dashboardPayload.value.metrics || {}
  return [
    { title: 'projetos ativos', value: String(metrics.active_projects || 0) },
    { title: 'capital alocado', value: formatCurrency(metrics.total_allocated || 0) },
    { title: 'ROI consolidado', value: `${metrics.roi_consolidated || 0}%` },
    { title: 'carteira quant', value: String(quantDashboardPayload.value.portfolio_size || 0) }
  ]
})

const quantSummary = computed(() => ({
  portfolioSize: quantDashboardPayload.value.portfolio_size || 0,
  expectedReturn: formatCurrency(quantDashboardPayload.value.expected_return_weighted || 0),
  eventsPublished: quantPublishedTopics.value.length,
}))

const lexSummary = computed(() => ({
  pnl: formatCurrency(lexDashboardPayload.value.pnl || 0),
  openOrders: (lexDashboardPayload.value.order_book || []).length,
  executedTrades: (lexDashboardPayload.value.trades || []).length,
  eventsPublished: lexPublishedTopics.value.length,
}))

const lexFairSnapshot = computed(() => ({
  fairPrice: formatCurrency(lexFairPayload.value.fair_price || 0),
  marketPrice: formatCurrency(lexFairPayload.value.market_price || 0),
  recommendation: lexFairPayload.value.john_recommendation || 'manter',
}))

const selectedFairSnapshot = computed(() => ({
  fairPrice: formatCurrency(selectedFairPayload.value.fair_price || 0),
  marketPrice: formatCurrency(selectedFairPayload.value.market_price || 0),
  recommendation: selectedFairPayload.value.john_recommendation || 'manter',
}))

const marketMakerSnapshot = computed(() => ({
  bid: formatCurrency(marketMakerPayload.value.bid || 0),
  ask: formatCurrency(marketMakerPayload.value.ask || 0),
  spread: formatCurrency(marketMakerPayload.value.spread || 0),
  depth: Number(marketMakerPayload.value.depth || 0),
}))

const indexSnapshot = computed(() => {
  const list = lexIndicesPayload.value.indices || []
  if (!list.length) return { summary: 'Sem indices recalculados.' }
  const top = list.slice(0, 2).map((item) => `${item.code}: ${formatCurrency(item.value)}`)
  return { summary: top.join(' | ') }
})

const fundsSnapshot = computed(() => {
  const list = lexFundsPayload.value.funds || []
  if (!list.length) return { summary: 'Sem fundos carregados.' }
  const labels = list.slice(0, 2).map((item) => `${item.name} (${formatCurrency(item.total_value)})`)
  return { summary: labels.join(' | ') }
})

const manualInputLocked = computed(() => isSafeDemoRunning.value)

const recentRebalances = computed(() => {
  const list = quantDashboardPayload.value.rebalances || []
  return [...list].reverse().slice(0, 5)
})

const opportunities = computed(() => {
  const items = dashboardPayload.value.open_opportunities || []
  if (!items.length) {
    return [
      {
        id: 'fallback-opportunity',
        title: 'Sem oportunidades abertas no momento',
        text: 'Assim que o IR publicar uma nova oportunidade, ela aparecera aqui em tempo real.',
        projectId: '-',
        riskLevel: '-',
        expectedReturn: 0
      }
    ]
  }

  return items.map((item) => ({
    id: item.id,
    title: item.project_id || 'Projeto sem identificador',
    text: `Programa ${item.program || 'infra'} | Risco ${item.risk_level || '-'} | Retorno esperado ${item.expected_return || 0}%`,
    projectId: item.project_id,
    riskLevel: item.risk_level,
    expectedReturn: item.expected_return
  }))
})

function formatCurrency(value) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
    maximumFractionDigits: 0
  }).format(Number(value || 0))
}

function normalizeProxyResult(responseData) {
  if (!responseData) return {}
  if (responseData.result && typeof responseData.result === 'object') return responseData.result
  return responseData
}

function mapRiskToNumber(riskLevel) {
  const risk = String(riskLevel || '').toLowerCase()
  if (risk === 'low') return 0.2
  if (risk === 'moderate' || risk === 'moderado') return 0.4
  if (risk === 'high' || risk === 'agressivo') return 0.7
  if (risk === 'critical') return 0.9
  return 0.4
}

async function loadLexFairPrice(roi, risk, progress = 65) {
  const { data } = await getLexFairPrice(Number(roi || 0), Number(risk || 0.4), Number(progress || 65))
  return normalizeProxyResult(data)
}

async function loadInvestorRelationsData() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const [
      dashboardResponse,
      eventsResponse,
      quantDashboardResponse,
      quantEventsResponse,
      lexDashboardResponse,
      lexEventsResponse,
    ] = await Promise.all([
      getIRDashboard(),
      getIREventsPublished(),
      getQuantDashboard(),
      getQuantEventsPublished(),
      getLexDashboard(),
      getLexEventsPublished(),
    ])

    dashboardPayload.value = {
      metrics: {},
      open_opportunities: [],
      john_pitch: '',
      ...normalizeProxyResult(dashboardResponse.data)
    }

    const eventsResult = normalizeProxyResult(eventsResponse.data)
    publishedTopics.value = eventsResult.topics || []

    quantDashboardPayload.value = {
      portfolio_size: 0,
      expected_return_weighted: 0,
      allocations: [],
      rebalances: [],
      ...normalizeProxyResult(quantDashboardResponse.data)
    }

    const quantEventsResult = normalizeProxyResult(quantEventsResponse.data)
    quantPublishedTopics.value = quantEventsResult.topics || []

    lexDashboardPayload.value = {
      assets: [],
      positions: [],
      order_book: [],
      trades: [],
      pnl: 0,
      ...normalizeProxyResult(lexDashboardResponse.data)
    }

    const lexEventsResult = normalizeProxyResult(lexEventsResponse.data)
    lexPublishedTopics.value = lexEventsResult.topics || []

    await loadLexMarketData()

    const primaryOpportunity = (dashboardPayload.value.open_opportunities || [])[0]
    if (primaryOpportunity) {
      lexFairPayload.value = await loadLexFairPrice(
        primaryOpportunity.expected_return,
        mapRiskToNumber(primaryOpportunity.risk_level),
        65,
      )
    }
  } catch (error) {
    errorMessage.value = 'Nao foi possivel sincronizar Investor Relations, Quant Engine e LEX com o backend agora.'
  } finally {
    isLoading.value = false
  }
}

async function rebalancePortfolio() {
  isRebalancing.value = true
  rebalanceFeedback.value = ''

  try {
    const snapshot = quantDashboardPayload.value || {}
    const portfolio = (snapshot.allocations || []).map((allocation) => ({
      project_id: allocation.project_id,
      risk: Number(allocation.risk || 0.4),
      roi: Number(allocation.score || 0) * 10,
    }))

    if (!portfolio.length) {
      rebalanceFeedback.value = 'Sem ativos para rebalancear no momento.'
      return
    }

    const { data } = await runQuantRebalance(portfolio)
    const result = normalizeProxyResult(data)
    const actions = result.actions || []
    rebalanceFeedback.value = `Rebalanceamento executado: ${actions.length} acoes geradas.`

    await loadInvestorRelationsData()
  } catch (_error) {
    rebalanceFeedback.value = 'Falha ao executar rebalanceamento no Quant Engine.'
  } finally {
    isRebalancing.value = false
  }
}

async function openOpportunity(item) {
  selectedOpportunity.value = item
  tradeFeedback.value = ''

  const assets = lexDashboardPayload.value.assets || []
  const matchedAsset = assets.find((asset) => asset.project_id === item.projectId)
  const fallbackAsset = assets[0]
  selectedAssetId.value = matchedAsset?.id || fallbackAsset?.id || ''

  const basePrice = Number(matchedAsset?.price_per_share || 100)
  tradeForm.value.price = Math.max(1, Number(basePrice.toFixed(2)))

  try {
    selectedFairPayload.value = await loadLexFairPrice(item.expectedReturn, mapRiskToNumber(item.riskLevel), 65)
  } catch (_error) {
    selectedFairPayload.value = { fair_price: 0, market_price: 0, john_recommendation: 'manter' }
  }
}

function closeOpportunityModal() {
  selectedOpportunity.value = null
}

async function submitLexOrder() {
  if (!selectedAssetId.value) {
    tradeFeedback.value = 'Nenhum ativo tokenizado disponivel para esta oportunidade.'
    return
  }

  isTrading.value = true
  tradeFeedback.value = ''

  try {
    await approveLexKyc(tradeForm.value.investorId)

    if (tradeForm.value.side === 'buy' && Number(tradeForm.value.cashDeposit || 0) > 0) {
      await depositLexCash({
        investor_id: tradeForm.value.investorId,
        amount: Number(tradeForm.value.cashDeposit || 0),
      })
    }

    if (tradeForm.value.side === 'sell' && Number(tradeForm.value.inventoryQuantity || 0) > 0) {
      await grantLexInventory({
        investor_id: tradeForm.value.investorId,
        asset_id: selectedAssetId.value,
        quantity: Number(tradeForm.value.inventoryQuantity || 0),
        avg_price: Number(tradeForm.value.price || 0),
      })
    }

    await createLexOrder({
      investor_id: tradeForm.value.investorId,
      asset_id: selectedAssetId.value,
      side: tradeForm.value.side,
      price: Number(tradeForm.value.price || 0),
      quantity: Number(tradeForm.value.quantity || 0),
      order_type: tradeForm.value.orderType,
      stop_price: Number(tradeForm.value.stopPrice || 0),
      visible_quantity: Number(tradeForm.value.visibleQuantity || 0),
    })
    tradeFeedback.value = 'Ordem enviada com sucesso no book do LEX.'
    await loadInvestorRelationsData()
  } catch (_error) {
    tradeFeedback.value = 'Falha ao enviar ordem para o LEX.'
  } finally {
    isTrading.value = false
  }
}

async function executeLexMatching() {
  if (!selectedAssetId.value) {
    tradeFeedback.value = 'Selecione uma oportunidade com ativo tokenizado para executar matching.'
    return
  }

  isTrading.value = true
  tradeFeedback.value = ''

  try {
    const { data } = await runLexMatching(selectedAssetId.value)
    const result = normalizeProxyResult(data)
    tradeFeedback.value = `Matching executado: ${result.count || 0} trade(s).`
    await loadInvestorRelationsData()
  } catch (_error) {
    tradeFeedback.value = 'Falha ao executar matching no LEX.'
  } finally {
    isTrading.value = false
  }
}

async function runLexSetupFlow() {
  if (!selectedAssetId.value) {
    tradeFeedback.value = 'Selecione uma oportunidade com ativo tokenizado para preparar o clearing.'
    return
  }

  isTrading.value = true
  tradeFeedback.value = ''

  try {
    await approveLexKyc(tradeForm.value.investorId)
    await depositLexCash({
      investor_id: tradeForm.value.investorId,
      amount: Number(tradeForm.value.cashDeposit || 0),
    })
    await grantLexInventory({
      investor_id: tradeForm.value.investorId,
      asset_id: selectedAssetId.value,
      quantity: Number(tradeForm.value.inventoryQuantity || 0),
      avg_price: Number(tradeForm.value.price || 0),
    })
    tradeFeedback.value = 'Clearing preparado: KYC, caixa e inventario atualizados.'
    await loadInvestorRelationsData()
  } catch (_error) {
    tradeFeedback.value = 'Falha ao preparar clearing para operacao.'
  } finally {
    isTrading.value = false
  }
}

async function loadLexMarketData() {
  if (!selectedAssetId.value) return

  try {
    const [quoteResponse, indicesResponse, fundsResponse, johnResponse] = await Promise.all([
      getLexMarketMakerQuote(selectedAssetId.value, Number(tradeForm.value.mmConfidence || 0.65)),
      recalculateLexIndices(),
      getLexFunds(),
      getLexJohnMarketBrief('LEX-INFRA'),
    ])

    marketMakerPayload.value = {
      bid: 0,
      ask: 0,
      spread: 0,
      depth: 0,
      ...normalizeProxyResult(quoteResponse.data),
    }
    lexIndicesPayload.value = {
      indices: [],
      ...normalizeProxyResult(indicesResponse.data),
    }
    lexFundsPayload.value = {
      funds: [],
      ...normalizeProxyResult(fundsResponse.data),
    }
    johnMarketBrief.value = normalizeProxyResult(johnResponse.data).brief || 'Sem briefing no momento.'
  } catch (_error) {
    // Mantem silencioso para nao bloquear fluxo principal de operacao.
  }
}

async function subscribeDefaultFund() {
  isTrading.value = true
  tradeFeedback.value = ''

  try {
    await approveLexKyc(tradeForm.value.investorId)
    await depositLexCash({
      investor_id: tradeForm.value.investorId,
      amount: Number(tradeForm.value.fundSubscriptionAmount || 0),
    })

    if (!(lexFundsPayload.value.funds || []).length) {
      await loadLexMarketData()
    }

    const firstFund = (lexFundsPayload.value.funds || [])[0]
    if (!firstFund) {
      tradeFeedback.value = 'Nenhum fundo disponivel para subscricao.'
      return
    }

    await subscribeLexFund({
      fund_id: firstFund.id,
      investor_id: tradeForm.value.investorId,
      amount: Number(tradeForm.value.fundSubscriptionAmount || 0),
    })

    tradeFeedback.value = `Subscricao concluida no fundo ${firstFund.name}.`
    await loadInvestorRelationsData()
  } catch (_error) {
    tradeFeedback.value = 'Falha ao subscrever fundo no LEX.'
  } finally {
    isTrading.value = false
  }
}

async function runExecutiveLexDemoFlow() {
  isTrading.value = true
  tradeFeedback.value = ''

  try {
    const assets = lexDashboardPayload.value.assets || []
    const fallbackAssetId = selectedAssetId.value || assets[0]?.id
    if (!fallbackAssetId) {
      tradeFeedback.value = 'Sem ativo tokenizado para executar a demo executiva.'
      return
    }

    selectedAssetId.value = fallbackAssetId
    const buyerId = 'INVESTOR_DEMO_BUYER'
    const sellerId = 'INVESTOR_DEMO_SELLER'
    const tradePrice = Number(tradeForm.value.price || 100)
    const tradeQty = Math.max(1, Number(tradeForm.value.quantity || 100))
    const depositAmount = Math.max(1000, tradePrice * tradeQty * 1.3)

    await Promise.all([approveLexKyc(buyerId), approveLexKyc(sellerId)])

    await depositLexCash({
      investor_id: buyerId,
      amount: depositAmount,
    })

    await grantLexInventory({
      investor_id: sellerId,
      asset_id: selectedAssetId.value,
      quantity: tradeQty,
      avg_price: tradePrice,
    })

    await createLexOrder({
      investor_id: buyerId,
      asset_id: selectedAssetId.value,
      side: 'buy',
      price: tradePrice,
      quantity: tradeQty,
      order_type: 'limit',
      stop_price: 0,
      visible_quantity: 0,
    })

    await createLexOrder({
      investor_id: sellerId,
      asset_id: selectedAssetId.value,
      side: 'sell',
      price: tradePrice,
      quantity: tradeQty,
      order_type: 'limit',
      stop_price: 0,
      visible_quantity: 0,
    })

    const matching = await runLexMatching(selectedAssetId.value)
    const matchingResult = normalizeProxyResult(matching.data)

    if (!(lexFundsPayload.value.funds || []).length) {
      await loadLexMarketData()
    }

    const firstFund = (lexFundsPayload.value.funds || [])[0]
    if (firstFund) {
      await depositLexCash({
        investor_id: buyerId,
        amount: 5000,
      })
      await subscribeLexFund({
        fund_id: firstFund.id,
        investor_id: buyerId,
        amount: 5000,
      })
    }

    await loadLexMarketData()
    await loadInvestorRelationsData()

    tradeFeedback.value = `Demo executiva concluida: ${matchingResult.count || 0} trade(s) liquidados e subscricao de fundo processada.`
  } catch (_error) {
    tradeFeedback.value = 'Falha ao executar demo executiva 1 clique do LEX.'
  } finally {
    isTrading.value = false
  }
}

async function cleanupDemoResidualOrders(assetId, demoInvestorIds = []) {
  const { data } = await getLexDashboard()
  const snapshot = normalizeProxyResult(data)
  const openOrders = (snapshot.order_book || []).filter(
    (item) => item.asset_id === assetId && demoInvestorIds.includes(item.investor_id)
  )

  for (const order of openOrders) {
    if (!order.quantity || Number(order.quantity) <= 0) continue

    const hedgeInvestor = order.investor_id === DEMO_SAFE_BUYER_ID ? DEMO_SAFE_SELLER_ID : DEMO_SAFE_BUYER_ID
    if (order.type === 'buy') {
      await grantLexInventory({
        investor_id: hedgeInvestor,
        asset_id: assetId,
        quantity: Number(order.quantity),
        avg_price: Number(order.price || 100),
      })
    } else {
      await depositLexCash({
        investor_id: hedgeInvestor,
        amount: Math.max(500, Number(order.price || 100) * Number(order.quantity || 0) * 1.2),
      })
    }

    await createLexOrder({
      investor_id: hedgeInvestor,
      asset_id: assetId,
      side: order.type === 'buy' ? 'sell' : 'buy',
      price: Number(order.price || 100),
      quantity: Number(order.quantity || 0),
      order_type: 'limit',
      stop_price: 0,
      visible_quantity: 0,
    })
  }

  if (openOrders.length) {
    await runLexMatching(assetId)
  }

  return openOrders.length
}

async function runSafeLexDemoFlow() {
  isSafeDemoRunning.value = true
  isTrading.value = true
  tradeFeedback.value = ''

  try {
    const assets = lexDashboardPayload.value.assets || []
    const fallbackAssetId = selectedAssetId.value || assets[0]?.id
    if (!fallbackAssetId) {
      tradeFeedback.value = 'Sem ativo tokenizado para executar a demo segura.'
      return
    }

    selectedAssetId.value = fallbackAssetId
    const safePrice = 100
    const safeQty = 10
    const safeDeposit = 2000

    await Promise.all([approveLexKyc(DEMO_SAFE_BUYER_ID), approveLexKyc(DEMO_SAFE_SELLER_ID)])

    await depositLexCash({ investor_id: DEMO_SAFE_BUYER_ID, amount: safeDeposit })
    await grantLexInventory({
      investor_id: DEMO_SAFE_SELLER_ID,
      asset_id: selectedAssetId.value,
      quantity: safeQty,
      avg_price: safePrice,
    })

    await createLexOrder({
      investor_id: DEMO_SAFE_BUYER_ID,
      asset_id: selectedAssetId.value,
      side: 'buy',
      price: safePrice,
      quantity: safeQty,
      order_type: 'limit',
      stop_price: 0,
      visible_quantity: 0,
    })

    await createLexOrder({
      investor_id: DEMO_SAFE_SELLER_ID,
      asset_id: selectedAssetId.value,
      side: 'sell',
      price: safePrice,
      quantity: safeQty,
      order_type: 'limit',
      stop_price: 0,
      visible_quantity: 0,
    })

    const matching = await runLexMatching(selectedAssetId.value)
    const matchingResult = normalizeProxyResult(matching.data)
    const cleanedOrders = await cleanupDemoResidualOrders(selectedAssetId.value, [DEMO_SAFE_BUYER_ID, DEMO_SAFE_SELLER_ID])

    await loadLexMarketData()
    await loadInvestorRelationsData()

    tradeFeedback.value = `Demo segura concluida: ${matchingResult.count || 0} trade(s), limpeza de ${cleanedOrders} ordem(ns) residual(is).`
  } catch (_error) {
    tradeFeedback.value = 'Falha ao executar demo segura do LEX.'
  } finally {
    isSafeDemoRunning.value = false
    isTrading.value = false
  }
}

onMounted(loadInvestorRelationsData)
</script>

<style scoped>
.portal-page {
  min-height: 100vh;
  padding: 32px 5%;
  background: linear-gradient(180deg, #f8fafc, #eef4fb);
}

.page-header {
  max-width: 860px;
  display: grid;
  gap: 10px;
  margin-bottom: 24px;
}

.back-btn {
  width: fit-content;
  border: none;
  background: transparent;
  color: #133a5e;
  font-weight: 800;
  cursor: pointer;
}

.eyebrow {
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: #c53030;
}

h1 {
  font-size: clamp(2rem, 4vw, 3rem);
  color: #133a5e;
}

.page-header p {
  color: #516173;
  max-width: 720px;
}

.status {
  margin-bottom: 18px;
  font-weight: 700;
}

.status-loading {
  color: #133a5e;
}

.status-error {
  color: #c53030;
}

.stats-grid,
.content-grid {
  display: grid;
  gap: 16px;
}

.stats-grid {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  margin-bottom: 22px;
}

.stat-card,
.panel-card {
  background: white;
  border-radius: 18px;
  border: 1px solid #dbe4ee;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);
}

.stat-card {
  padding: 18px;
  display: grid;
  gap: 6px;
}

.stat-card strong {
  font-size: 1.6rem;
  color: #133a5e;
}

.stat-card span,
.panel-card p {
  color: #64748b;
}

.content-grid {
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}

.quant-panel {
  background: #ffffff;
  border: 1px solid #dbe4ee;
  border-radius: 18px;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);
  padding: 20px;
  margin-bottom: 22px;
  display: grid;
  gap: 8px;
}

.quant-panel h2 {
  color: #133a5e;
}

.quant-panel p {
  color: #64748b;
}

.lex-panel {
  background: #ffffff;
  border: 1px solid #dbe4ee;
  border-radius: 18px;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.06);
  padding: 20px;
  margin-bottom: 22px;
  display: grid;
  gap: 8px;
}

.lex-panel h2 {
  color: #133a5e;
}

.lex-panel p {
  color: #64748b;
}

.lex-fair-box {
  margin-top: 8px;
  padding: 10px;
  border-radius: 10px;
  background: #f8fafc;
  border: 1px solid #dbe4ee;
  display: grid;
  gap: 4px;
}

.lex-fair-box strong {
  color: #133a5e;
}

.lex-fair-box span,
.lex-fair-box small {
  color: #475569;
}

.quant-actions {
  margin-top: 8px;
  display: grid;
  gap: 8px;
}

.rebalance-feedback {
  font-size: 0.9rem;
  color: #334155;
}

.panel-card {
  padding: 20px;
  display: grid;
  gap: 10px;
}

.panel-card h2 {
  color: #133a5e;
}

.action-btn {
  width: fit-content;
  border: none;
  border-radius: 12px;
  padding: 10px 14px;
  background: #133a5e;
  color: white;
  font-weight: 800;
  cursor: pointer;
}

.opportunity-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: grid;
  place-items: center;
  padding: 16px;
  z-index: 20;
}

.opportunity-modal {
  width: min(760px, 100%);
  max-height: 90vh;
  overflow: auto;
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #dbe4ee;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.22);
  padding: 20px;
  display: grid;
  gap: 14px;
}

.opportunity-modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-head-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.presentation-badge {
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: #ffffff;
  background: #0f766e;
  border-radius: 999px;
  padding: 6px 10px;
}

.modal-close {
  border: none;
  border-radius: 10px;
  background: #0f172a;
  color: #ffffff;
  padding: 8px 12px;
  cursor: pointer;
  font-weight: 700;
}

.modal-grid {
  display: grid;
  gap: 6px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.modal-grid p,
.modal-block p,
.rebalance-list {
  color: #475569;
}

.modal-block {
  border-top: 1px solid #e2e8f0;
  padding-top: 10px;
  display: grid;
  gap: 6px;
}

.modal-block h3 {
  color: #133a5e;
}

.presentation-lock-note {
  color: #0f766e;
  font-size: 0.88rem;
  font-weight: 700;
}

.rebalance-list {
  padding-left: 18px;
  display: grid;
  gap: 4px;
}

.trade-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 10px;
}

.trade-grid-secondary {
  margin-top: 8px;
}

.trade-grid label {
  display: grid;
  gap: 4px;
  color: #334155;
  font-size: 0.9rem;
}

.trade-grid input,
.trade-grid select {
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 8px;
}

.trade-actions {
  margin-top: 10px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.action-btn.ghost {
  background: #334155;
}

.action-btn.executive {
  background: #065f46;
}

.action-btn.safe {
  background: #0f766e;
}

.trade-feedback {
  margin-top: 8px;
  color: #334155;
  font-size: 0.9rem;
}

.lex-insights-grid {
  margin-top: 12px;
  display: grid;
  gap: 10px;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.lex-insight-card {
  border: 1px solid #dbe4ee;
  border-radius: 10px;
  padding: 10px;
  background: #f8fafc;
  display: grid;
  gap: 4px;
}

.lex-insight-card strong {
  color: #133a5e;
}

.lex-insight-card p,
.lex-insight-card small {
  color: #475569;
}
</style>
