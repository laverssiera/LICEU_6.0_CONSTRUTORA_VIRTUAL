<template>
  <div class="p-6 bg-indigo-900 text-white rounded-2xl shadow-xl">
    <h3 class="font-black italic mb-4">🏆 AJUDE SEU AMIGO A CONSTRUIR!</h3>
    <p class="text-sm mb-6">O que você acha dessa combinação de cores para a fachada?</p>
    
    <div class="flex gap-4 mb-6">
      <button @click="votar(1)" class="flex-1 bg-white text-indigo-900 font-bold py-2 rounded">OPÇÃO A</button>
      <button @click="votar(2)" class="flex-1 bg-white text-indigo-900 font-bold py-2 rounded">OPÇÃO B</button>
    </div>

    <div v-if="votou" class="text-center animate-bounce">
      <p class="font-bold text-yellow-400">BRINDE DESBLOQUEADO! 🎁</p>
      <p class="text-xs">Verifique seu e-mail para seu desconto Liceu.</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const votou = ref(false)
const votar = (opcao) => {
  votou.value = true
  // Envia para o backend processar_voto_amigo()
}
</script>
