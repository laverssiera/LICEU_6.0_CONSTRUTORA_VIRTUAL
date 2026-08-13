<template>
  <div class="min-h-screen bg-[#f8fafc] font-sans">
    <!-- Header de Navegação Interna -->
    <nav class="bg-[#1a365d] p-6 text-white flex justify-between items-center shadow-lg">
      <button @click="$router.back()" class="flex items-center gap-2 hover:text-[#c53030] transition-colors font-bold text-xs uppercase tracking-widest">
        ← Voltar ao Dashboard
      </button>
      <div class="font-black italic uppercase tracking-tighter">Academia do Saber <span class="text-[#c53030]">6.0</span></div>
    </nav>

    <main class="max-w-6xl mx-auto py-16 px-6">
      <header class="mb-12 border-l-8 border-[#c53030] pl-8">
        <h1 class="text-5xl font-black text-[#1a365d] uppercase tracking-tighter leading-none mb-4">
          Centro de <br/> <span class="text-[#c53030]">Treinamento</span> Industrial
        </h1>
        <p class="text-slate-500 text-lg italic max-w-2xl font-light">
          Capacitando a mão de obra para a revolução da construção modular e industrializada.
        </p>
      </header>

      <!-- Grid de Cursos/Treinamentos -->
      <div class="grid md:grid-cols-3 gap-8">
        <div v-for="curso in cursos" :key="curso.id" class="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm hover:shadow-xl transition-all group">
          <div class="text-4xl mb-4 group-hover:scale-110 transition-transform duration-300">{{ curso.icon }}</div>
          <h3 class="font-bold text-[#1a365d] text-xl mb-2">{{ curso.titulo }}</h3>
          <p class="text-sm text-slate-400 mb-6">{{ curso.desc }}</p>
          <button class="w-full bg-[#f1f5f9] text-[#1a365d] py-3 rounded-lg font-bold text-[10px] uppercase tracking-widest hover:bg-[#1a365d] hover:text-white transition">
            Iniciar Módulo
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const cursos = ref([
  { id: 1, icon: '🏗️', titulo: 'Montagem Modular', desc: 'Técnicas avançadas de encaixe e vedação de módulos industriais.' },
  { id: 2, icon: '🤖', titulo: 'Operação BIM', desc: 'Leitura de projetos em tempo real no canteiro de obras.' },
  { id: 3, icon: '🛡️', titulo: 'Segurança 6.0', desc: 'Protocolos de segurança para ambientes de construção virtual.' }
])
</script>

<style scoped>
/* Estilos específicos para a Academia do Saber */
</style>
