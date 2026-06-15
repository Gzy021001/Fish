<template>
  <div class="min-h-screen flex flex-col bg-dunhuang-bg">
    <header class="safe-top px-4 pt-3 pb-3 bg-[#efe3cf] border-b border-[#d8c1a0]">
      <h1 class="text-lg font-serif tracking-[0.08em] text-[#6d4f32]">
        Fish Mobile
      </h1>
    </header>

    <main class="flex-1 overflow-y-auto pb-[calc(64px+env(safe-area-inset-bottom))]">
      <router-view />
    </main>

    <MobileTabBar />
  </div>
</template>

<script setup lang="ts">
import MobileTabBar from './MobileTabBar.vue'
</script>
