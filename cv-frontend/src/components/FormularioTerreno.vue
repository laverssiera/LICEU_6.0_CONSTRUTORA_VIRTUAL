<template>
  <div class="bg-white p-6 rounded-xl shadow-md border-t-4 border-blue-600 h-full">
    <h3 class="font-black text-gray-800 mb-6 flex items-center">
      🏗️ NOVA ANÁLISE DE LOTE
    </h3>
    
    <form @submit.prevent="enviarEstudo" class="space-y-4">
      <div>
        <label class="text-xs font-bold text-gray-500 uppercase">Endereço ou CEP</label>
        <input v-model="form.endereco" type="text" class="w-full border p-2 rounded bg-gray-50 focus:ring-2 focus:ring-blue-500" placeholder="Ex: Rua Oscar Freire, 500" required />
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="text-xs font-bold text-gray-500 uppercase">Área (m²)</label>
          <input v-model.number="form.area_terreno" type="number" class="w-full border p-2 rounded bg-gray-50" required />
        </div>
        <div>
          <label class="text-xs font-bold text-gray-500 uppercase">Matrícula</label>
          <input v-model="form.matricula" type="text" class="w-full border p-2 rounded bg-gray-50" placeholder="000.000" required />
        </div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="text-xs font-bold text-gray-500 uppercase">Valor Terreno (R$)</label>
          <input v-model.number="form.valor_terreno" type="number" class="w-full border p-2 rounded bg-gray-50" required />
        </div>
        <div>
          <label class="text-xs font-bold text-gray-500 uppercase">Venda Estimada/m²</label>
          <input v-model.number="form.valor_venda_m2" type="number" class="w-full border p-2 rounded bg-gray-50" value="4500" />
        </div>
      </div>

      <button type="submit" :disabled="loading" 
        class="w-full bg-blue-900 text-white font-black py-3 rounded-lg hover:bg-blue-800 transition disabled:bg-gray-400">
        {{ loading ? 'PROCESSANDO IA...' : 'GERAR VIABILIDADE' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import api from '@/services/api'

const emit = defineEmits(['estudoCriado'])
const loading = ref(false)
const form = reactive({
  endereco: '', area_terreno: 0, valor_terreno: 0,
  valor_venda_m2: 4500, custo_obra_m2: 2200, matricula: ''
})

const enviarEstudo = async () => {
  loading.value = true
  try {
    const res = await api.post('/viabilidade/gerar-evtl/', form)
    alert(`Sucesso! Zona Detectada: ${res.data.zona_detectada}`)
    emit('estudoCriado') // Avisa o App.vue para recarregar o mapa e stats
    // Limpa o form
    form.endereco = ''; form.area_terreno = 0; form.valor_terreno = 0; form.matricula = ''
  } catch (e) {
    alert("Erro ao processar: " + (e.response?.data?.detail || "Erro de conexão"))
  } finally {
    loading.value = false
  }
}
</script>
