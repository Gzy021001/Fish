<template>
  <div ref="rootRef" class="relative">
    <button
      type="button"
      @click="toggle"
      :class="[
        'w-full flex items-center gap-2.5 rounded-lg border transition-all duration-200 focus:outline-none group',
        size === 'sm' ? 'py-2 px-4 text-sm' : 'py-2.5 px-3 text-sm',
        hasValue
          ? 'bg-white border-dunhuang-blue/30 text-dunhuang-blue shadow-sm shadow-dunhuang-blue/5 hover:border-dunhuang-blue/50'
          : 'bg-dunhuang-bg border-dunhuang-yellow/50 text-dunhuang-text/40 hover:border-dunhuang-blue/40 hover:text-dunhuang-text/60 hover:bg-white',
      ]"
    >
      <svg
        class="shrink-0 transition-colors"
        :class="[
          hasValue
            ? 'text-dunhuang-blue'
            : 'text-dunhuang-text/25 group-hover:text-dunhuang-blue/50',
          size === 'sm' ? 'w-4 h-4' : 'w-[18px] h-[18px]',
        ]"
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

      <span class="text-sm font-medium truncate">
        {{ hasValue ? displayText : placeholder }}
      </span>

      <button
        v-if="hasValue && clearable"
        type="button"
        @click.stop="clear"
        class="ml-auto shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-dunhuang-text/30 hover:text-dunhuang-red hover:bg-dunhuang-red/10 transition-colors"
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

    <Transition :name="dropUp ? 'picker-drop-up' : 'picker-drop'">
      <div
        v-if="open"
        class="absolute z-50"
        :class="[
          placement === 'right' ? 'right-0' : 'left-0',
          dropUp ? 'bottom-full mb-1.5' : 'top-full mt-1.5',
        ]"
      >
        <div
          class="bg-white rounded-xl shadow-xl border border-dunhuang-yellow/20 overflow-hidden w-[256px]"
          style="
            box-shadow:
              0 8px 28px rgba(92, 64, 51, 0.1),
              0 3px 8px rgba(92, 64, 51, 0.05);
          "
        >
          <!-- 年份切换模式 -->
          <template v-if="mode === 'year'">
            <div
              class="flex items-center justify-between px-3 py-2 border-b border-dunhuang-yellow/10"
            >
              <button
                type="button"
                @click="prevYearPage"
                class="w-7 h-7 rounded-lg flex items-center justify-center text-dunhuang-text/40 hover:bg-dunhuang-yellow/10 hover:text-dunhuang-blue transition-colors"
              >
                <svg
                  class="w-4 h-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                >
                  <polyline points="15 18 9 12 15 6" />
                </svg>
              </button>
              <span class="text-sm font-serif font-bold text-dunhuang-blue"
                >{{ yearStart }} - {{ yearStart + 11 }}</span
              >
              <button
                type="button"
                @click="nextYearPage"
                class="w-7 h-7 rounded-lg flex items-center justify-center text-dunhuang-text/40 hover:bg-dunhuang-yellow/10 hover:text-dunhuang-blue transition-colors"
              >
                <svg
                  class="w-4 h-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                >
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </button>
            </div>
            <div class="grid grid-cols-4 gap-0.5 p-2">
              <button
                v-for="y in yearPage"
                :key="y"
                type="button"
                @click="pickYear(y)"
                :class="[
                  'py-1.5 rounded-md text-sm font-medium transition-colors',
                  y === viewYear
                    ? 'bg-dunhuang-blue text-white shadow-sm'
                    : y === today.getFullYear()
                      ? 'bg-dunhuang-blue/5 text-dunhuang-blue hover:bg-dunhuang-blue/10'
                      : 'text-dunhuang-text/60 hover:bg-dunhuang-bg hover:text-dunhuang-blue',
                ]"
              >
                {{ y }}
              </button>
            </div>
          </template>

          <!-- 月份切换模式 -->
          <template v-else-if="mode === 'month'">
            <div
              class="flex items-center justify-between px-3 py-2 border-b border-dunhuang-yellow/10"
            >
              <button
                type="button"
                @click="prevYear"
                class="w-7 h-7 rounded-lg flex items-center justify-center text-dunhuang-text/40 hover:bg-dunhuang-yellow/10 hover:text-dunhuang-blue transition-colors"
              >
                <svg
                  class="w-4 h-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                >
                  <polyline points="15 18 9 12 15 6" />
                </svg>
              </button>
              <button
                type="button"
                @click="mode = 'year'"
                class="text-sm font-serif font-bold text-dunhuang-blue hover:text-dunhuang-orange transition-colors px-2 py-0.5 rounded hover:bg-dunhuang-yellow/5"
              >
                {{ viewYear }}
              </button>
              <button
                type="button"
                @click="nextYear"
                class="w-7 h-7 rounded-lg flex items-center justify-center text-dunhuang-text/40 hover:bg-dunhuang-yellow/10 hover:text-dunhuang-blue transition-colors"
              >
                <svg
                  class="w-4 h-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                >
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </button>
            </div>
            <div class="grid grid-cols-4 gap-0.5 p-2">
              <button
                v-for="(m, idx) in monthLabels"
                :key="idx"
                type="button"
                @click="pickMonth(idx)"
                :class="[
                  'py-2 rounded-md text-sm font-medium transition-colors',
                  idx === viewMonth
                    ? 'bg-dunhuang-blue text-white shadow-sm'
                    : idx === today.getMonth() &&
                        viewYear === today.getFullYear()
                      ? 'bg-dunhuang-blue/5 text-dunhuang-blue hover:bg-dunhuang-blue/10'
                      : 'text-dunhuang-text/60 hover:bg-dunhuang-bg hover:text-dunhuang-blue',
                ]"
              >
                {{ m }}
              </button>
            </div>
          </template>

          <!-- 日历主面板 -->
          <template v-else>
            <!-- 头部：年月导航 -->
            <div
              class="flex items-center justify-between px-3 py-2 border-b border-dunhuang-yellow/10"
            >
              <button
                type="button"
                @click="prevMonth"
                class="w-7 h-7 rounded-lg flex items-center justify-center text-dunhuang-text/40 hover:bg-dunhuang-yellow/10 hover:text-dunhuang-blue transition-colors"
              >
                <svg
                  class="w-4 h-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                >
                  <polyline points="15 18 9 12 15 6" />
                </svg>
              </button>
              <div class="flex items-center gap-2">
                <button
                  type="button"
                  @click="mode = 'year'"
                  class="text-sm font-serif font-bold text-dunhuang-blue hover:text-dunhuang-orange transition-colors px-1.5 py-0.5 rounded hover:bg-dunhuang-yellow/5"
                >
                  {{ viewYear }}年
                </button>
                <button
                  type="button"
                  @click="mode = 'month'"
                  class="text-sm font-serif font-bold text-dunhuang-blue hover:text-dunhuang-orange transition-colors px-1.5 py-0.5 rounded hover:bg-dunhuang-yellow/5"
                >
                  {{ monthLabels[viewMonth] }}月
                </button>
              </div>
              <button
                type="button"
                @click="prevMonth(false)"
                class="w-7 h-7 rounded-lg flex items-center justify-center text-dunhuang-text/40 hover:bg-dunhuang-yellow/10 hover:text-dunhuang-blue transition-colors"
              >
                <svg
                  class="w-4 h-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                >
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </button>
            </div>

            <!-- 星期标题 -->
            <div class="grid grid-cols-7 px-2 pt-1.5 pb-0.5">
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

            <!-- 日期网格 -->
            <div class="grid grid-cols-7 px-2 pb-2">
              <button
                v-for="(day, idx) in calendarDays"
                :key="idx"
                type="button"
                @click="pickDay(day)"
                :disabled="!day.currentMonth"
                :class="[
                  'relative w-full aspect-square flex items-center justify-center text-xs rounded-md transition-all duration-150',
                  day.currentMonth
                    ? isToday(day) && !isSelected(day)
                      ? 'text-dunhuang-orange font-bold bg-dunhuang-orange/8 hover:bg-dunhuang-orange/15'
                      : isSelected(day)
                        ? 'bg-dunhuang-blue text-white font-bold shadow-sm'
                        : isWeekend(day)
                          ? 'text-dunhuang-orange/70 hover:bg-dunhuang-orange/8 hover:text-dunhuang-orange'
                          : 'text-dunhuang-text/70 hover:bg-dunhuang-bg hover:text-dunhuang-blue'
                    : 'text-dunhuang-text/15 cursor-default',
                  isToday(day) && isSelected(day)
                    ? 'ring-2 ring-dunhuang-blue/30 ring-offset-1 ring-offset-white'
                    : '',
                ]"
              >
                {{ day.value }}
              </button>
            </div>

            <!-- 底部：今天 & 清除 -->
            <div
              class="flex items-center justify-between px-3 py-2 border-t border-dunhuang-yellow/10 bg-dunhuang-card/80"
            >
              <button
                type="button"
                @click="goToToday"
                class="text-xs text-dunhuang-blue/60 hover:text-dunhuang-blue font-medium transition-colors px-2 py-1 rounded hover:bg-dunhuang-blue/5"
              >
                今天
              </button>
              <button
                v-if="hasValue && clearable"
                type="button"
                @click="clear"
                class="text-xs text-dunhuang-text/40 hover:text-dunhuang-red font-medium transition-colors px-2 py-1 rounded hover:bg-dunhuang-red/5"
              >
                清除日期
              </button>
            </div>
          </template>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from "vue";

const props = withDefaults(
  defineProps<{
    modelValue: string;
    placeholder?: string;
    size?: "sm" | "default";
    clearable?: boolean;
    placement?: "left" | "right";
  }>(),
  {
    placeholder: "请选择日期",
    size: "default",
    clearable: true,
    placement: "right",
  },
);

const emit = defineEmits<{
  "update:modelValue": [value: string];
}>();

const rootRef = ref<HTMLElement | null>(null);
const open = ref(false);
const dropUp = ref(false);
const mode = ref<"calendar" | "year" | "month">("calendar");
const viewYear = ref(new Date().getFullYear());
const viewMonth = ref(new Date().getMonth());
const yearStart = ref(Math.floor(new Date().getFullYear() / 12) * 12);

const weekHeaders = ["一", "二", "三", "四", "五", "六", "日"];
const monthLabels = [
  "1",
  "2",
  "3",
  "4",
  "5",
  "6",
  "7",
  "8",
  "9",
  "10",
  "11",
  "12",
];

const today = new Date();
const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

const hasValue = computed(() => !!props.modelValue);

const displayText = computed(() => {
  if (!props.modelValue) return "";
  const [y, m, d] = props.modelValue.split("-");
  if (!y || !m || !d) return props.modelValue;
  return `${parseInt(y)}年${parseInt(m)}月${parseInt(d)}日`;
});

const selectedDate = computed(() => {
  if (!props.modelValue) return null;
  const [y, m, d] = props.modelValue.split("-").map(Number);
  return { y, m, d };
});

const calendarDays = computed(() => {
  const firstDay = new Date(viewYear.value, viewMonth.value, 1);
  const lastDay = new Date(viewYear.value, viewMonth.value + 1, 0);
  const startDayOfWeek = firstDay.getDay();
  const adjustedStart = startDayOfWeek === 0 ? 6 : startDayOfWeek - 1;
  const totalDays = lastDay.getDate();

  const days: { value: number; currentMonth: boolean; dateStr: string }[] = [];

  const prevLastDay = new Date(viewYear.value, viewMonth.value, 0).getDate();
  for (let i = adjustedStart - 1; i >= 0; i--) {
    const d = prevLastDay - i;
    const m = viewMonth.value === 0 ? 12 : viewMonth.value;
    const y = viewMonth.value === 0 ? viewYear.value - 1 : viewYear.value;
    days.push({
      value: d,
      currentMonth: false,
      dateStr: `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`,
    });
  }

  for (let d = 1; d <= totalDays; d++) {
    days.push({
      value: d,
      currentMonth: true,
      dateStr: `${viewYear.value}-${String(viewMonth.value + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`,
    });
  }

  let nextDay = 1;
  while (days.length < 42) {
    const m = viewMonth.value + 2 > 12 ? 1 : viewMonth.value + 2;
    const y = viewMonth.value + 2 > 12 ? viewYear.value + 1 : viewYear.value;
    days.push({
      value: nextDay,
      currentMonth: false,
      dateStr: `${y}-${String(m).padStart(2, "0")}-${String(nextDay).padStart(2, "0")}`,
    });
    nextDay++;
  }

  return days;
});

const yearPage = computed(() => {
  const start = yearStart.value;
  return Array.from({ length: 12 }, (_, i) => start + i);
});

const isToday = (day: { dateStr: string; currentMonth: boolean }) =>
  day.dateStr === todayStr;

const isSelected = (day: { dateStr: string }) => {
  if (!selectedDate.value) return false;
  return day.dateStr === props.modelValue;
};

const isWeekend = (day: { currentMonth: boolean }) => {
  const pos = calendarDays.value.indexOf(day);
  return pos >= 0 && (pos % 7 === 5 || pos % 7 === 6);
};

const toggle = () => {
  if (open.value) {
    open.value = false;
    mode.value = "calendar";
  } else {
    openPicker();
  }
};

const openPicker = async () => {
  if (selectedDate.value) {
    viewYear.value = selectedDate.value.y;
    viewMonth.value = selectedDate.value.m - 1;
  } else {
    viewYear.value = today.getFullYear();
    viewMonth.value = today.getMonth();
  }
  mode.value = "calendar";
  open.value = true;
  await nextTick();
  if (rootRef.value) {
    const rect = rootRef.value.getBoundingClientRect();
    const panelHeight = 310;
    const spaceBelow = window.innerHeight - rect.bottom;
    dropUp.value = spaceBelow < panelHeight + 8 && rect.top > panelHeight + 8;
  }
};

const pickDay = (day: { currentMonth: boolean; dateStr: string }) => {
  if (!day.currentMonth) return;
  emit("update:modelValue", day.dateStr);
  open.value = false;
  mode.value = "calendar";
};

const prevMonth = (forward = true) => {
  if (forward) {
    if (viewMonth.value === 0) {
      viewMonth.value = 11;
      viewYear.value--;
    } else {
      viewMonth.value--;
    }
  } else {
    if (viewMonth.value === 11) {
      viewMonth.value = 0;
      viewYear.value++;
    } else {
      viewMonth.value++;
    }
  }
};

const prevYear = () => {
  viewYear.value--;
};
const nextYear = () => {
  viewYear.value++;
};

const prevYearPage = () => {
  yearStart.value -= 12;
};
const nextYearPage = () => {
  yearStart.value += 12;
};

const pickYear = (y: number) => {
  viewYear.value = y;
  mode.value = "month";
};

const pickMonth = (m: number) => {
  viewMonth.value = m;
  mode.value = "calendar";
};

const goToToday = () => {
  emit("update:modelValue", todayStr);
  open.value = false;
  mode.value = "calendar";
};

const clear = () => {
  emit("update:modelValue", "");
  open.value = false;
  mode.value = "calendar";
};

const handleClickOutside = (e: MouseEvent) => {
  if (rootRef.value && !rootRef.value.contains(e.target as Node)) {
    open.value = false;
    mode.value = "calendar";
  }
};

onMounted(() => document.addEventListener("click", handleClickOutside));
onBeforeUnmount(() =>
  document.removeEventListener("click", handleClickOutside),
);
</script>

<style scoped>
.picker-drop-enter-active,
.picker-drop-up-enter-active {
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.picker-drop-leave-active,
.picker-drop-up-leave-active {
  transition: all 0.15s ease-in;
}
.picker-drop-enter-from {
  opacity: 0;
  transform: translateY(-8px) scale(0.96);
}
.picker-drop-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.98);
}
.picker-drop-up-enter-from {
  opacity: 0;
  transform: translateY(8px) scale(0.96);
}
.picker-drop-up-leave-to {
  opacity: 0;
  transform: translateY(4px) scale(0.98);
}
</style>
