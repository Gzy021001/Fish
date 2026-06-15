<template>
  <div>
    <button
      type="button"
      class="w-full rounded-xl border border-[#d8c1a0] bg-white px-3 py-2.5 text-left text-sm text-[#5c4033] outline-none focus:border-[#8b6914] flex items-center gap-2"
      @click="openPicker"
    >
      <svg class="h-4 w-4 shrink-0 text-[#b8a68a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
        <line x1="16" y1="2" x2="16" y2="6" />
        <line x1="8" y1="2" x2="8" y2="6" />
        <line x1="3" y1="10" x2="21" y2="10" />
      </svg>
      <span :class="!modelValue ? 'text-[#b8a68a]' : ''">
        {{ modelValue || placeholder }}
      </span>
      <button
        v-if="modelValue && clearable"
        type="button"
        class="ml-auto shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-[#b8a68a] active:text-red-500 active:bg-red-50"
        @click.stop="clear"
      >
        <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="3">
          <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </button>

    <Transition name="sheet">
      <div v-if="open" class="fixed inset-0 z-[100] flex flex-col bg-black/20" @click.self="open = false">
        <div class="mt-auto flex flex-col rounded-t-3xl bg-[#f7efe2] shadow-2xl">
          <div class="shrink-0 flex items-center justify-between border-b border-[#ead9bc] px-5 py-4">
            <button
              type="button"
              class="text-sm text-[#8a6b4a] active:opacity-70"
              @click="open = false"
            >
              取消
            </button>
            <h2 class="text-base font-semibold text-[#5c4033]">{{ title }}</h2>
            <button
              type="button"
              class="text-sm font-medium text-[#8b6914] active:opacity-70"
              @click="confirm"
            >
              确定
            </button>
          </div>

          <div class="relative flex h-56 select-none overflow-hidden">
            <div
              class="pointer-events-none absolute left-3 right-3 top-1/2 z-10 h-10 -translate-y-1/2 rounded-lg border-y border-[#d8c1a0] bg-[#8b6914]/5"
            ></div>
            <div
              class="pointer-events-none absolute inset-y-0 left-3 right-3 z-10"
              style="background: linear-gradient(to bottom, #f7efe2 0%, transparent 30%, transparent 70%, #f7efe2 100%)"
            ></div>

            <div
              ref="yearCol"
              class="flex-1 overflow-y-auto overscroll-contain scrollbar-hide"
              style="-webkit-overflow-scrolling: touch"
              @scroll.passive="onYearScroll"
            >
              <div :style="{ padding: `${padTop}px 0 ${padBottom}px 0` }">
                <div
                  v-for="(y, yi) in yearRange"
                  :key="y"
                  class="h-10 flex items-center justify-center cursor-pointer"
                  :class="y === selYear
                    ? 'text-base font-semibold text-[#8b6914]'
                    : 'text-xs text-[#b8a68a]'"
                  @mousedown.prevent
                  @touchstart.prevent="tapYear(yi)"
                >
                  {{ y }}年
                </div>
              </div>
            </div>

            <div
              ref="monthCol"
              class="flex-1 overflow-y-auto overscroll-contain scrollbar-hide"
              style="-webkit-overflow-scrolling: touch"
              @scroll.passive="onMonthScroll"
            >
              <div :style="{ padding: `${padTop}px 0 ${padBottom}px 0` }">
                <div
                  v-for="m in 12"
                  :key="m"
                  class="h-10 flex items-center justify-center cursor-pointer"
                  :class="m === selMonth
                    ? 'text-base font-semibold text-[#8b6914]'
                    : 'text-xs text-[#b8a68a]'"
                  @mousedown.prevent
                  @touchstart.prevent="tapMonth(m - 1)"
                >
                  {{ m }}月
                </div>
              </div>
            </div>

            <div
              ref="dayCol"
              class="flex-1 overflow-y-auto overscroll-contain scrollbar-hide"
              style="-webkit-overflow-scrolling: touch"
              @scroll.passive="onDayScroll"
            >
              <div :style="{ padding: `${padTop}px 0 ${padBottom}px 0` }">
                <div
                  v-for="d in maxDay"
                  :key="d"
                  class="h-10 flex items-center justify-center cursor-pointer"
                  :class="d === selDay
                    ? 'text-base font-semibold text-[#8b6914]'
                    : 'text-xs text-[#b8a68a]'"
                  @mousedown.prevent
                  @touchstart.prevent="tapDay(d - 1)"
                >
                  {{ d }}日
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, nextTick } from 'vue'

const props = withDefaults(defineProps<{
  modelValue: string
  placeholder?: string
  title?: string
  clearable?: boolean
}>(), {
  placeholder: '请选择日期',
  title: '选择日期',
  clearable: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const ITEM_HEIGHT = 40
const COL_HEIGHT = 224
const PAD_BLOCKS = Math.floor(COL_HEIGHT / ITEM_HEIGHT / 2)
const padTop = PAD_BLOCKS * ITEM_HEIGHT
const padBottom = PAD_BLOCKS * ITEM_HEIGHT

const thisYear = new Date().getFullYear()
const YEAR_START = thisYear - 15

const yearRange = computed(() => {
  const years: number[] = []
  for (let y = YEAR_START; y <= thisYear + 5; y++) {
    years.push(y)
  }
  return years
})

const open = ref(false)
const selYear = ref(new Date().getFullYear())
const selMonth = ref(new Date().getMonth() + 1)
const selDay = ref(new Date().getDate())

const yearCol = ref<HTMLDivElement | null>(null)
const monthCol = ref<HTMLDivElement | null>(null)
const dayCol = ref<HTMLDivElement | null>(null)

let snapTimer: ReturnType<typeof setTimeout> | null = null
let initDone = false

const maxDay = computed(() => {
  return new Date(selYear.value, selMonth.value, 0).getDate()
})

watch([selYear, selMonth], () => {
  if (selDay.value > maxDay.value) {
    selDay.value = maxDay.value
    nextTick(() => snapTo(dayCol.value, selDay.value - 1, false))
  }
})

// 纯数学计算：根据 scrollTop 得出中心项索引（无 DOM 查询）
const indexFromScroll = (el: HTMLElement): number => {
  const raw = (el.scrollTop + padTop) / ITEM_HEIGHT
  return Math.round(raw)
}

// 纯数学定位
const snapTo = (el: HTMLDivElement | null, idx: number, animate = true) => {
  if (!el) return
  const target = idx * ITEM_HEIGHT
  if (!animate) {
    el.style.scrollBehavior = 'auto'
  }
  el.scrollTop = target
  if (!animate) {
    requestAnimationFrame(() => { el.style.scrollBehavior = '' })
  }
}

const scheduleSnap = () => {
  if (snapTimer) clearTimeout(snapTimer)
  snapTimer = setTimeout(() => {
    snapTo(yearCol.value, yearRange.value.indexOf(selYear.value))
    snapTo(monthCol.value, selMonth.value - 1)
    snapTo(dayCol.value, selDay.value - 1)
  }, 300)
}

const onYearScroll = () => {
  if (!initDone || !yearCol.value) return
  selYear.value = yearRange.value[indexFromScroll(yearCol.value)] || selYear.value
  scheduleSnap()
}

const onMonthScroll = () => {
  if (!initDone || !monthCol.value) return
  selMonth.value = indexFromScroll(monthCol.value) + 1
  scheduleSnap()
}

const onDayScroll = () => {
  if (!initDone || !dayCol.value) return
  selDay.value = indexFromScroll(dayCol.value) + 1
  scheduleSnap()
}

const tapYear = (yi: number) => {
  selYear.value = yearRange.value[yi] || selYear.value
  snapTo(yearCol.value, yi)
}

const tapMonth = (mi: number) => {
  selMonth.value = mi + 1
  snapTo(monthCol.value, mi)
}

const tapDay = (di: number) => {
  selDay.value = di + 1
  snapTo(dayCol.value, di)
}

const formatDate = (y: number, m: number, d: number) => {
  return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
}

const confirm = () => {
  emit('update:modelValue', formatDate(selYear.value, selMonth.value, selDay.value))
  open.value = false
}

const clear = () => {
  emit('update:modelValue', '')
}

const openPicker = () => {
  open.value = true
}

const scrollToInit = async (y: number, m: number, d: number) => {
  initDone = false
  selYear.value = y
  selMonth.value = m
  selDay.value = Math.min(d, new Date(y, m, 0).getDate())
  await nextTick()
  await new Promise(r => setTimeout(r, 20))
  snapTo(yearCol.value, y - yearRange.value[0], false)
  snapTo(monthCol.value, m - 1, false)
  snapTo(dayCol.value, selDay.value - 1, false)
  await nextTick()
  initDone = true
}

watch(open, async (isOpen) => {
  if (isOpen) {
    if (props.modelValue) {
      const parts = props.modelValue.split('-')
      if (parts.length === 3) {
        await scrollToInit(Number(parts[0]), Number(parts[1]), Number(parts[2]))
      } else {
        const d = new Date()
        await scrollToInit(d.getFullYear(), d.getMonth() + 1, d.getDate())
      }
    } else {
      const d = new Date()
      await scrollToInit(d.getFullYear(), d.getMonth() + 1, d.getDate())
    }
  }
})
</script>
