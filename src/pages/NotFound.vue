<template>
  <div class="min-h-screen flex items-center justify-center bg-dunhuang-bg">
    <div class="text-center space-y-6">
      <p class="text-8xl font-serif font-bold text-dunhuang-blue/20">404</p>
      <p class="text-lg text-dunhuang-text/60">页面未找到</p>
      <router-link
        to="/dashboard"
        class="inline-block px-6 py-2.5 rounded-xl bg-dunhuang-blue text-white text-sm font-medium hover:bg-dunhuang-blue/90 transition-colors"
      >
        返回首页
      </router-link>
    </div>
  </div>
</template>
