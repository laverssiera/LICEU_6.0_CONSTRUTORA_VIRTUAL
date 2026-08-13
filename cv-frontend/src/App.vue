<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import JohnConcierge from '@/components/JohnConcierge.vue'

const route = useRoute()
const showJohnConcierge = computed(() => route.path !== '/download')
</script>

<template>
  <router-view />
  <JohnConcierge v-if="showJohnConcierge" />
</template>

<style>
/* RESET GLOBAL - Isso resolve o desalinhamento da imagem */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', sans-serif;
  background-color: #f4f7f6;
  -webkit-font-smoothing: antialiased;
}

/* Scrollbar Industrial */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #f1f1f1; }
::-webkit-scrollbar-thumb { background: #1a365d; border-radius: 4px; }
</style>
