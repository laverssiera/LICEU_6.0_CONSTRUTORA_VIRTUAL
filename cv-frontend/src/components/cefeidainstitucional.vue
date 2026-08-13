<template>
  <!-- Fundo em Terracota Profundo para passar autoridade -->
  <div class="min-h-screen bg-[#2C1B18] font-sans selection:bg-[#D97757] selection:text-white">
    
    <!-- Header de Navegação Rápida (Estilo Liceu) -->
    <nav class="p-6 flex justify-between items-center border-b border-[#D97757]/20 sticky top-0 bg-[#2C1B18]/90 backdrop-blur-md z-50">
      <button @click="$router.back()" class="text-[#F4EBD0] flex items-center gap-2 hover:opacity-70 transition group">
        <span class="group-hover:-translate-x-1 transition-transform">←</span> 
        <span class="uppercase tracking-widest text-[10px] sm:text-xs">Voltar ao Ecossistema</span>
      </button>
      <div class="text-[#D97757] font-serif italic text-xl select-none">Liceu 6.0</div>
    </nav>

    <main class="max-w-7xl mx-auto px-6 py-12 lg:py-20">
      <div class="grid lg:grid-cols-2 gap-16 items-start">
        
        <!-- COLUNA 1: NARRATIVA E VÍDEO -->
        <div class="space-y-10">
          <header>
            <h1 class="font-serif text-5xl lg:text-7xl text-[#F4EBD0] mb-6 leading-tight">
              3C273 <span class="text-[#D97757]">Cefeida</span>
            </h1>
            <p class="text-[#F4EBD0]/80 text-xl font-light leading-relaxed max-w-xl">
              A inteligência pericial que transforma o caos operacional em uma estratégia industrializável e lucrativa.
            </p>
          </header>

          <!-- Vídeo Institucional com Moldura de Luxo -->
          <div class="relative group">
            <div class="absolute -inset-1 bg-gradient-to-r from-[#D97757] to-[#34495E] rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000"></div>
            <div class="relative aspect-video bg-black rounded-xl overflow-hidden border border-[#F4EBD0]/10 shadow-2xl">
              <!-- Substitua o ID final pelo ID real do seu vídeo no YouTube -->
              <iframe 
                class="w-full h-full" 
                src="https://youtube.com" 
                title="Liceu 6.0 - Cefeida"
                frameborder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
              </iframe>
            </div>
          </div>

          <article class="space-y-4">
            <h3 class="text-[#D97757] font-serif text-2xl">Reestruturação de Empresas</h3>
            <p class="text-[#F4EBD0]/70 leading-relaxed text-lg">
              Através da Cefeida, a Liceu 6.0 aplica seu <strong>Sistema Operacional</strong> para salvar e escalar negócios. Identificamos gargalos financeiros e operacionais com precisão quasar, redesenhando sua empresa para rodar com a fluidez de uma linha de montagem industrial.
            </p>
          </article>
        </div>

        <!-- COLUNA 2: QUESTIONÁRIO PERICIAL (O "GATE") -->
        <div class="lg:sticky lg:top-32 bg-[#F4EBD0] p-8 sm:p-10 rounded-3xl shadow-2xl transform lg:rotate-1 transition-transform hover:rotate-0 duration-500">
          <div class="text-[#2C1B18]">
            <h2 class="font-serif text-3xl mb-2">Solicitar Diagnóstico</h2>
            <p class="text-xs opacity-70 mb-8 uppercase tracking-widest font-bold">Inicie sua reestruturação estratégica</p>
            
            <form @submit.prevent="handleSubmit" class="space-y-6">
              <div class="space-y-1">
                <label class="text-[10px] font-bold uppercase text-[#2C1B18]/60">Nome da Organização</label>
                <input required v-model="form.empresa" type="text" placeholder="Ex: Construtora Alfa" class="w-full bg-transparent border-b-2 border-[#2C1B18]/20 py-3 focus:border-[#D97757] outline-none transition-colors placeholder:text-[#2C1B18]/30">
              </div>

              <div class="space-y-1">
                <label class="text-[10px] font-bold uppercase text-[#2C1B18]/60">Principal Desafio Atual</label>
                <div class="relative">
                  <select v-model="form.desafio" class="w-full bg-transparent border-b-2 border-[#2C1B18]/20 py-3 focus:border-[#D97757] outline-none appearance-none cursor-pointer">
                    <option value="caixa">Fluxo de Caixa e Endividamento</option>
                    <option value="processos">Burocracia e Lentidão Operacional</option>
                    <option value="dados">Decisões Sem Base de Dados</option>
                    <option value="escala">Dificuldade em Escalar o Modelo</option>
                  </select>
                  <span class="absolute right-2 top-4 pointer-events-none text-[#2C1B18]/40">▼</span>
                </div>
              </div>

              <div class="space-y-1">
                <label class="text-[10px] font-bold uppercase text-[#2C1B18]/60">Nível de Urgência</label>
                <div class="flex gap-3 pt-2">
                  <label v-for="(label, idx) in ['Estratégico', 'Tático', 'Crítico']" :key="idx" class="flex-1 cursor-pointer">
                    <input type="radio" :value="idx + 1" v-model="form.urgencia" class="sr-only peer">
                    <div class="text-center p-2 text-[10px] sm:text-xs border border-[#2C1B18]/20 rounded-lg peer-checked:bg-[#2C1B18] peer-checked:text-white transition-all duration-300 hover:border-[#2C1B18]">
                      {{ label }}
                    </div>
                  </label>
                </div>
              </div>

              <div class="space-y-1">
                <label class="text-[10px] font-bold uppercase text-[#2C1B18]/60">Mensagem do Gestor</label>
                <textarea v-model="form.mensagem" rows="3" class="w-full bg-white/50 border border-[#2C1B18]/10 p-4 rounded-xl focus:border-[#D97757] outline-none transition-colors placeholder:text-[#2C1B18]/30" placeholder="Descreva brevemente sua dor operacional..."></textarea>
              </div>

              <button 
                type="submit" 
                :disabled="isSubmitting"
                class="w-full bg-[#2C1B18] text-[#F4EBD0] py-5 rounded-full font-bold uppercase tracking-[0.2em] text-xs hover:bg-[#D97757] transition-all shadow-lg active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-3"
              >
                <span v-if="isSubmitting" class="animate-spin text-xl">◌</span>
                {{ isSubmitting ? 'Processando Analítica...' : 'Enviar para Análise Cefeida' }}
              </button>
            </form>
          </div>
        </div>

      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const isSubmitting = ref(false)

const form = ref({
  empresa: '',
  desafio: 'caixa',
  urgencia: 1,
  mensagem: ''
})

const handleSubmit = async () => {
  isSubmitting.value = true
  
  try {
    // Simulação de delay para processamento da "IA/Analítica"
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    console.log("Payload para o Archimedes/Cefeida (FastAPI):", form.value)
    alert("Protocolo Cefeida Iniciado. Sua organização foi enviada para o cérebro estratégico da Liceu 6.0.")
    
    // Limpar formulário após envio
    form.value = { empresa: '', desafio: 'caixa', urgencia: 1, mensagem: '' }
    
  } catch (error) {
    alert("Erro na conexão com o Ecossistema. Tente novamente.")
  } finally {
    isSubmitting.value = false
  }
}
</script>

<style scoped>
/* Estilização refinada para inputs e transições */
input:focus, select:focus, textarea:focus {
  box-shadow: 0 4px 12px -6px rgba(217, 119, 87, 0.3);
}

/* Scrollbar personalizada para manter o visual premium */
::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-track {
  background: #2C1B18;
}
::-webkit-scrollbar-thumb {
  background: #D97757;
  border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover {
  background: #f4ebd0;
}
</style>
