import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'

import '@/styles/main.css'

import Home from '@/components/Home.vue'
import ArchimedesJourney from '@/Dashboard.vue'
import Escola from '@/views/Escola.vue'
import Obras from '@/views/Obras.vue'
import DownloadBridge from '@/views/DownloadBridge.vue'
import Investidores from '@/views/Investidores.vue'
import Dados from '@/views/Dados.vue'
import Juridico from '@/views/Juridico.vue'
import KanbanGlobal from '@/views/KanbanGlobal.vue'
import EcosystemView from '@/views/EcosystemView.vue'
import WorkspaceReactDesk from '@/views/WorkspaceReactDesk.vue'
import StrategicDashboard from '@/views/StrategicDashboard.vue'
import StrategyStudio from '@/views/StrategyStudio.vue'
import CRMDashboard from '@/views/CRMDashboard.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/archimedes',
    name: 'Archimedes',
    component: ArchimedesJourney
  },
  {
    path: '/download',
    name: 'DownloadBridge',
    component: DownloadBridge
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
    path: '/investidores',
    name: 'Investidores',
    component: Investidores
  },
  {
    path: '/dados',
    name: 'Dados',
    component: Dados
  },
  {
    path: '/juridico',
    name: 'Juridico',
    component: Juridico
  },
  {
    path: '/kanban',
    name: 'KanbanGlobal',
    component: KanbanGlobal
  },
  {
    path: '/estrategico',
    name: 'StrategicDashboard',
    component: StrategicDashboard
  },
  {
    path: '/estrategias',
    name: 'StrategyStudio',
    component: StrategyStudio
  },
  {
    path: '/crm-dashboard',
    name: 'CRMDashboard',
    component: CRMDashboard
  },
  {
    path: '/ecosystem',
    name: 'EcosystemDashboard',
    component: EcosystemView
  },
  {
    path: '/workspace/react-desk',
    name: 'WorkspaceReactDesk',
    component: WorkspaceReactDesk
  },
  {
    path: '/institucional',
    name: 'Institucional',
    component: () => import('@/pages/Institucional.vue')
  },
  {
    path: '/cefeida',
    redirect: '/dados'
  },
  {
    path: '/cea-investimentos',
    redirect: '/investidores'
  },
  {
    path: '/juridico-tech',
    redirect: '/juridico'
  }
]

// 3. Criação do Roteador (Motor de Navegação)
const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

// 4. Inicialização do Motor da Liceu 6.0
const app = createApp(App)

app.use(router)
app.mount('#app')

console.log("🚀 Liceu Engenharia 6.0: Home principal restaurada e jornada Archimedes em operação.");
