<template>
  <div class="w-full h-96 bg-gray-200 rounded-lg flex items-center justify-center">
    <p class="text-gray-600">Mapa de Viabilidade - Em desenvolvimento</p>
  </div>
</template>

<script setup>
defineProps({
  estudos: {
    type: Array,
    default: () => []
  }
})
</script>