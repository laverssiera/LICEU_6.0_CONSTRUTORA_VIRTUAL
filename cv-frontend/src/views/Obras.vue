<template>
  <div class="p-10 bg-slate-50 min-h-screen">
    <button @click="$router.back()" class="mb-6 text-blue-900 font-bold hover:underline">
      ← VOLTAR AO ECOSSISTEMA
    </button>
    
    <h1 class="text-4xl font-black text-[#1a365d] uppercase tracking-tighter">
      Status de <span class="text-[#c53030]">Obras</span>
    </h1>
    <p class="text-slate-500 mt-2 italic">Acompanhamento em tempo real da produção industrial Liceu 6.0.</p>
    
    <div class="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- Placeholder de Obra -->
      <div v-for="i in 3" :key="i" class="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <div class="h-40 bg-slate-100 rounded-lg mb-4 flex items-center justify-center text-slate-400">
          IMAGEM DA OBRA {{ i }}
        </div>
        <h3 class="font-bold text-lg">Residencial Liceu Alpha-0{{ i }}</h3>
        <p class="text-sm text-slate-500">Status: Montagem Estrutural</p>
      </div>
    </div>
  </div>
</template>

<script setup>
// Lógica de monitoramento de obras em tempo real
</script>

<style scoped>
/* Estilos específicos para o módulo de obras */
</style>
