<template>
  <div class="mission-dashboard-container p-6">
    <header class="mb-8">
      <h1 class="text-3xl font-bold text-slate-800 dark:text-slate-100 uppercase tracking-wide">
        🪐 Mission Lifecycle Dashboard
      </h1>
      <p class="text-slate-500 mt-2">
        Tracking cross-monolith execution, budget health, and orchestration statuses.
      </p>
    </header>

    <!-- Error State -->
    <div v-if="error" class="bg-red-100 text-red-700 p-4 rounded-md mb-6 shadow-sm">
      Falha ao carregar métricas das Missões: {{ error }}
    </div>

    <!-- Loading State -->
    <div v-else-if="loading" class="flex justify-center p-12">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
    </div>

    <!-- Data Loaded -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div 
        v-for="mission in missions" 
        :key="mission.mission_id" 
        class="bg-white dark:bg-slate-800 rounded-xl shadow-md p-6 border-l-4 transition-all duration-300 hover:shadow-lg"
        :class="borderClass(mission.health)"
      >
        <div class="flex justify-between items-start mb-4">
          <h2 class="text-xl font-bold text-slate-800 dark:text-slate-200">
            {{ mission.name }}
          </h2>
          <span 
            class="px-2 py-1 text-xs font-semibold rounded-full uppercase"
            :class="stateClass(mission.lifecycle_state)"
          >
            {{ mission.lifecycle_state }}
          </span>
        </div>
        
        <div class="text-sm text-slate-500 font-mono mb-4 text-xs truncate">
          ID: {{ mission.mission_id }}
        </div>

        <div class="mb-4">
          <p class="text-sm text-slate-600 dark:text-slate-400 mb-1">
            <strong>Orçamento Gasto:</strong> {{ mission.budget_spent_pct }}%
          </p>
          <div class="w-full bg-slate-200 rounded-full h-2.5 dark:bg-slate-700">
            <div 
              class="h-2.5 rounded-full" 
              :class="progressClass(mission.health)"
              :style="{ width: Math.min(mission.budget_spent_pct, 100) + '%' }"
            ></div>
          </div>
        </div>

        <div class="flex justify-between items-center text-sm mt-6 pt-4 border-t border-slate-100 dark:border-slate-700">
          <div>
            <span class="block text-slate-500">Contratos</span>
            <strong class="text-slate-700 dark:text-slate-300">{{ mission.contracts_active }} ativos</strong>
          </div>
          <div class="text-right">
            <span class="block text-slate-500">Stakeholders</span>
            <strong class="text-slate-700 dark:text-slate-300">{{ mission.stakeholders.length }} nodes</strong>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const missions = ref([]);
const loading = ref(true);
const error = ref(null);

const fetchMissions = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/v1/mission-tracker/status');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    missions.value = data;
  } catch (err) {
    error.value = err.message;
    console.error("Missions sync error:", err);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchMissions();
});

const borderClass = (health) => {
  if (health === 'GREEN') return 'border-emerald-500';
  if (health === 'YELLOW') return 'border-amber-400';
  if (health === 'RED') return 'border-rose-500';
  return 'border-slate-300';
};

const progressClass = (health) => {
  if (health === 'GREEN') return 'bg-emerald-500';
  if (health === 'YELLOW') return 'bg-amber-400';
  if (health === 'RED') return 'bg-rose-500';
  return 'bg-indigo-500';
};

const stateClass = (state) => {
  if (state === 'RUNNING') return 'bg-indigo-100 text-indigo-700';
  if (state === 'BLOCKED') return 'bg-rose-100 text-rose-700';
  if (state === 'COMPLETED') return 'bg-emerald-100 text-emerald-700';
  return 'bg-slate-100 text-slate-600';
};
</script>
