<template>
  <div class="fixed bottom-6 right-6 z-50">
    <!-- Balão de Fala do Amigão -->
    <div v-if="aberto" class="bg-white w-80 h-96 shadow-2xl rounded-3xl border-4 border-yellow-400 overflow-hidden flex flex-col">
      <div class="bg-yellow-400 p-4 font-black flex justify-between items-center text-gray-900">
        <span>👷‍♂️ AMIGÃO LICEU</span>
        <button @click="aberto = false">X</button>
      </div>
      
      <div class="flex-1 p-4 overflow-y-auto text-sm text-gray-700 space-y-4">
        <p class="bg-gray-100 p-3 rounded-2xl rounded-tl-none">
          Olá! Sou o **Amigão Liceu**. Vi que você está olhando esse terreno... Sabia que o zoneamento aqui permite 4x a área?
        </p>
      </div>

      <div class="p-4 border-t">
        <input type="text" placeholder="Pergunte ao Amigão..." class="w-full border rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-yellow-400" />
      </div>
    </div>

    <!-- Botão Avatar -->
    <button @click="aberto = !aberto" class="bg-yellow-400 w-16 h-16 rounded-full shadow-lg border-4 border-white flex items-center justify-center text-3xl hover:scale-110 transition">
      👷‍♂️
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const aberto = ref(false)
</script>
