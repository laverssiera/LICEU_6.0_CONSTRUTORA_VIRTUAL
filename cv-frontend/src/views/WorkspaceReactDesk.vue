<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { createElement } from 'react'
import { createRoot } from 'react-dom/client'
import KanbanBoard from '@/react-workspace/KanbanBoard.jsx'

const mountRef = ref(null)
let reactRoot = null

const featureEnabled = computed(() => import.meta.env.VITE_ENABLE_REACT_WORKSPACE !== 'false')

onMounted(() => {
  if (!featureEnabled.value || !mountRef.value) {
    return
  }

  reactRoot = createRoot(mountRef.value)
  reactRoot.render(createElement(KanbanBoard))
})

onBeforeUnmount(() => {
  if (reactRoot) {
    reactRoot.unmount()
    reactRoot = null
  }
})
</script>

<template>
  <section class="react-workspace-shell">
    <header class="bridge-head">
      <p class="eyebrow">LICEU 6.0</p>
      <h1>Workspace Central React Desk</h1>
      <p class="copy">
        Modo institucional em tempo real conectado ao /events/ws. Configure
        VITE_ENABLE_REACT_WORKSPACE=false para fallback sem montar React.
      </p>
    </header>

    <div v-if="featureEnabled" ref="mountRef" class="react-mount" />

    <article v-else class="fallback-box">
      <h2>Feature flag desativada</h2>
      <p>Defina VITE_ENABLE_REACT_WORKSPACE=true para ativar o desk React.</p>
    </article>
  </section>
</template>

<style scoped>
.react-workspace-shell {
  min-height: 100vh;
  background: linear-gradient(170deg, #020617 0%, #0f172a 55%, #111827 100%);
  color: #e2e8f0;
}

.bridge-head {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
}

.eyebrow {
  margin: 0;
  color: #67e8f9;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-size: 0.72rem;
}

.bridge-head h1 {
  margin: 0.35rem 0;
  font-size: 1.4rem;
}

.copy {
  margin: 0;
  color: #94a3b8;
  font-size: 0.92rem;
}

.react-mount {
  min-height: calc(100vh - 122px);
}

.fallback-box {
  margin: 1.5rem;
  padding: 1.25rem;
  border-radius: 14px;
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: rgba(15, 23, 42, 0.75);
}
</style>
