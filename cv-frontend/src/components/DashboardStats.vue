<template>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
    <!-- Card VGV -->
    <div class="bg-white p-6 rounded-xl shadow-md border-l-4 border-blue-500">
      <p class="text-sm text-gray-500 font-bold uppercase">VGV Mapeado</p>
      <p class="text-2xl font-black text-blue-900">R$ {{ stats.vgv_total_mapeado?.toLocaleString() }}</p>
    </div>

    <!-- Card Análises -->
    <div class="bg-white p-6 rounded-xl shadow-md border-l-4 border-green-500">
      <p class="text-sm text-gray-500 font-bold uppercase">Análises Realizadas</p>
      <p class="text-2xl font-black text-green-900">{{ stats.total_analises }} estudos</p>
    </div>

    <!-- Card Eficiência -->
    <div class="bg-white p-6 rounded-xl shadow-md border-l-4 border-purple-500">
      <p class="text-sm text-gray-500 font-bold uppercase">Taxa de Viabilidade</p>
      <p class="text-2xl font-black text-purple-900">{{ stats.taxa_viabilidade }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps(['stats'])
</script>
