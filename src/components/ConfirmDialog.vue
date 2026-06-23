<template>
  <Transition name="modal-backdrop">
    <div
      v-if="show"
      class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-[70]"
      @click="$emit('cancel')"
    >
      <Transition name="modal" appear>
        <div
          v-if="show"
          role="dialog"
          aria-modal="true"
          aria-labelledby="confirm-dialog-title"
          class="bg-white rounded-2xl shadow-2xl border-t-4 border-t-dunhuang-red border-dunhuang-yellow w-full max-w-sm p-6 relative overflow-hidden"
          @click.stop
          @keydown.escape="$emit('cancel')"
          @keydown.enter="$emit('confirm')"
        >
          <div class="flex items-center gap-3 mb-4">
            <div
              class="w-10 h-10 rounded-full bg-dunhuang-red/10 flex items-center justify-center text-dunhuang-red shrink-0"
            >
              <svg
                class="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <h3 id="confirm-dialog-title" class="text-lg font-serif text-dunhuang-blue font-bold">
              {{ title }}
            </h3>
          </div>
          <div class="text-dunhuang-text/70 mb-6 pl-13 text-sm">
            <slot />
          </div>
          <div class="flex justify-end gap-3">
            <button
              @click="$emit('cancel')"
              class="px-4 py-2 rounded text-sm transition-colors text-dunhuang-text/70 hover:bg-dunhuang-yellow/20 border border-dunhuang-yellow/50"
            >
              取消
            </button>
            <button
              @click="$emit('confirm')"
              class="px-4 py-2 rounded text-sm transition-colors bg-dunhuang-red text-white hover:bg-dunhuang-red/90 shadow-sm"
            >
              确定删除
            </button>
          </div>
        </div>
      </Transition>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { watch, nextTick } from "vue";

const props = defineProps<{
  show: boolean;
  title?: string;
}>();

const emit = defineEmits<{
  confirm: [];
  cancel: [];
}>();

watch(() => props.show, async (val) => {
  if (val) {
    await nextTick();
    const el = document.querySelector<HTMLElement>('[role="dialog"]');
    el?.focus();
  }
});
</script>
