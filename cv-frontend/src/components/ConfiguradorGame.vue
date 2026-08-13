<template>
  <div class="game-container bg-gray-900 p-8 rounded-3xl text-white shadow-2xl">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-black italic italic">🎮 CONSTRUTORA VIRTUAL LICEU</h2>
      <div class="flex gap-4">
        <span class="bg-yellow-500 p-2 rounded-lg font-bold text-black">XP: {{ xp }}</span>
        <span class="bg-blue-500 p-2 rounded-lg font-bold">NÍVEL: {{ nivel }}</span>
      </div>
    </div>

    <!-- O Visualizador 3D do BIM -->
    <div class="canvas-3d h-64 bg-gray-800 rounded-2xl mb-6 flex items-center justify-center border-2 border-dashed border-gray-600">
      <p class="text-gray-400">Renderização Real-Time do seu Kit Liceu</p>
    </div>

    <!-- Opções Estilo Card -->
    <div class="grid grid-cols-2 gap-4">
      <button @click="selecionarItem('painel_solar')" class="hover:scale-105 transition p-4 bg-gray-800 rounded-xl border-2 border-green-500">
        ☀️ Energia Solar (+500 XP)
      </button>
      <button @click="selecionarItem('automacao_premium')" class="hover:scale-105 transition p-4 bg-gray-800 rounded-xl border-2 border-purple-500">
        🤖 Automação (+300 XP)
      </button>
    </div>

    <!-- Botão Convidar Amigo -->
    <button class="mt-8 w-full bg-indigo-600 py-3 rounded-full font-black uppercase tracking-widest hover:bg-indigo-500 transition">
      📣 Chamar Amigos para Opinar
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const xp = ref(1200)
const nivel = ref('Mestre de Obra')

const selecionarItem = (item) => {
  // Aqui o Vue chama o 'gameficacao_motor.py' no backend
  console.log("Item selecionado:", item)
}
</script>
