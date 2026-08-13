<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const detectedPlatform = ref('desktop')
const isRedirecting = ref(false)

const token = computed(() => String(route.query.token || 'jornada-demo'))
const playStoreUrl = computed(() => `https://play.google.com/store/apps/details?id=br.liceu.app&referrer=${encodeURIComponent(token.value)}`)
const appStoreUrl = computed(() => `https://apps.apple.com/br/app/liceu-6-0/id6740000000?pt=${encodeURIComponent(token.value)}`)
const canonicalDownloadUrl = computed(() => `https://liceu.app/download?token=${encodeURIComponent(token.value)}`)
const qrCodeUrl = computed(() => `https://api.qrserver.com/v1/create-qr-code/?size=280x280&data=${encodeURIComponent(canonicalDownloadUrl.value)}`)

function detectPlatform() {
  if (typeof navigator === 'undefined') return 'desktop'
  const userAgent = navigator.userAgent.toLowerCase()
  if (/android/.test(userAgent)) return 'android'
  if (/iphone|ipad|ipod/.test(userAgent)) return 'ios'
  return 'desktop'
}

function redirectToStore(platform = detectedPlatform.value) {
  isRedirecting.value = true
  window.location.href = platform === 'android' ? playStoreUrl.value : appStoreUrl.value
}

onMounted(() => {
  detectedPlatform.value = String(route.query.platform || detectPlatform())

  if (detectedPlatform.value === 'android' || detectedPlatform.value === 'ios') {
    window.setTimeout(() => redirectToStore(detectedPlatform.value), 350)
  }
})
</script>

<template>
  <section class="download-bridge">
    <div class="download-card">
      <span class="eyebrow">LICEU APP</span>
      <h1>Continue sua jornada no App LICEU 6.0</h1>
      <p>
        {{ isRedirecting
          ? 'Abrindo a loja do seu dispositivo para continuar sua jornada.'
          : 'Acompanhe sua casa em tempo real, com login automático e eventos do John.' }}
      </p>

      <div v-if="detectedPlatform === 'desktop'" class="desktop-layout">
        <img :src="qrCodeUrl" alt="QR Code LICEU App" class="qr-image" />
        <div class="download-actions">
          <a :href="playStoreUrl" class="store-btn">Baixar Android</a>
          <a :href="appStoreUrl" class="store-btn secondary">Baixar iPhone</a>
        </div>
        <small>Token da jornada reconhecido: {{ token }}</small>
      </div>

      <div v-else class="mobile-layout">
        <div class="mobile-icon">📱</div>
        <div class="download-actions">
          <button class="store-btn" @click="redirectToStore(detectedPlatform)">Abrir download</button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.download-bridge {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 32px 16px;
  background: linear-gradient(135deg, #0f172a, #1d4ed8);
}

.download-card {
  width: min(560px, 100%);
  background: white;
  border-radius: 24px;
  padding: 28px;
  text-align: center;
  box-shadow: 0 25px 60px rgba(15, 23, 42, 0.28);
}

.eyebrow {
  display: inline-block;
  margin-bottom: 10px;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  color: #c53030;
}

h1 {
  font-size: 2rem;
  color: #133a5e;
  margin-bottom: 10px;
}

p {
  color: #475569;
  margin-bottom: 18px;
}

.desktop-layout,
.mobile-layout {
  display: grid;
  gap: 16px;
  justify-items: center;
}

.qr-image {
  width: 280px;
  height: 280px;
  border-radius: 18px;
  border: 1px solid #e2e8f0;
  padding: 10px;
  background: white;
}

.mobile-icon {
  font-size: 3rem;
}

.download-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: center;
}

.store-btn {
  border: none;
  background: #133a5e;
  color: white;
  text-decoration: none;
  padding: 12px 18px;
  border-radius: 12px;
  font-weight: 700;
  cursor: pointer;
}

.store-btn.secondary {
  background: #7c3aed;
}

small {
  color: #64748b;
  word-break: break-word;
}
</style>
