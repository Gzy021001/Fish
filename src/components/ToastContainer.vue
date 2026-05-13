<template>
  <Teleport to="body">
    <div class="fixed top-6 right-6 z-[9999] flex flex-col items-end gap-3 pointer-events-none">
      <TransitionGroup name="toast">
        <div
          v-for="t in toasts"
          :key="t.id"
          class="pointer-events-auto w-[340px] rounded-2xl shadow-2xl overflow-hidden"
          :class="bgClass(t.type)"
          @mouseenter="hoveredId = t.id"
          @mouseleave="hoveredId = null"
        >
          <div class="flex items-start gap-3 px-4 py-3.5">
            <div
              class="shrink-0 mt-0.5 w-6 h-6 rounded-full flex items-center justify-center"
              :class="iconBgClass(t.type)"
            >
              <svg v-if="t.type === 'success'" class="w-3.5 h-3.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              <svg v-else-if="t.type === 'error'" class="w-3.5 h-3.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
              <svg v-else-if="t.type === 'warning'" class="w-3.5 h-3.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
              <svg v-else class="w-3.5 h-3.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="16" x2="12" y2="12" />
                <line x1="12" y1="8" x2="12.01" y2="8" />
              </svg>
            </div>

            <div class="flex-1 min-w-0 pt-0.5">
              <p class="text-xs font-bold tracking-wider uppercase mb-0.5" :class="labelClass(t.type)">
                {{ typeLabel(t.type) }}
              </p>
              <p class="text-sm leading-snug" :class="textClass(t.type)">
                {{ t.message }}
              </p>
            </div>

            <button
              type="button"
              class="shrink-0 w-5 h-5 rounded-full flex items-center justify-center mt-0.5 transition-colors"
              :class="closeClass(t.type)"
              @click="removeToast(t.id)"
            >
              <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          <div class="h-0.5 w-full" :class="barTrackClass(t.type)">
            <div
              class="h-full origin-left animate-shrink-bar"
              :class="barFillClass(t.type)"
              :style="{ animationDuration: TOAST_DURATION + 'ms', animationPlayState: hoveredId === t.id ? 'paused' : 'running' }"
            />
          </div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from "vue"
import { useToast, TOAST_DURATION } from "../composables/useToast"

const { toasts, remove } = useToast()

const hoveredId = ref<number | null>(null)

const removeToast = (id: number) => remove(id)

const typeLabel = (type: string) => {
  const map: Record<string, string> = {
    success: "成功",
    error: "错误",
    warning: "提醒",
    info: "消息",
  }
  return map[type] || type
}

const bgClass = (type: string) => ({
  success: "bg-dunhuang-card border border-dunhuang-green/20",
  error: "bg-dunhuang-card border border-red-300/30",
  warning: "bg-dunhuang-card border border-dunhuang-orange/20",
  info: "bg-dunhuang-card border border-dunhuang-blue/15",
}[type] || "bg-dunhuang-card border border-dunhuang-blue/15")

const iconBgClass = (type: string) => ({
  success: "bg-dunhuang-green",
  error: "bg-red-500",
  warning: "bg-dunhuang-orange",
  info: "bg-dunhuang-blue",
}[type] || "bg-dunhuang-blue")

const labelClass = (type: string) => ({
  success: "text-dunhuang-green",
  error: "text-red-500",
  warning: "text-dunhuang-orange",
  info: "text-dunhuang-blue",
}[type] || "text-dunhuang-blue")

const textClass = (type: string) => ({
  success: "text-dunhuang-text/80",
  error: "text-dunhuang-text/80",
  warning: "text-dunhuang-text/80",
  info: "text-dunhuang-text/80",
}[type] || "text-dunhuang-text/80")

const closeClass = (type: string) => ({
  success: "text-dunhuang-text/20 hover:text-dunhuang-green hover:bg-dunhuang-green/8",
  error: "text-dunhuang-text/20 hover:text-red-500 hover:bg-red-50",
  warning: "text-dunhuang-text/20 hover:text-dunhuang-orange hover:bg-dunhuang-orange/8",
  info: "text-dunhuang-text/20 hover:text-dunhuang-blue hover:bg-dunhuang-blue/8",
}[type] || "text-dunhuang-text/20 hover:text-dunhuang-blue hover:bg-dunhuang-blue/8")

const barTrackClass = (type: string) => ({
  success: "bg-dunhuang-green/10",
  error: "bg-red-100",
  warning: "bg-dunhuang-orange/10",
  info: "bg-dunhuang-blue/5",
}[type] || "bg-dunhuang-blue/5")

const barFillClass = (type: string) => ({
  success: "bg-dunhuang-green/60",
  error: "bg-red-400/60",
  warning: "bg-dunhuang-orange/60",
  info: "bg-dunhuang-blue/50",
}[type] || "bg-dunhuang-blue/50")
</script>

<style scoped>
.animate-shrink-bar {
  animation: shrink-bar linear forwards;
}

@keyframes shrink-bar {
  from {
    width: 100%;
  }
  to {
    width: 0%;
  }
}

.toast-enter-active {
  transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.toast-leave-active {
  transition: all 0.2s ease-in;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(60px) scale(0.92);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(60px) scale(0.92);
}
</style>
