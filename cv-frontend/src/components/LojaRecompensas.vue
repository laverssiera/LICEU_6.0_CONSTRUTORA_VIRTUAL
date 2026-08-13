<template>
  <div class="bg-gray-50 p-6 rounded-3xl border-2 border-dashed border-indigo-200">
    <div class="flex items-center justify-between mb-6">
      <h3 class="font-black text-indigo-900 uppercase italic">🎁 Loja de Conquistas</h3>
      <div class="text-right">
        <p class="text-xs font-bold text-gray-400">SEUS PONTOS</p>
        <p class="text-2xl font-black text-indigo-600">✨ {{ saldo }}</p>
      </div>
    </div>

    <div class="space-y-4">
      <div v-for="item in catalogo" :key="item.id" 
           class="flex items-center justify-between p-4 bg-white rounded-2xl shadow-sm border border-gray-100">
        <div class="flex items-center gap-3">
          <span class="text-2xl">{{ item.icone }}</span>
          <div>
            <p class="font-bold text-sm text-gray-800">{{ item.nome }}</p>
            <p class="text-[10px] text-gray-400 uppercase tracking-tighter">{{ item.custo }} Pontos</p>
          </div>
        </div>
        <button :disabled="saldo < item.custo" 
                class="px-4 py-2 bg-indigo-600 text-white text-xs font-black rounded-lg disabled:bg-gray-200 transition">
          RESGATAR
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const saldo = ref(6800)
const catalogo = [
  { id: 1, nome: 'Fechadura Digital', custo: 3000, icone: '🔐' },
  { id: 2, nome: 'Upgrade Painel Solar', custo: 8000, icone: '☀️' },
  { id: 3, nome: 'Kit Automação Luz', custo: 2000, icone: '💡' }
]
</script>
