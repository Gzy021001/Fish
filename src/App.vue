<template>
  <SpeedInsights />
  <router-view />
  <ToastContainer />
</template>

<script setup lang="ts">
import { SpeedInsights } from "@vercel/speed-insights/vue";
import ToastContainer from "./components/ToastContainer.vue";
</script>

<style>
#app {
  min-height: 100vh;
  width: 100%;
}
</style>
