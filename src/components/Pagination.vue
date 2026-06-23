<template>
  <div class="flex items-center gap-4">
    <!-- 每页条数下拉框 (自定义下拉样式) -->
    <div class="flex items-center gap-2" v-if="showPageSizeSelect" ref="dropdownRef">
      <div class="relative group">
        <button
          type="button"
          @click.stop="isOpen = !isOpen"
          class="h-8 pl-3 pr-8 rounded-lg border border-dunhuang-yellow/30 text-sm text-dunhuang-text font-medium bg-white/50 backdrop-blur shadow-sm hover:border-dunhuang-yellow/60 focus:outline-none focus:border-dunhuang-blue focus:ring-2 focus:ring-dunhuang-blue/20 transition-all cursor-pointer flex items-center justify-between min-w-[80px]"
        >
          <span>{{ pageSize }}条/页</span>
        </button>
        
        <div class="absolute inset-y-0 right-0 flex items-center pr-2.5 pointer-events-none text-dunhuang-text/40 group-hover:text-dunhuang-blue/60 transition-colors">
          <svg class="w-4 h-4 transition-transform duration-200" :class="{ 'rotate-180': isOpen }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </div>

        <Transition name="fade-down">
          <div 
            v-if="isOpen" 
            class="absolute bottom-full mb-1.5 left-0 w-full min-w-[80px] bg-white rounded-lg shadow-lg border border-dunhuang-yellow/20 py-1 z-50 overflow-hidden"
          >
            <button
              v-for="size in [10, 20, 30, 40, 50]"
              :key="size"
              @click.stop="handleSelect(size)"
              class="w-full text-center px-3 py-1.5 text-sm transition-colors"
              :class="size === pageSize ? 'bg-dunhuang-blue/5 text-dunhuang-blue font-bold' : 'text-dunhuang-text/70 hover:bg-dunhuang-yellow/10 hover:text-dunhuang-blue'"
            >
              {{ size }}条/页
            </button>
          </div>
        </Transition>
      </div>
    </div>

    <!-- 分页控件 -->
    <div class="flex items-center gap-0.5" v-if="totalPages > 1">
      <!-- 首页 -->
      <button
        @click="$emit('update:currentPage', 1)"
        :disabled="currentPage === 1"
        class="group h-8 w-8 flex items-center justify-center rounded-full disabled:opacity-20 disabled:cursor-not-allowed transition-colors"
      >
        <svg class="w-4 h-4 text-dunhuang-text/40 group-hover:text-dunhuang-blue transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
        </svg>
      </button>
      <!-- 上一页 -->
      <button
        @click="$emit('update:currentPage', currentPage - 1)"
        :disabled="currentPage === 1"
        class="group h-8 w-8 flex items-center justify-center rounded-full mr-2 disabled:opacity-20 disabled:cursor-not-allowed transition-colors"
      >
        <svg class="w-4 h-4 text-dunhuang-text/40 group-hover:text-dunhuang-blue transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      <!-- 页码 -->
      <div class="flex items-center gap-0.5 bg-dunhuang-bg/50 rounded-full px-1 py-0.5">
        <button
          v-for="page in displayedPages"
          :key="page"
          @click="$emit('update:currentPage', page)"
          :class="[
            'h-7 w-7 flex items-center justify-center rounded-full text-xs font-medium transition-all duration-200',
            currentPage === page
              ? 'bg-white text-dunhuang-blue shadow-sm ring-1 ring-black/5'
              : 'text-dunhuang-text/40 hover:text-dunhuang-text/70',
          ]"
        >
          {{ page }}
        </button>
      </div>

      <!-- 下一页 -->
      <button
        @click="$emit('update:currentPage', currentPage + 1)"
        :disabled="currentPage === totalPages"
        class="group h-8 w-8 flex items-center justify-center rounded-full ml-2 disabled:opacity-20 disabled:cursor-not-allowed transition-colors"
      >
        <svg class="w-4 h-4 text-dunhuang-text/40 group-hover:text-dunhuang-blue transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
        </svg>
      </button>
      <!-- 末页 -->
      <button
        @click="$emit('update:currentPage', totalPages)"
        :disabled="currentPage === totalPages"
        class="group h-8 w-8 flex items-center justify-center rounded-full disabled:opacity-20 disabled:cursor-not-allowed transition-colors"
      >
        <svg class="w-4 h-4 text-dunhuang-text/40 group-hover:text-dunhuang-blue transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
        </svg>
      </button>

      <!-- 跳转 -->
      <div class="flex items-center gap-1 ml-3">
        <span class="text-[11px] text-dunhuang-text/25">跳至</span>
        <input
          v-model.number="jumpInput"
          type="number"
          :min="1"
          :max="totalPages"
          class="w-10 h-7 rounded-full text-center text-xs text-dunhuang-text/60 bg-dunhuang-bg/50 focus:outline-none focus:bg-white focus:ring-1 focus:ring-dunhuang-blue/20 transition-all [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
          @keydown.enter="doJump"
          @blur="doJump"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue"

const props = defineProps<{
  currentPage: number
  totalPages: number
  pageSize?: number
  showPageSizeSelect?: boolean
}>()

const emit = defineEmits<{
  "update:currentPage": [page: number]
  "update:pageSize": [size: number]
}>()

const jumpInput = ref<number | null>(null)
const isOpen = ref(false)
const dropdownRef = ref<HTMLElement | null>(null)

const handleSelect = (size: number) => {
  emit('update:pageSize', size)
  emit('update:currentPage', 1) // 切换条数时自动回到第一页
  isOpen.value = false
}

const handleClickOutside = (event: MouseEvent) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target as Node)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

const displayedPages = computed(() => {
  const pages = []
  let start = Math.max(1, props.currentPage - 2)
  let end = Math.min(props.totalPages, start + 4)

  if (end - start < 4) {
    start = Math.max(1, end - 4)
  }

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
})

const doJump = () => {
  const val = jumpInput.value
  if (val == null || val < 1) {
    jumpInput.value = null
    return
  }
  const target = Math.min(Math.floor(val), props.totalPages)
  jumpInput.value = target
  emit("update:currentPage", target)
}
</script>

<style scoped>
.fade-down-enter-active,
.fade-down-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-down-enter-from,
.fade-down-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>
