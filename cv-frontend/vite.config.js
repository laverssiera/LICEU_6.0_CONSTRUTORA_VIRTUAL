import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// Configuração do ambiente de compilação
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const proxyTarget = env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000'

  return {
    plugins: [vue(), react()],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src') // Define o atalho @ para a pasta src
      }
    },
    server: {
      proxy: {
        '/gateway': { target: proxyTarget, changeOrigin: true },
        '/viabilidade': { target: proxyTarget, changeOrigin: true },
        '/john': { target: proxyTarget, changeOrigin: true },
        '/auth': { target: proxyTarget, changeOrigin: true },
        '/kanban': { target: proxyTarget, changeOrigin: true },
        '/strategic-kanban': { target: proxyTarget, changeOrigin: true },
        '/strategic-suggestions': { target: proxyTarget, changeOrigin: true },
        '/strategies': { target: proxyTarget, changeOrigin: true },
        '/objectives': { target: proxyTarget, changeOrigin: true },
        '/initiatives': { target: proxyTarget, changeOrigin: true },
        '/plans': { target: proxyTarget, changeOrigin: true },
        '/tasks': { target: proxyTarget, changeOrigin: true },
        '/events': { target: proxyTarget, changeOrigin: true, ws: true },
        '/ws': { target: proxyTarget, changeOrigin: true, ws: true },
        '/sdk': { target: proxyTarget, changeOrigin: true },
        '/metrics': { target: proxyTarget, changeOrigin: true },
        '/decisions': { target: proxyTarget, changeOrigin: true },
        '/autonomous': { target: proxyTarget, changeOrigin: true },
        '/executive': { target: proxyTarget, changeOrigin: true },
        '/innovation': { target: proxyTarget, changeOrigin: true }
      }
    }
  }
})
