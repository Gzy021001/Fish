<template>
  <SpeedInsights />
  <router-view />
</template>

<script setup lang="ts">
import { SpeedInsights } from "@vercel/speed-insights/vue";
</script>

<style>
#app {
  min-height: 100vh;
  width: 100%;
}
</style>
