<template>
  <div
    class="inline-flex items-center gap-1 p-1 rounded-full bg-dunhuang-bg/70 border border-dunhuang-yellow/25 w-fit"
  >
    <button
      v-for="opt in options"
      :key="opt.value"
      type="button"
      @click="toggle(opt.value)"
      :class="[
        'h-9 px-4 rounded-full text-sm font-medium transition-all duration-200 whitespace-nowrap',
        isSelected(opt.value)
          ? 'bg-dunhuang-blue text-white shadow-md shadow-dunhuang-blue/20'
          : 'text-dunhuang-text/50 hover:text-dunhuang-blue hover:bg-white hover:shadow-sm',
      ]"
    >
      {{ opt.label }}
    </button>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const options = [
  { value: '支付宝', label: '支付宝' },
  { value: '微信', label: '微信' },
  { value: '随喜放生', label: '随喜放生' },
]

const isSelected = (value: string) => props.modelValue === value

const toggle = (value: string) => {
  emit('update:modelValue', props.modelValue === value ? '' : value)
}
</script>
