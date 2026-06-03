<template>
  <div class="flex items-center bg-white border border-dunhuang-blue/30 rounded-lg px-3 py-1.5 shadow-sm transition-colors hover:border-dunhuang-blue/50 focus-within:border-dunhuang-blue focus-within:ring-2 focus-within:ring-dunhuang-blue/20">
    <button type="button" @click="$emit('search')" class="text-dunhuang-blue hover:text-dunhuang-blue/70 transition-colors shrink-0">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" x2="16.65" y1="21" y2="16.65"></line>
      </svg>
    </button>
    <input
      type="text"
      :value="modelValue"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      :placeholder="placeholder"
      @keydown.enter="$emit('search')"
      class="bg-transparent border-none text-sm text-dunhuang-blue font-medium focus:outline-none focus:ring-0 p-0 w-40 ml-2"
    />
    <button
      v-if="modelValue"
      @click="$emit('clear')"
      class="text-dunhuang-text/40 hover:text-dunhuang-red text-sm leading-none px-1"
    >✕</button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: string
  placeholder?: string
}>()

defineEmits<{
  "update:modelValue": [value: string]
  search: []
  clear: []
}>()
</script>
