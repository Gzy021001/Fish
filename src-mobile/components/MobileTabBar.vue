<template>
  <nav
    class="fixed bottom-0 inset-x-0 z-40 h-16 px-4 pb-[env(safe-area-inset-bottom)] bg-[#f5ead7] border-t border-[#d8c1a0] flex items-center justify-around"
  >
    <RouterLink v-slot="{ isActive, navigate }" to="/dashboard" custom>
      <button
        class="rounded-full px-3 py-1.5 text-sm transition-opacity active:opacity-70"
        :class="isActive ? 'bg-[#8b6914] text-white' : 'text-[#6d4f32]'"
        @click="navigate"
      >
        首页
      </button>
    </RouterLink>
    <RouterLink v-slot="{ isActive, navigate }" to="/billing" custom>
      <button
        class="rounded-full px-3 py-1.5 text-sm transition-opacity active:opacity-70"
        :class="isActive ? 'bg-[#8b6914] text-white' : 'text-[#6d4f32]'"
        @click="navigate"
      >
        账单
      </button>
    </RouterLink>
    <RouterLink v-slot="{ isActive, navigate }" to="/species" custom>
      <button
        class="rounded-full px-3 py-1.5 text-sm transition-opacity active:opacity-70"
        :class="isActive ? 'bg-[#8b6914] text-white' : 'text-[#6d4f32]'"
        @click="navigate"
      >
        品种
      </button>
    </RouterLink>
  </nav>
</template>
