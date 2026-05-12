<template>
  <div
    class="w-full h-full relative group cursor-pointer overflow-hidden transition-all duration-300 hover:ring-2 hover:ring-dunhuang-blue/30 min-h-[200px]"
    :class="displaySrc ? '' : 'flex items-center justify-center bg-dunhuang-bg'"
    @click="trigger"
  >
    <img
      v-if="displaySrc"
      :src="displaySrc"
      :alt="nameZh"
      class="w-full h-full object-cover block"
    />
    <div
      v-else-if="nameZh"
      class="text-5xl font-bold text-dunhuang-blue/30 font-serif"
    >
      {{ nameZh.charAt(0) }}
    </div>
    <svg
      v-else
      class="w-16 h-16 text-dunhuang-text/15"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="1.5"
        d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
      />
    </svg>
    <div
      class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
    >
      <span class="text-white text-sm font-medium">{{
        displaySrc ? "更换图片" : "选择图片"
      }}</span>
    </div>
    <input
      ref="inputRef"
      type="file"
      accept="image/*"
      class="hidden"
      @change="onFileChange"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";

const props = defineProps<{
  imageUrl?: string | null;
  nameZh?: string;
}>();

const emit = defineEmits<{
  select: [file: File | null];
}>();

const inputRef = ref<HTMLInputElement | null>(null);
const localPreview = ref<string | null>(null);

const displaySrc = computed(() => localPreview.value || props.imageUrl || null);

const trigger = () => {
  inputRef.value?.click();
};

const onFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0] ?? null;
  if (localPreview.value) {
    URL.revokeObjectURL(localPreview.value);
  }
  localPreview.value = file ? URL.createObjectURL(file) : null;
  emit("select", file);
};

const reset = () => {
  if (localPreview.value) {
    URL.revokeObjectURL(localPreview.value);
    localPreview.value = null;
  }
  if (inputRef.value) {
    inputRef.value.value = "";
  }
};

defineExpose({ reset });
</script>
