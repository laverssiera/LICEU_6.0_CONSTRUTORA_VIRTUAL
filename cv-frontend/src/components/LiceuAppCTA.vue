<script setup>
import { computed } from 'vue'

const props = defineProps({
  downloadUrl: {
    type: String,
    default: 'https://liceu.app/download'
  },
  playStoreUrl: {
    type: String,
    default: 'https://play.google.com/store/apps/details?id=br.liceu.app'
  },
  appStoreUrl: {
    type: String,
    default: 'https://apps.apple.com/br/app/liceu-6-0/id6740000000'
  }
})

const qrCodeUrl = computed(() => {
  const encoded = encodeURIComponent(props.downloadUrl)
  return `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encoded}`
})
</script>

<template>
  <section class="app-cta-shell">
    <div class="app-cta-card">
      <h2>Continue sua jornada no App LICEU 6.0</h2>
      <p class="subtitle">Acompanhe sua casa em tempo real</p>

      <div class="qr-wrapper">
        <img :src="qrCodeUrl" alt="QR Code App LICEU 6.0" class="qr-image" />
      </div>

      <p class="hint">Escaneie com o celular</p>

      <div class="download-row">
        <a :href="playStoreUrl" class="store-btn android">Baixar Android</a>
        <a :href="appStoreUrl" class="store-btn ios">Baixar iPhone</a>
      </div>
    </div>
  </section>
</template>

<style scoped>
.app-cta-shell {
  padding: 8px 0;
}

.app-cta-card {
  background: linear-gradient(135deg, #f8fafc, #eef2f7);
  border-radius: 24px;
  padding: 32px 20px;
  text-align: center;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.12);
  border: 1px solid #dbe4ee;
}

.app-cta-card h2 {
  font-size: clamp(1.8rem, 4vw, 2.3rem);
  color: #133a5e;
  margin-bottom: 8px;
}

.subtitle {
  color: #5b6b7b;
  margin-bottom: 18px;
}

.qr-wrapper {
  display: flex;
  justify-content: center;
  margin: 16px 0;
}

.qr-image {
  width: 180px;
  height: 180px;
  border-radius: 18px;
  border: 1px solid #dbe4ee;
  padding: 10px;
  background: white;
}

.hint {
  color: #6b7280;
  font-size: 0.95rem;
}

.download-row {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 18px;
}

.store-btn {
  text-decoration: none;
  padding: 12px 18px;
  border-radius: 14px;
  color: white;
  font-weight: 700;
  min-width: 170px;
}

.store-btn.android {
  background: #111827;
}

.store-btn.ios {
  background: #374151;
}
</style>
