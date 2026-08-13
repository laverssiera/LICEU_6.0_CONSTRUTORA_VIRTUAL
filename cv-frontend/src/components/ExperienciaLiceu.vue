<template>
  <div class="liceu-os bg-[#fdfcfb] min-h-screen pb-32 selection:bg-[#c53030] selection:text-white">
    
    <!-- DASHBOARD SUPERIOR: INTELIGÊNCIA 3C273 CEFEIDA -->
    <section class="max-w-[1600px] mx-auto px-10 pt-20 grid lg:grid-cols-2 gap-12 mb-24">
      
      <!-- VISÃO CLIENTE: REALIDADE AUMENTADA (ESTILO DUBAI) -->
      <div class="bg-[#4a4542] p-12 text-[#fdfcfb] shadow-[0_40px_100px_rgba(0,0,0,0.2)] border-t-4 border-[#c53030]">
        <div class="flex justify-between items-start mb-8">
          <div>
            <span class="text-[#c53030] font-bold tracking-[0.4em] text-[10px] uppercase">Monólito 01 / Cefeida</span>
            <h3 class="text-4xl font-serif mt-2 italic tracking-tighter">Imersão <span class="font-sans not-italic font-black text-white/20">RA</span></h3>
          </div>
          <div class="border border-[#fdfcfb]/20 px-4 py-1 text-[9px] font-bold tracking-[0.2em] uppercase">Status: Live 📡</div>
        </div>
        
        <model-viewer 
          :src="modeloUrl" 
          ar ar-modes="webxr scene-viewer quick-look" 
          camera-controls 
          shadow-intensity="2"
          class="w-full h-80 bg-black/10 mb-8 border border-white/5">
          <button slot="ar-button" class="btn-liceu-primary w-full bg-[#fdfcfb] text-[#4a4542] hover:bg-[#c53030] hover:text-white">
            Iniciar Experiência 1:1
          </button>
        </model-viewer>

        <!-- LINK PARA INSTITUCIONAL -->
        <router-link to="/monolito/cefeida" class="text-[9px] uppercase font-bold tracking-[0.4em] opacity-40 hover:opacity-100 hover:text-[#c53030] transition-all no-underline">
          Arquitetura de Dados Cefeida ➔
        </router-link>
      </div>

      <!-- VISÃO DIRETOR: LEADS REESTRUTURADOS -->
      <div class="operation-card flex flex-col justify-between">
        <div>
          <div class="flex justify-between items-center mb-10 border-b border-slate-100 pb-6">
            <h3 class="text-[#4a4542] font-serif text-2xl italic tracking-tight">
              Leads <span class="font-sans not-italic font-black text-[#c53030] uppercase text-sm tracking-[0.3em]">Qualificados</span>
            </h3>
            <span class="text-[10px] font-bold text-slate-400 tracking-widest uppercase">Base: {{ leads.length }}</span>
          </div>

          <div class="space-y-6 max-h-[320px] overflow-y-auto pr-4 custom-scroll">
            <div v-for="lead in leads" :key="lead.id" class="group flex justify-between items-center py-4 border-b border-slate-50 hover:bg-slate-50/50 transition-all px-2">
              <div class="flex items-center gap-6">
                <div class="w-1 bg-[#4a4542] group-hover:bg-[#c53030] h-8 transition-all"></div>
                <div>
                  <p class="font-bold text-[#4a4542] text-xs tracking-wider uppercase">{{ lead.email }}</p>
                  <p class="text-[9px] text-slate-400 font-medium tracking-[0.2em] uppercase mt-1">Interesse: {{ lead.interesse }}</p>
                </div>
              </div>
              <div class="text-right">
                <div :class="lead.score > 80 ? 'text-[#c53030]' : 'text-slate-400'" class="text-[10px] font-black italic tracking-widest">
                  SCORE: {{ lead.score }}%
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- NAVEGAÇÃO VIA DASHBOARD -->
        <router-link to="/monolito/cefeida" class="btn-liceu-outline mt-10 text-center no-underline">
          Acessar Relatório Pericial
        </router-link>
      </div>
    </section>

    <!-- GRID DOS 14 MONÓLITOS: ESTRUTURA DE PODER -->
    <main class="max-w-[1600px] mx-auto px-10">
      <h2 class="font-serif text-3xl italic mb-16 text-[#4a4542]">Arquitetura de <span class="font-sans not-italic font-black uppercase text-[#c53030] text-sm tracking-[0.5em]">Monólitos</span></h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-x-12 gap-y-20">
        <div v-for="m in monolitos" :key="m.id" class="group relative">
          <div class="absolute -top-6 left-0 text-3xl grayscale group-hover:grayscale-0 transition-all duration-700 opacity-20 group-hover:opacity-100">{{ m.icon }}</div>
          
          <div class="pt-8 border-t border-slate-200 group-hover:border-[#c53030] transition-all duration-1000">
            <h3 class="font-serif text-xl font-bold text-[#4a4542] group-hover:italic transition-all">{{ m.nome }}</h3>
            <p class="text-[10px] text-slate-400 font-medium uppercase tracking-[0.2em] mt-3 leading-relaxed min-h-[40px]">
              {{ m.desc }}
            </p>
          </div>
          
          <!-- NAVEGAÇÃO CIRÚRGICA NOS CARDS -->
          <div class="mt-8">
            <router-link 
              v-if="m.id === 'cefeida'" 
              to="/monolito/cefeida" 
              class="btn-liceu-primary block text-center w-full no-underline"
            >
              Conhecer Área
            </router-link>

            <button 
              v-else 
              @click="alert('Monólito ' + m.nome + ' em fase de implantação técnica.')"
              class="btn-liceu-outline w-full"
            >
              Em Breve
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const modeloUrl = ref('https://liceu.io')

const leads = ref([
  { id: 1, email: 'diretoria@liceu.io', interesse: 'Reestruturação', score: 98 },
  { id: 2, email: 'ceo@global_assets.com', interesse: 'Smart Capital', score: 89 },
  { id: 3, email: 'eng@projeto_x.com', interesse: 'Robótica BIM', score: 74 }
])

const monolitos = [
  { id: 'cefeida', nome: '3C273 CEFEIDA', icon: '🧠', desc: 'Mineração de Dados & Planejamento Estratégico.' },
  { id: 'archimedes', nome: 'ARCHIMEDES', icon: '📐', desc: 'Gestão de Ativos Reais & Viabilidade de Terrenos.' },
  { id: 'cea', nome: 'CEA INVEST.', icon: '📈', desc: 'Gestão de Capital & Giro de Obras Industrializadas.' },
  { id: 'gtamkt', nome: 'GTAMKT', icon: '🎮', desc: 'Marketing Gameificado & Experiência Imersiva.' },
  { id: 'bim', nome: 'BIM.ARQU.ENG', icon: '🤖', desc: 'Engenharia de Precisão, Robótica & Manufatura.' },
  { id: 'cdvirtual', nome: 'CDVIRTUAL', icon: '📦', desc: 'Logística Just-in-Time & Cadeia de Suprimentos.' },
  { id: 'erp', nome: 'ERPFORNECEDORES', icon: '⚙️', desc: 'Gestão Administrativa de Parceiros Homologados.' },
  { id: 'pd-ia', nome: 'P&D.IA', icon: '🔬', desc: 'Pesquisa Acadêmica & IA aplicada ao PCP.' }
]
</script>

<style scoped>
/* Estilos que o main.css não cobre ou variáveis de componentes externos */
model-viewer {
  --progress-bar-color: #c53030;
  --ar-button-display: none;
}
.custom-scroll::-webkit-scrollbar { width: 2px; }
.custom-scroll::-webkit-scrollbar-thumb { background: #c53030; }
</style>
