import { createRouter, createWebHistory } from 'vue-router'

// 1. Importações baseadas na sua estrutura de pastas (Imagem enviada)
// O Dashboard está na raiz do src, então usamos '../Dashboard.vue' se estiver dentro da pasta router
import Dashboard from '@/Dashboard.vue' 
import Escola from '@/views/Escola.vue'
import Obras from '@/views/Obras.vue'
import MissionDashboard from '@/views/MissionDashboard.vue'

// 2. Definição ÚNICA das rotas
const routes = [
  {
    path: '/',
    name: 'Home',
    component: Dashboard
  },
  {
    path: '/escola',
    name: 'Escola',
    component: Escola
  },
  {
    path: '/obras',
    name: 'Obras',
    component: Obras
  },
  {
    path: '/mission-dashboard',
    name: 'MissionDashboard',
    component: MissionDashboard
  }
]

// 3. Criação ÚNICA do motor de navegação
const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
