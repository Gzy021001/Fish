<template>
  <div ref="rootRef" class="relative">
    <button
      type="button"
      class="date-range-trigger"
      @click="toggle"
      :class="[
        'w-full flex items-center gap-2 transition-all duration-200 focus:outline-none group',
        variant === 'default' ? 'rounded-lg border' : 'rounded-md',
        variant === 'default'
          ? hasValue
            ? 'bg-white border-dunhuang-blue/30 text-dunhuang-blue shadow-sm shadow-dunhuang-blue/5 hover:border-dunhuang-blue/50'
            : 'bg-white/70 border-dunhuang-yellow/25 text-dunhuang-text/50 hover:border-dunhuang-yellow/40 hover:text-dunhuang-text/70 hover:bg-white'
          : hasValue
            ? 'text-dunhuang-blue hover:bg-dunhuang-blue/5'
            : 'text-dunhuang-text/50 hover:bg-black/5',
        'h-9 px-3 text-sm',
      ]"
    >
      <svg
        class="shrink-0 transition-colors"
        :class="
          hasValue
            ? 'text-dunhuang-blue'
            : 'text-dunhuang-yellow/60 group-hover:text-dunhuang-blue/60'
        "
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
        <line x1="16" y1="2" x2="16" y2="6" />
        <line x1="8" y1="2" x2="8" y2="6" />
        <line x1="3" y1="10" x2="21" y2="10" />
      </svg>

      <span class="text-sm font-medium truncate tabular-nums">{{
        displayText
      }}</span>

      <button
        v-if="hasValue && clearable"
        type="button"
        @click.stop="clearRange"
        class="ml-auto shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-dunhuang-text/25 hover:text-dunhuang-red hover:bg-dunhuang-red/10 transition-colors"
        title="清除日期范围"
      >
        <svg
          class="w-3 h-3"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
        >
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </button>

    <Transition :name="dropUp ? 'range-drop-up' : 'range-drop'">
      <div
        v-if="open"
        class="absolute z-50"
        :class="[
          alignRight ? 'right-0' : 'left-0',
          dropUp ? 'bottom-full mb-1.5' : 'top-full mt-1.5',
        ]"
      >
        <div
          class="date-range-panel bg-white rounded-xl shadow-xl border border-dunhuang-yellow/20 w-[568px]"
          style="
            box-shadow:
              0 12px 36px rgba(92, 64, 51, 0.12),
              0 4px 12px rgba(92, 64, 51, 0.06);
          "
        >
          <div class="grid grid-cols-2 gap-2 p-3">
            <div v-for="(month, idx) in visibleMonths" :key="idx">
              <!-- 月份导航 -->
              <div class="flex items-center justify-between h-8 px-1">
                <div class="flex items-center gap-0.5">
                  <button
                    v-if="idx === 0"
                    type="button"
                    @click="shiftMonth(-12)"
                    class="w-7 h-7 rounded-md flex items-center justify-center text-dunhuang-text/35 hover:bg-dunhuang-yellow/10 hover:text-dunhuang-blue transition-colors"
                    title="上一年"
                  >
                    <svg
                      class="w-3.5 h-3.5"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                    >
                      <polyline points="11 17 6 12 11 7" />
                      <polyline points="18 17 13 12 18 7" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    @click="shiftMonth(-1)"
                    class="w-7 h-7 rounded-md flex items-center justify-center text-dunhuang-text/35 hover:bg-dunhuang-yellow/10 hover:text-dunhuang-blue transition-colors"
                    title="上个月"
                  >
                    <svg
                      class="w-3.5 h-3.5"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                    >
                      <polyline points="15 18 9 12 15 6" />
                    </svg>
                  </button>
                </div>

                <span class="text-sm font-serif font-bold text-dunhuang-blue">
                  {{ month.year }} 年 {{ month.month + 1 }} 月
                </span>

                <div class="flex items-center gap-0.5">
                  <button
                    type="button"
                    @click="shiftMonth(1)"
                    class="w-7 h-7 rounded-md flex items-center justify-center text-dunhuang-text/35 hover:bg-dunhuang-yellow/10 hover:text-dunhuang-blue transition-colors"
                    title="下个月"
                  >
                    <svg
                      class="w-3.5 h-3.5"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                    >
                      <polyline points="9 18 15 12 9 6" />
                    </svg>
                  </button>
                  <button
                    v-if="idx === 1"
                    type="button"
                    @click="shiftMonth(12)"
                    class="w-7 h-7 rounded-md flex items-center justify-center text-dunhuang-text/35 hover:bg-dunhuang-yellow/10 hover:text-dunhuang-blue transition-colors"
                    title="下一年"
                  >
                    <svg
                      class="w-3.5 h-3.5"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                    >
                      <polyline points="13 17 18 12 13 7" />
                      <polyline points="6 17 11 12 6 7" />
                    </svg>
                  </button>
                </div>
              </div>

              <!-- 星期 -->
              <div class="grid grid-cols-7 pt-1 pb-0.5">
                <span
                  v-for="(w, i) in weekHeaders"
                  :key="w"
                  class="text-center text-[11px] py-0.5"
                  :class="
                    i === 5 || i === 6
                      ? 'text-dunhuang-orange/60'
                      : 'text-dunhuang-text/30'
                  "
                  >{{ w }}</span
                >
              </div>

              <!-- 日期 -->
              <div class="grid grid-cols-7 gap-y-0.5">
                <button
                  v-for="day in month.days"
                  :key="day.dateStr"
                  type="button"
                  :disabled="!day.inMonth"
                  @click="pickDay(day)"
                  @mouseenter="hoverDay = day.dateStr"
                  @mouseleave="hoverDay = ''"
                  :class="[
                    'relative h-8 text-xs transition-colors duration-100 flex items-center justify-center',
                    !day.inMonth
                      ? 'text-dunhuang-text/15 cursor-default'
                      : isEdge(day.dateStr)
                        ? 'bg-dunhuang-blue text-white font-bold z-10'
                        : inRange(day.dateStr)
                          ? 'bg-dunhuang-blue/10 text-dunhuang-blue font-medium'
                          : isToday(day.dateStr)
                            ? 'text-dunhuang-orange font-bold'
                            : isWeekend(day)
                              ? 'text-dunhuang-orange/70 hover:bg-dunhuang-orange/10'
                              : 'text-dunhuang-text/70 hover:bg-dunhuang-bg hover:text-dunhuang-blue',
                    isEdge(day.dateStr) && day.inMonth
                      ? day.dateStr === activeRange?.from
                        ? 'rounded-l-md'
                        : 'rounded-r-md'
                      : '',
                  ]"
                >
                  {{ day.value }}
                </button>
              </div>
            </div>
          </div>

          <!-- 快捷范围 + 清除 -->
          <div
            class="flex items-center justify-between gap-2 px-3 py-2 border-t border-dunhuang-yellow/10 bg-dunhuang-card/80 rounded-b-xl"
          >
            <div class="flex items-center gap-1">
              <button
                v-for="preset in presets"
                :key="preset.key"
                type="button"
                @click="applyPreset(preset.key)"
                class="text-xs text-dunhuang-blue/70 hover:text-dunhuang-blue font-medium transition-colors px-2 py-1 rounded hover:bg-dunhuang-blue/5"
              >
                {{ preset.label }}
              </button>
            </div>
            <button
              v-if="hasValue"
              type="button"
              @click="clearRange"
              class="text-xs text-dunhuang-text/40 hover:text-dunhuang-red font-medium transition-colors px-2 py-1 rounded hover:bg-dunhuang-red/5 shrink-0"
            >
              清除
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from "vue";

const props = withDefaults(
  defineProps<{
    from: string;
    to: string;
    placeholder?: string;
    clearable?: boolean;
    variant?: "default" | "ghost";
    align?: "auto" | "left" | "right";
  }>(),
  {
    placeholder: "选择放生日期范围",
    clearable: true,
    variant: "default",
    align: "auto",
  },
);

const emit = defineEmits<{
  "update:from": [value: string];
  "update:to": [value: string];
  change: [range: { from: string; to: string }];
}>();

const rootRef = ref<HTMLElement | null>(null);
const open = ref(false);
const dropUp = ref(false);
const alignRight = ref(true);
const pickStart = ref("");
const hoverDay = ref("");
const today = new Date();
const viewYear = ref(today.getFullYear());
const viewMonth = ref(today.getMonth());

const weekHeaders = ["一", "二", "三", "四", "五", "六", "日"];
const presets = [
  { key: "last7", label: "近7天" },
  { key: "thisMonth", label: "本月" },
  { key: "lastMonth", label: "上月" },
] as const;

const pad = (n: number) => String(n).padStart(2, "0");
const fmt = (y: number, m: number, d: number) => `${y}-${pad(m)}-${pad(d)}`;
const todayStr = fmt(today.getFullYear(), today.getMonth() + 1, today.getDate());

const hasValue = computed(() => !!props.from || !!props.to);

const displayText = computed(() => {
  if (!hasValue.value) return props.placeholder;
  const from = props.from || "开始";
  const to = props.to || "结束";
  return `${from} - ${to}`;
});

const buildMonth = (year: number, month: number) => {
  const first = new Date(year, month, 1);
  const last = new Date(year, month + 1, 0);
  const startOffset = first.getDay() === 0 ? 6 : first.getDay() - 1;
  const days: {
    value: number;
    inMonth: boolean;
    dateStr: string;
  }[] = [];

  const prevLastDay = new Date(year, month, 0).getDate();
  for (let i = startOffset - 1; i >= 0; i--) {
    const d = prevLastDay - i;
    const pm = month === 0 ? 12 : month;
    const py = month === 0 ? year - 1 : year;
    days.push({ value: d, inMonth: false, dateStr: fmt(py, pm, d) });
  }
  for (let d = 1; d <= last.getDate(); d++) {
    days.push({ value: d, inMonth: true, dateStr: fmt(year, month + 1, d) });
  }
  let nextDay = 1;
  while (days.length < 42) {
    const nm = month + 2 > 12 ? 1 : month + 2;
    const ny = month + 2 > 12 ? year + 1 : year;
    days.push({
      value: nextDay,
      inMonth: false,
      dateStr: fmt(ny, nm, nextDay),
    });
    nextDay++;
  }
  return { year, month, days };
};

const visibleMonths = computed(() => {
  const first = buildMonth(viewYear.value, viewMonth.value);
  const nextMonth = viewMonth.value === 11 ? 0 : viewMonth.value + 1;
  const nextYear = viewMonth.value === 11 ? viewYear.value + 1 : viewYear.value;
  const second = buildMonth(nextYear, nextMonth);
  return [first, second];
});

const isToday = (dateStr: string) => dateStr === todayStr;

const isWeekend = (day: { dateStr: string }) => {
  const d = new Date(day.dateStr);
  const w = d.getDay();
  return w === 0 || w === 6;
};

const activeRange = computed(() => {
  if (pickStart.value) {
    const other = hoverDay.value || pickStart.value;
    return pickStart.value <= other
      ? { from: pickStart.value, to: other }
      : { from: other, to: pickStart.value };
  }
  if (props.from && props.to) return { from: props.from, to: props.to };
  if (props.from) return { from: props.from, to: props.from };
  return null;
});

const isEdge = (dateStr: string) => {
  const range = activeRange.value;
  if (!range) return false;
  return dateStr === range.from || dateStr === range.to;
};

const inRange = (dateStr: string) => {
  const range = activeRange.value;
  if (!range) return false;
  if (!props.from && !pickStart.value) return false;
  return dateStr > range.from && dateStr < range.to;
};

const openPicker = async () => {
  open.value = true;
  pickStart.value = "";
  const anchor = props.from || props.to;
  if (anchor) {
    const [y, m] = anchor.split("-").map(Number);
    viewYear.value = y;
    viewMonth.value = m - 1;
  } else {
    viewYear.value = today.getFullYear();
    viewMonth.value = today.getMonth();
  }
  await nextTick();
  if (rootRef.value) {
    const rect = rootRef.value.getBoundingClientRect();
    const panelHeight = 400;
    const panelWidth = 568;
    dropUp.value =
      window.innerHeight - rect.bottom < panelHeight + 8 &&
      rect.top > panelHeight + 8;
    if (props.align === "left") alignRight.value = false;
    else if (props.align === "right") alignRight.value = true;
    else
      alignRight.value =
        rect.left + panelWidth > window.innerWidth - 12 &&
        rect.right - panelWidth > 12;
  }
};

const toggle = () => {
  if (open.value) {
    open.value = false;
    pickStart.value = "";
  } else {
    openPicker();
  }
};

const emitRange = (from: string, to: string) => {
  emit("update:from", from);
  emit("update:to", to);
  emit("change", { from, to });
};

const pickDay = (day: { inMonth: boolean; dateStr: string }) => {
  if (!day.inMonth) return;
  if (!pickStart.value) {
    pickStart.value = day.dateStr;
    hoverDay.value = day.dateStr;
    return;
  }
  const from = pickStart.value <= day.dateStr ? pickStart.value : day.dateStr;
  const to = pickStart.value <= day.dateStr ? day.dateStr : pickStart.value;
  pickStart.value = "";
  emitRange(from, to);
  open.value = false;
};

const applyPreset = (key: "last7" | "thisMonth" | "lastMonth") => {
  const y = today.getFullYear();
  const m = today.getMonth();
  if (key === "last7") {
    const start = new Date(today);
    start.setDate(start.getDate() - 6);
    emitRange(
      fmt(start.getFullYear(), start.getMonth() + 1, start.getDate()),
      todayStr,
    );
  } else if (key === "thisMonth") {
    emitRange(
      fmt(y, m + 1, 1),
      fmt(y, m + 1, new Date(y, m + 1, 0).getDate()),
    );
  } else {
    const prev = new Date(y, m - 1, 1);
    const py = prev.getFullYear();
    const pm = prev.getMonth() + 1;
    emitRange(fmt(py, pm, 1), fmt(py, pm, new Date(py, pm, 0).getDate()));
  }
  open.value = false;
};

const clearRange = () => {
  pickStart.value = "";
  emitRange("", "");
  open.value = false;
};

const shiftMonth = (delta: number) => {
  const next = new Date(viewYear.value, viewMonth.value + delta, 1);
  viewYear.value = next.getFullYear();
  viewMonth.value = next.getMonth();
};

const handleClickOutside = (event: MouseEvent) => {
  if (rootRef.value && !rootRef.value.contains(event.target as Node)) {
    open.value = false;
    pickStart.value = "";
  }
};

onMounted(() => document.addEventListener("click", handleClickOutside));
onBeforeUnmount(() => document.removeEventListener("click", handleClickOutside));
</script>

<style scoped>
.range-drop-enter-active,
.range-drop-up-enter-active {
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.range-drop-leave-active,
.range-drop-up-leave-active {
  transition: all 0.15s ease-in;
}
.range-drop-enter-from {
  opacity: 0;
  transform: translateY(-8px) scale(0.96);
}
.range-drop-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
}
.range-drop-up-enter-from {
  opacity: 0;
  transform: translateY(8px) scale(0.96);
}
.range-drop-up-leave-to {
  opacity: 0;
  transform: translateY(4px) scale(0.98);
}
</style>
