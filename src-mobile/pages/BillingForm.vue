<template>
  <section class="p-4 space-y-4">
    <div class="flex items-center justify-between gap-3">
      <div class="flex items-center gap-3 min-w-0">
        <button
          class="rounded-full border border-[#d8c1a0] bg-white/80 px-3 py-1.5 text-sm text-[#6d4f32] active:opacity-70 shrink-0"
          @click="goBack"
        >
          返回
        </button>
        <h1 class="truncate text-xl font-serif text-[#6d4f32]">
          {{ isEdit ? '编辑账单' : '记一笔' }}
        </h1>
      </div>
    </div>
    
    <div class="rounded-2xl bg-white/90 p-4 shadow-sm">
      <p class="text-sm text-[#8a6b4a]">表单内容占位</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => route.name === 'MobileBillingEdit')

const goBack = () => {
  router.back()
}
</script>