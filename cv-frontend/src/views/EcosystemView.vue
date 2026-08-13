<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { createElement } from 'react'
import { createRoot } from 'react-dom/client'
import EcosystemDashboard from '@/react-workspace/EcosystemDashboard.jsx'

const mountRef = ref(null)
let reactRoot = null

onMounted(() => {
  if (!mountRef.value) return
  reactRoot = createRoot(mountRef.value)
  reactRoot.render(createElement(EcosystemDashboard))
})

onBeforeUnmount(() => {
  if (reactRoot) {
    reactRoot.unmount()
    reactRoot = null
  }
})
</script>

<template>
  <div ref="mountRef" class="ecosystem-shell" />
</template>

<style scoped>
.ecosystem-shell {
  min-height: 100vh;
  background: #020617;
}
</style>
