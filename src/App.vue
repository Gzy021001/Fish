<template>
  <router-view />
  <ToastContainer />
</template>

<script setup lang="ts">
import ToastContainer from "./components/ToastContainer.vue";
</script>

<style>
#app {
  min-height: 100vh;
  width: 100%;
}
</style>
