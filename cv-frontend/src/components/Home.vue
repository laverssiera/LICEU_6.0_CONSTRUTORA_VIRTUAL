<template>
  <div class="liceu-os">
    <header class="main-header">
      <div class="nav-container">
        <div class="logo-text-box" @click="$router.push('/')">
          <div class="brand-name">LICEU <span class="v6">6.0</span></div>
          <div class="brand-tag">CONSTRUTORA VIRTUAL</div>
        </div>

        <nav class="market-nav">
          <div v-for="item in menuMercados" :key="item.label" class="nav-item">
            <div class="nav-link">
              <span class="nav-icon-retro">{{ item.icon }}</span>
              <div class="nav-text">
                <span class="nav-label-main">{{ item.label }}</span>
                <span class="nav-label-sub">{{ item.sub[0].title }}</span>
              </div>
            </div>
          </div>
        </nav>

        <div class="auth-nav">
          <button class="btn-head">📞 BUSINESS</button>
          <button class="btn-head">📹 LIVE</button>
          <button class="btn-head">NOSSO DNA</button>
          <button class="btn-head" @click="$router.push('/institucional')">🏛️ INSTITUCIONAL</button>
          <button class="btn-connect" @click="$router.push('/archimedes')">ARCHIMEDES</button>
        </div>
      </div>
    </header>

    <section class="hero-main">
      <div class="hero-copy">
        <span class="hero-eyebrow">PLATAFORMA PRINCIPAL LICEU 6.0</span>
        <h1>Construção, capital e inteligência conectados em um só ecossistema.</h1>
        <p>
          Esta é a página principal institucional da LICEU 6.0. Quando o cliente pedir ao John para ver imóveis ou clicar em Archimedes, a navegação segue para a experiência específica de terrenos, patrimônio e viabilidade.
        </p>

        <div class="hero-actions">
          <button class="btn-connect hero-btn" @click="$router.push('/archimedes')">Ver imóveis com John</button>
          <button class="btn-head hero-btn" @click="$router.push('/investidores')">Área investidores</button>
          <button class="btn-head hero-btn" @click="$router.push('/obras')">Acompanhar obras</button>
        </div>

        <div class="hero-metrics">
          <div v-for="metric in metrics" :key="metric.label" class="metric-pill">
            <strong>{{ metric.value }}</strong>
            <span>{{ metric.label }}</span>
          </div>
        </div>
      </div>

      <aside class="hero-highlight-card">
        <span class="mini-badge">Jornada recomendada</span>
        <h3>Quando entrar no Archimedes</h3>
        <ul>
          <li>quando o cliente pedir ao John para ver imóveis</li>
          <li>quando clicar no botão Archimedes</li>
          <li>quando quiser terrenos e leitura de viabilidade</li>
        </ul>
        <button class="btn-connect full" @click="$router.push('/archimedes')">Abrir experiência Archimedes</button>
      </aside>
    </section>

    <section class="institutional-strip">
      <article v-for="item in highlights" :key="item.title" class="strip-card">
        <strong>{{ item.title }}</strong>
        <p>{{ item.text }}</p>
      </article>
    </section>

    <main class="page-shell">
      <section class="section-block">
        <div class="section-heading">
          <span>ECOSSISTEMA</span>
          <h2>Páginas e áreas da LICEU 6.0</h2>
          <p>Da home institucional, o cliente e os parceiros acessam as áreas especializadas do grupo.</p>
        </div>

        <div class="grid-container">
          <div v-for="m in monolitos" :key="m.id" class="card-monolito">
            <div class="card-header-bar" :style="{ background: m.accent }"></div>
            <div class="card-body">
              <div class="monolito-icon">{{ m.icon }}</div>
              <h3 class="monolito-title">{{ m.nome }}</h3>
              <p class="monolito-desc">{{ m.desc }}</p>
              <button @click="$router.push(m.path)" class="btn-conhecer-link">
                {{ m.cta }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <section class="section-block">
        <div class="section-heading">
          <span>JORNADAS</span>
          <h2>Entradas principais do site</h2>
          <p>Cada público entra por uma jornada adequada, com John atuando como concierge e o Archimedes como portal imobiliário dedicado.</p>
        </div>

        <div class="journey-grid">
          <article v-for="journey in journeys" :key="journey.title" class="journey-card">
            <span class="journey-icon">{{ journey.icon }}</span>
            <h3>{{ journey.title }}</h3>
            <p>{{ journey.text }}</p>
            <button class="link-btn" @click="$router.push(journey.path)">{{ journey.cta }}</button>
          </article>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
const menuMercados = [
  { label: 'BUSINESS', icon: '⧉', sub: [{ title: 'Evolução Digital', desc: 'B2B Scalability' }] },
  { label: 'SMART CAPITAL', icon: '⚖', sub: [{ title: 'Ativos Reais', desc: 'Asset Mgmt' }] },
  { label: 'LIVING', icon: '⌂', sub: [{ title: 'Portfólio', desc: 'Casas e Lotes' }] },
  { label: 'GOVTECH', icon: '🏛', sub: [{ title: 'Smart Tenders', desc: 'Licitações' }] },
  { label: 'IMPACTO', icon: '◈', sub: [{ title: 'Consciência ESG', desc: 'Sustentabilidade' }] }
]

const metrics = [
  { value: '15', label: 'monólitos mapeados' },
  { value: '24h', label: 'leitura operacional' },
  { value: '1 só fluxo', label: 'site + John + app' }
]

const highlights = [
  { title: 'John central', text: 'Recebe, entende a intenção e direciona o cliente para a experiência correta.' },
  { title: 'Archimedes dedicado', text: 'Terrenos, imóveis e viabilidade ficam em uma jornada separada e focada.' },
  { title: 'Tempo real', text: 'O núcleo acompanha eventos e atualiza a experiência de forma contínua.' }
]

const monolitos = [
  { id: 'archimedes', nome: 'ARCHIMEDES', icon: '🏘️', desc: 'Terrenos, imóveis e viabilidade patrimonial.', path: '/archimedes', cta: 'VER IMÓVEIS', accent: 'linear-gradient(90deg, #1a365d, #c53030)' },
  { id: 'investidores', nome: 'CEA INVESTIMENTOS', icon: '💰', desc: 'Capital inteligente e oportunidades da jornada.', path: '/investidores', cta: 'ABRIR INVESTIDORES', accent: '#1a365d' },
  { id: 'cefeida', nome: '3C273 CEFEIDA', icon: '🧠', desc: 'Dados, inteligência e estratégia operacional.', path: '/dados', cta: 'VER DADOS', accent: '#1a365d' },
  { id: 'escola', nome: 'ACADEMIA DO SABER', icon: '🎓', desc: 'Treinamento e qualificação da irmandade.', path: '/escola', cta: 'ENTRAR NA ACADEMIA', accent: '#1a365d' },
  { id: 'obras', nome: 'STATUS DE OBRAS', icon: '🏗️', desc: 'Produção real e acompanhamento de campo.', path: '/obras', cta: 'ACOMPANHAR OBRAS', accent: '#1a365d' }
]

const journeys = [
  { icon: '🏠', title: 'Cliente em busca de imóvel', text: 'Quando o usuário pedir ao John para ver imóveis, a entrada correta é o Archimedes.', path: '/archimedes', cta: 'Ir para Archimedes' },
  { icon: '📈', title: 'Investidor e parceiro', text: 'A área financeira e de oportunidades mantém a visão de capital, crescimento e governança.', path: '/investidores', cta: 'Abrir investidores' },
  { icon: '🏗️', title: 'Acompanhamento da obra', text: 'O cliente também pode acompanhar o andamento do projeto e os marcos operacionais.', path: '/obras', cta: 'Ver obras' }
]
</script>

<style scoped>
.liceu-os {
  min-height: 100vh;
  background: linear-gradient(180deg, #f8fafc 0%, #eef4f9 100%);
  font-family: 'Inter', sans-serif;
}

.main-header {
  background: rgba(255, 255, 255, 0.98);
  border-bottom: 1px solid #d8e2ec;
  padding: 12px 4%;
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(10px);
}

.nav-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  max-width: 1400px;
  margin: 0 auto;
}

.logo-text-box {
  line-height: 1;
  cursor: pointer;
}

.brand-name {
  font-size: 1.7rem;
  font-weight: 900;
  color: #143a5d;
}

.v6 {
  color: #d63a32;
}

.brand-tag {
  font-size: 0.65rem;
  font-weight: 800;
  color: #7a8b9a;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.market-nav {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}

.nav-item {
  padding: 4px 6px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-text {
  display: flex;
  flex-direction: column;
}

.nav-icon-retro {
  font-size: 1rem;
  color: #1a365d;
}

.nav-label-main {
  display: block;
  font-size: 0.56rem;
  font-weight: 900;
  color: #94a3b8;
}

.nav-label-sub {
  display: block;
  font-size: 0.68rem;
  font-weight: 700;
  color: #18324a;
}

.auth-nav {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-head,
.btn-connect,
.btn-conhecer-link,
.link-btn {
  cursor: pointer;
  transition: 0.2s ease;
}

.btn-head {
  border: 1px solid #143a5d;
  padding: 8px 12px;
  font-size: 0.65rem;
  font-weight: 900;
  border-radius: 999px;
  background: #fff;
  color: #143a5d;
}

.btn-connect {
  background: #d63a32;
  color: #fff;
  border: none;
  padding: 8px 14px;
  font-size: 0.68rem;
  font-weight: 900;
  border-radius: 999px;
}

.hero-main {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 24px;
  align-items: stretch;
  padding: 42px 6%;
  background: linear-gradient(135deg, #0e2744, #1e4d92);
  color: white;
}

.hero-copy h1 {
  font-size: clamp(2rem, 4vw, 3.3rem);
  line-height: 1.08;
  margin-bottom: 14px;
}

.hero-copy p {
  max-width: 760px;
  color: rgba(255, 255, 255, 0.88);
  font-size: 1.02rem;
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 28px;
}

.hero-btn {
  padding: 12px 20px;
  font-size: 0.85rem;
}

.hero-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin-top: 28px;
}

.metric-pill {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 12px;
  text-align: center;
}

.metric-pill strong {
  display: block;
  font-size: 1.3rem;
  margin-bottom: 4px;
}

.metric-pill span {
  display: block;
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.7);
}

.hero-highlight-card {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  padding: 24px;
  backdrop-filter: blur(10px);
}

.mini-badge {
  display: inline-block;
  background: rgba(255, 255, 255, 0.15);
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  margin-bottom: 12px;
}

.hero-highlight-card h3 {
  font-size: 1.2rem;
  margin-bottom: 12px;
}

.hero-highlight-card ul {
  list-style: none;
  padding: 0;
  margin: 16px 0;
}

.hero-highlight-card li {
  padding: 8px 0;
  padding-left: 20px;
  position: relative;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.8);
}

.hero-highlight-card li:before {
  content: '→';
  position: absolute;
  left: 0;
}

.btn-connect.full {
  width: 100%;
  margin-top: 16px;
}

.institutional-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  padding: 32px 6%;
  background: rgba(20, 58, 93, 0.05);
}

.strip-card {
  padding: 16px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 8px;
  border-left: 4px solid #d63a32;
}

.strip-card strong {
  display: block;
  color: #143a5d;
  margin-bottom: 8px;
  font-size: 0.92rem;
}

.strip-card p {
  font-size: 0.85rem;
  color: #5a6c7d;
  line-height: 1.5;
}

.page-shell {
  padding: 0;
}

.section-block {
  padding: 48px 6%;
}

.section-block:nth-child(even) {
  background: rgba(20, 58, 93, 0.02);
}

.section-heading {
  margin-bottom: 32px;
}

.section-heading span {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 900;
  color: #7a8b9a;
  text-transform: uppercase;
  margin-bottom: 8px;
  letter-spacing: 0.15em;
}

.section-heading h2 {
  font-size: 2.2rem;
  color: #0e2744;
  margin-bottom: 8px;
}

.section-heading p {
  color: #64748b;
  max-width: 600px;
}

.grid-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
}

.card-monolito {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.card-monolito:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  transform: translateY(-4px);
}

.card-header-bar {
  height: 3px;
  width: 100%;
}

.card-body {
  padding: 20px;
  text-align: center;
}

.monolito-icon {
  font-size: 2.4rem;
  margin-bottom: 12px;
}

.monolito-title {
  font-size: 0.95rem;
  font-weight: 900;
  color: #143a5d;
  margin-bottom: 8px;
}

.monolito-desc {
  font-size: 0.85rem;
  color: #64748b;
  margin-bottom: 16px;
  min-height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-conhecer-link {
  background: #143a5d;
  color: white;
  border: none;
  padding: 8px 14px;
  font-size: 0.7rem;
  font-weight: 700;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-conhecer-link:hover {
  background: #0e2744;
}

.journey-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.journey-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.journey-card:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  transform: translateY(-4px);
  border-color: #d63a32;
}

.journey-icon {
  display: block;
  font-size: 2rem;
  margin-bottom: 12px;
}

.journey-card h3 {
  font-size: 1.05rem;
  color: #143a5d;
  margin-bottom: 8px;
  font-weight: 700;
}

.journey-card p {
  font-size: 0.88rem;
  color: #64748b;
  margin-bottom: 16px;
  line-height: 1.6;
}

.link-btn {
  background: transparent;
  color: #d63a32;
  border: 2px solid #d63a32;
  padding: 6px 14px;
  font-size: 0.75rem;
  font-weight: 700;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.link-btn:hover {
  background: #d63a32;
  color: white;
}

@media (max-width: 768px) {
  .hero-main {
    grid-template-columns: 1fr;
  }

  .section-heading h2 {
    font-size: 1.6rem;
  }

  .hero-actions {
    flex-direction: column;
  }

  .hero-btn {
    width: 100%;
  }
}
</style>
