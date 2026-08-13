<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import ConfiguradorGame from '@/components/ConfiguradorGame.vue'
import FormularioTerreno from '@/components/FormularioTerreno.vue'
import LiceuAppCTA from '@/components/LiceuAppCTA.vue'
import { createJourneyQr } from '@/services/api'

const router = useRouter()
const journeyStarted = ref(false)
const isGeneratingQr = ref(false)
const qrJourney = ref({
  url: 'https://liceu.app/download?token=jornada-demo',
  play_store_url: 'https://play.google.com/store/apps/details?id=br.liceu.app',
  app_store_url: 'https://apps.apple.com/br/app/liceu-6-0/id6740000000'
})

const terrainOffers = [
  { title: 'Terrenos premium', text: 'Lotes com leitura urbanística e potencial de valorização acompanhados pelo Archimedes.', path: '/archimedes', cta: 'Abrir Archimedes' },
  { title: 'Investidores ativos', text: 'Capital inteligente pronto para impulsionar a jornada com confiança e governança.', path: '/investidores', cta: 'Ver investidores' },
  { title: 'Viabilidade assistida', text: 'John e CORE.OS transformam intenção em decisão, sem perda de contexto.', path: '/dados', cta: 'Explorar dados' }
]

const portalLinks = [
  { title: 'Archimedes', text: 'Terrenos, viabilidade e leitura patrimonial.', path: '/archimedes', cta: 'Entrar' },
  { title: 'Investidores', text: 'Capital inteligente e oportunidades da jornada.', path: '/investidores', cta: 'Abrir página' },
  { title: 'Dados', text: 'Inteligência, sinais e visão do Cefeida.', path: '/dados', cta: 'Ver insights' },
  { title: 'Jurídico', text: 'Compliance, contratos e segurança da operação.', path: '/juridico', cta: 'Abrir jurídico' },
  { title: 'Academia', text: 'Treinamento e capacitação da irmandade montadora.', path: '/escola', cta: 'Acessar escola' },
  { title: 'Obras', text: 'Status e acompanhamento da produção em campo.', path: '/obras', cta: 'Ver obras' }
]

const testimonials = [
  { name: 'Ana Souza', role: 'Cliente', text: 'Comecei no site, escaneei o QR e continuei toda a jornada no app sem repetir nenhuma etapa.' },
  { name: 'Carlos Menezes', role: 'Investidor', text: 'Acompanhei a aprovação de viabilidade e os marcos da obra em tempo real.' },
  { name: 'Fernanda Rocha', role: 'Parceira de obra', text: 'O John acelerou a entrada no fluxo e o acompanhamento ficou muito mais claro.' }
]

async function generateJourneyQr(origin = 'site-home') {
  if (isGeneratingQr.value) return

  isGeneratingQr.value = true
  try {
    const { data } = await createJourneyQr({
      user_id: 'cliente_demo',
      portal: 'archimedes',
      journey_context: {
        source: origin,
        current_page: typeof window !== 'undefined' ? window.location.pathname : '/',
        stage: 'site-fachada'
      }
    })
    qrJourney.value = data
  } catch (error) {
    qrJourney.value = {
      url: 'https://liceu.app/download?token=jornada-demo',
      play_store_url: 'https://play.google.com/store/apps/details?id=br.liceu.app',
      app_store_url: 'https://apps.apple.com/br/app/liceu-6-0/id6740000000'
    }
  } finally {
    isGeneratingQr.value = false
  }
}

async function startJourney(origin = 'hero') {
  journeyStarted.value = true
  if (typeof window !== 'undefined') {
    window.localStorage.setItem('liceu_jornada_started', '1')
  }
  await generateJourneyQr(origin)
  await nextTick()
  document.getElementById('app-cta')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function openPortal(path) {
  if (!path) return
  router.push(path)
}

function handleJourneyEvent(event) {
  journeyStarted.value = true
  generateJourneyQr(event?.detail?.origin || 'john-concierge')
}

onMounted(() => {
  if (typeof window !== 'undefined') {
    if (window.localStorage.getItem('liceu_jornada_started') === '1') {
      journeyStarted.value = true
      generateJourneyQr('persisted')
    }
    window.addEventListener('liceu:jornada-iniciada', handleJourneyEvent)
  }
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('liceu:jornada-iniciada', handleJourneyEvent)
  }
})
</script>

<template>
  <div class="journey-page">
    <header class="topbar">
      <div>
        <div class="brand-name">LICEU <span>6.0</span></div>
        <div class="brand-tag">CONSTRUTORA VIRTUAL</div>
      </div>

      <nav class="top-nav">
        <a href="#jornada">Jornada</a>
        <a href="#viabilidade">Viabilidade</a>
        <a href="#depoimentos">Depoimentos</a>
        <button class="btn-primary small" @click="startJourney('topbar')">Iniciar com John</button>
      </nav>
    </header>

    <section class="hero-john">
      <div class="hero-copy">
        <span class="eyebrow">HERO JOHN BRASILEIRO</span>
        <h1>Construa sua casa com o John guiando cada etapa da jornada.</h1>
        <p>
          Entre pelo site, monte sua casa, avalie terrenos, valide a viabilidade e continue tudo no app LICEU 6.0 sem perder contexto.
        </p>
        <div class="hero-actions">
          <button class="btn-primary" @click="startJourney('hero')">Começar jornada</button>
          <button class="btn-secondary" @click="router.push('/download')">Ver app</button>
        </div>
      </div>

      <div class="hero-panel">
        <div class="john-avatar">🧠</div>
        <strong>John Brasileiro online</strong>
        <p>Recebe o cliente, organiza a jornada e prepara a continuidade em tempo real no app.</p>
        <ul>
          <li>Montagem gameificada</li>
          <li>Oferta de terrenos e investidores</li>
          <li>Simulação de viabilidade</li>
          <li>Handoff instantâneo para o app</li>
        </ul>
      </div>
    </section>

    <main class="content-shell">
      <section id="jornada" class="section-block">
        <div class="section-heading">
          <span>ETAPA 1</span>
          <h2>Monte sua casa gameificada</h2>
          <p>O cliente começa a jornada com o John e já visualiza a experiência de montagem da casa.</p>
        </div>
        <ConfiguradorGame />
      </section>

      <section class="section-block offers-grid">
        <div class="section-heading">
          <span>ETAPA 2</span>
          <h2>Oferta de terrenos e investidores</h2>
          <p>O John conecta lotes, capital e oportunidade antes da obra começar.</p>
        </div>
        <div class="cards-grid">
          <article v-for="offer in terrainOffers" :key="offer.title" class="info-card">
            <h3>{{ offer.title }}</h3>
            <p>{{ offer.text }}</p>
            <button class="link-btn" @click="openPortal(offer.path)">{{ offer.cta }}</button>
          </article>
        </div>
      </section>

      <section class="section-block">
        <div class="section-heading">
          <span>ETAPA 2.1</span>
          <h2>Outras páginas do site LICEU</h2>
          <p>O cliente também pode navegar diretamente pelos portais do ecossistema no frontend.</p>
        </div>
        <div class="cards-grid">
          <article v-for="page in portalLinks" :key="page.title" class="info-card">
            <h3>{{ page.title }}</h3>
            <p>{{ page.text }}</p>
            <button class="link-btn" @click="openPortal(page.path)">{{ page.cta }}</button>
          </article>
        </div>
      </section>

      <section id="viabilidade" class="section-block viability-layout">
        <div>
          <div class="section-heading left">
            <span>ETAPA 3</span>
            <h2>Simulação de viabilidade</h2>
            <p>Valide o lote, o custo e o potencial da obra com leitura operacional integrada.</p>
          </div>
          <FormularioTerreno />
        </div>

        <aside class="journey-summary-card">
          <h3>Continuidade da jornada</h3>
          <ol>
            <li>Usuário entra no site</li>
            <li>John recebe e orienta</li>
            <li>Casa começa a tomar forma</li>
            <li>QR aparece para continuidade</li>
            <li>App assume a jornada com login automático</li>
          </ol>
        </aside>
      </section>

      <section v-if="journeyStarted" id="app-cta" class="section-block">
        <div class="section-heading">
          <span>ETAPA 4</span>
          <h2>Continue no app depois de iniciar com o John</h2>
          <p>
            {{ isGeneratingQr ? 'Preparando seu QR inteligente...' : 'Escaneie, faça login automático e acompanhe tudo em tempo real.' }}
          </p>
        </div>
        <LiceuAppCTA
          :download-url="qrJourney.url"
          :play-store-url="qrJourney.play_store_url"
          :app-store-url="qrJourney.app_store_url"
        />
      </section>

      <section id="depoimentos" class="section-block">
        <div class="section-heading">
          <span>ETAPA 5</span>
          <h2>Depoimentos</h2>
          <p>Clientes e parceiros continuam a jornada entre site e app com fluidez.</p>
        </div>
        <div class="cards-grid">
          <article v-for="item in testimonials" :key="item.name" class="testimonial-card">
            <p>“{{ item.text }}”</p>
            <strong>{{ item.name }}</strong>
            <small>{{ item.role }}</small>
          </article>
        </div>
      </section>

      <section class="final-cta">
        <div>
          <span class="eyebrow">CTA FINAL</span>
          <h2>Entre no fluxo LICEU 6.0 e acompanhe sua casa até a entrega.</h2>
        </div>
        <div class="hero-actions">
          <button class="btn-primary" @click="startJourney('final-cta')">Continuar com John</button>
          <button class="btn-secondary" @click="router.push('/obras')">Acompanhar obra</button>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.journey-page {
  min-height: 100vh;
  background: #f8fafc;
  color: #0f172a;
}

.topbar {
  position: sticky;
  top: 0;
  z-index: 30;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 16px 5%;
  background: rgba(255, 255, 255, 0.95);
  border-bottom: 1px solid #dbe4ee;
  backdrop-filter: blur(10px);
}

.brand-name {
  font-size: 1.5rem;
  font-weight: 900;
  color: #133a5e;
}

.brand-name span {
  color: #c53030;
}

.brand-tag {
  font-size: 0.7rem;
  letter-spacing: 0.12em;
  color: #64748b;
}

.top-nav {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.top-nav a {
  color: #133a5e;
  text-decoration: none;
  font-weight: 700;
}

.hero-john {
  display: grid;
  grid-template-columns: 1.3fr 0.9fr;
  gap: 24px;
  padding: 48px 5%;
  background: linear-gradient(135deg, #0f172a, #133a5e 55%, #1d4ed8);
  color: white;
}

.eyebrow {
  display: inline-block;
  margin-bottom: 12px;
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  color: #fca5a5;
}

.hero-copy h1 {
  font-size: clamp(2.2rem, 5vw, 3.4rem);
  line-height: 1.05;
  margin-bottom: 12px;
}

.hero-copy p {
  max-width: 720px;
  color: #d7e4f3;
  margin-bottom: 20px;
}

.hero-panel {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.25);
}

.john-avatar {
  font-size: 3rem;
  margin-bottom: 10px;
}

.hero-panel ul {
  margin-top: 12px;
  padding-left: 18px;
  color: #e2e8f0;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.btn-primary,
.btn-secondary {
  border: none;
  border-radius: 14px;
  padding: 12px 18px;
  cursor: pointer;
  font-weight: 800;
}

.btn-primary {
  background: #c53030;
  color: white;
}

.btn-primary.small {
  padding: 10px 14px;
}

.btn-secondary {
  background: white;
  color: #133a5e;
}

.content-shell {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 16px 64px;
}

.section-block {
  display: grid;
  gap: 18px;
  margin-bottom: 32px;
}

.section-heading span {
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: #c53030;
}

.section-heading h2 {
  font-size: clamp(1.7rem, 3vw, 2.3rem);
  color: #133a5e;
}

.section-heading p {
  color: #64748b;
  max-width: 700px;
}

.offers-grid,
.cards-grid {
  display: grid;
  gap: 16px;
}

.cards-grid {
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.info-card,
.testimonial-card,
.journey-summary-card {
  background: white;
  border: 1px solid #dbe4ee;
  border-radius: 18px;
  padding: 20px;
  box-shadow: 0 10px 25px rgba(15, 23, 42, 0.06);
}

.info-card h3,
.journey-summary-card h3 {
  color: #133a5e;
  margin-bottom: 8px;
}

.info-card p,
.testimonial-card p,
.journey-summary-card ol {
  color: #516173;
}

.link-btn {
  margin-top: 12px;
  width: fit-content;
  border: none;
  border-radius: 12px;
  padding: 10px 14px;
  background: #133a5e;
  color: white;
  font-weight: 800;
  cursor: pointer;
}

.link-btn:hover {
  background: #c53030;
}

.viability-layout {
  grid-template-columns: 1.2fr 0.8fr;
  align-items: start;
}

.journey-summary-card ol {
  padding-left: 18px;
  display: grid;
  gap: 8px;
}

.testimonial-card strong {
  display: block;
  margin-top: 14px;
  color: #133a5e;
}

.testimonial-card small {
  color: #64748b;
}

.final-cta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  padding: 24px;
  border-radius: 24px;
  background: linear-gradient(135deg, #133a5e, #1d4ed8);
  color: white;
}

.final-cta h2 {
  max-width: 720px;
}

@media (max-width: 900px) {
  .hero-john,
  .viability-layout,
  .final-cta,
  .topbar {
    grid-template-columns: 1fr;
    flex-direction: column;
    align-items: flex-start;
  }

  .top-nav {
    width: 100%;
  }
}
</style>