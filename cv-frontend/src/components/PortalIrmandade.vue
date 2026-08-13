<template>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-6 p-6 bg-gray-50">
    
    <!-- CARD 1: MEU PROGRESSO (GAMIFICAÇÃO) -->
    <div class="bg-indigo-900 text-white p-6 rounded-3xl shadow-xl">
      <div class="flex justify-between items-start mb-4">
        <p class="text-xs font-bold uppercase tracking-widest opacity-70">Nível na Irmandade</p>
        <span class="text-2xl">🥇</span>
      </div>
      <h3 class="text-2xl font-black mb-2">Mestre Montador</h3>
      <div class="w-full bg-indigo-800 h-2 rounded-full mt-4">
        <div class="bg-yellow-400 h-2 rounded-full" style="width: 75%"></div>
      </div>
      <p class="text-[10px] mt-2 text-indigo-200">Faltam 250 pontos para o próximo nível (Especialista BIM)</p>
    </div>

    <!-- CARD 2: TREINAMENTOS E VÍDEOS -->
    <div class="bg-white p-6 rounded-3xl shadow-md border border-gray-100">
      <h4 class="font-black text-gray-800 mb-4 flex items-center gap-2">
        📚 MINHA ACADEMIA LICEU
      </h4>
      <ul class="space-y-3">
        <li class="flex items-center gap-3 text-sm p-2 bg-gray-50 rounded-lg">
          <span class="bg-blue-100 p-1 rounded">🎥</span>
          <span>Manifesto Liceu 6.0</span>
          <span class="ml-auto text-green-500 font-bold">✓</span>
        </li>
        <li class="flex items-center gap-3 text-sm p-2 border-l-4 border-yellow-400">
          <span class="bg-yellow-100 p-1 rounded">⚡</span>
          <span>Novas NBRs de Incêndio</span>
          <button class="ml-auto bg-yellow-400 text-[10px] px-2 py-1 rounded font-bold">ASSISTIR</button>
        </li>
      </ul>
    </div>

    <!-- CARD 3: CLUBE DE BENEFÍCIOS -->
    <div class="bg-white p-6 rounded-3xl shadow-md border border-gray-100">
      <h4 class="font-black text-gray-800 mb-4 flex items-center gap-2">
        🎁 MEUS CONVÊNIOS
      </h4>
      <div class="grid grid-cols-2 gap-2 text-[10px] font-bold uppercase">
        <div class="bg-green-50 text-green-700 p-3 rounded-xl text-center border border-green-100">
          Saúde <br> Porto Seguro
        </div>
        <div class="bg-purple-50 text-purple-700 p-3 rounded-xl text-center border border-purple-100">
          Gympass <br> Ativo
        </div>
      </div>
      <button class="w-full mt-4 text-xs font-bold text-indigo-600 underline">Ver todos os parceiros</button>
    </div>

  </div>
</template>
