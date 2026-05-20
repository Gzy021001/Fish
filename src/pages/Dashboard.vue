<template>
  <div class="h-full flex flex-col space-y-6 overflow-y-auto no-page-scrollbar">
    <div class="flex items-center gap-4 flex-none">
      <div class="relative">
        <button
          class="flex items-center gap-2 bg-white rounded-xl shadow-sm border border-dunhuang-yellow/30 px-4 py-2.5 hover:border-dunhuang-yellow/60 transition-colors cursor-pointer"
          @click.stop="toggleYearDropdown"
          @blur="closeYearDropdown"
        >
          <svg
            class="w-4 h-4 text-dunhuang-blue/60 shrink-0"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <rect
              x="3"
              y="4"
              width="18"
              height="18"
              rx="2"
              ry="2"
              stroke-linejoin="round"
            />
            <path d="M16 2v4M8 2v4M3 10h18" />
          </svg>
          <span
            class="text-sm font-bold text-dunhuang-blue tabular-nums tracking-wide"
            >{{ selectedYear }} 年</span
          >
          <svg
            class="w-3 h-3 text-dunhuang-blue/40 transition-transform duration-200"
            :class="{ 'rotate-180': yearDropdownOpen }"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="3"
          >
            <path d="M6 9l6 6 6-6" />
          </svg>
        </button>
        <Transition name="dropdown">
          <ul
            v-if="yearDropdownOpen"
            class="absolute top-full mt-1.5 left-0 w-full bg-white rounded-xl shadow-lg border border-dunhuang-yellow/25 py-1 z-50 overflow-hidden"
            @mousedown.prevent
          >
            <li
              v-for="y in availableYears"
              :key="y"
              class="px-4 py-2 text-sm cursor-pointer transition-colors"
              :class="
                y === selectedYear
                  ? 'bg-dunhuang-blue/8 text-dunhuang-blue font-bold'
                  : 'text-dunhuang-text hover:bg-dunhuang-bg'
              "
              @click="selectYear(y)"
            >
              {{ y }} 年
            </li>
          </ul>
        </Transition>
      </div>
    </div>

    <div
      class="bg-white rounded-2xl shadow-md border border-dunhuang-yellow/30 p-8 flex flex-col card-no-scroll"
    >
      <div class="flex items-center justify-between mb-6 flex-none">
        <h3
          class="text-2xl font-serif text-dunhuang-blue flex items-center gap-3 font-bold"
        >
          {{ t("dashboard.price_trend") }}
        </h3>
      </div>

      <div class="relative flex-1 overflow-hidden" style="min-height: 500px">
        <Transition name="fade">
          <div
            v-if="loading"
            class="absolute inset-0 flex items-center justify-center z-20 bg-white/50 backdrop-blur-sm rounded-xl"
          >
            <div
              class="animate-spin rounded-full h-12 w-12 border-b-2 border-dunhuang-blue"
            ></div>
          </div>
        </Transition>
        <Transition name="fade">
          <div
            v-if="!loading && !hasTrendData && !trendErrorMsg"
            class="absolute inset-0 flex items-center justify-center text-dunhuang-text/50"
          >
            最近暂无价格走势数据
          </div>
        </Transition>
        <Transition name="fade">
          <div
            v-if="!loading && trendErrorMsg"
            class="absolute inset-0 flex items-center justify-center text-dunhuang-red"
          >
            {{ trendErrorMsg }}
          </div>
        </Transition>
        <div
          v-show="hasTrendData"
          class="absolute inset-0 flex gap-4 trend-scroll-container"
          @mousedown="onCardScrollMouseDown"
        >
          <div
            class="flex-1 min-w-0 overflow-y-auto pr-1 trend-scroll-left"
            ref="cardScrollEl"
          >
            <div v-if="priceTrendAll.length > 0" class="grid grid-cols-2 gap-3">
              <div
                v-for="item in priceTrendAll"
                :key="item.speciesId"
                class="bg-white rounded-xl border hover:border-dunhuang-yellow/40 transition-colors overflow-hidden"
                :class="
                  item.change > 0 ? 'border-red-200/50' : 'border-green-200/50'
                "
              >
                <div class="px-4 pt-3 pb-2 border-b border-dunhuang-yellow/10">
                  <div class="flex items-center justify-between">
                    <span
                      class="text-sm font-bold text-dunhuang-text truncate"
                      >{{ item.name }}</span
                    >
                    <span
                      class="text-xs font-bold shrink-0 ml-2"
                      :class="
                        item.change > 0 ? 'text-red-500' : 'text-green-600'
                      "
                    >
                      {{ item.change > 0 ? "+" : ""
                      }}{{ formatPrice(item.change) }}
                    </span>
                  </div>
                  <div
                    class="flex items-center justify-between mt-1 text-[10px] text-dunhuang-text/40"
                  >
                    <span
                      >{{ dayLabel(item.dates[0]) }} ~
                      {{ dayLabel(item.dates[item.dates.length - 1]) }}</span
                    >
                    <span class="tabular-nums"
                      >{{ formatPrice(item.startPrice) }} →
                      {{ formatPrice(item.currentPrice) }}</span
                    >
                  </div>
                </div>
                <div
                  class="overflow-y-auto card-dates-scroll"
                  :style="
                    item.dates.length > 3 ? { maxHeight: '4.625rem' } : {}
                  "
                >
                  <div
                    v-for="(date, di) in item.dates"
                    :key="di"
                    class="flex items-center justify-between px-4 py-1 text-xs border-b border-dunhuang-yellow/3 last:border-b-0 hover:bg-dunhuang-bg/30 transition-colors"
                  >
                    <span
                      class="text-dunhuang-text/50 tabular-nums w-16 shrink-0"
                      >{{ dayLabel(date as string) }}</span
                    >
                    <span
                      v-if="di > 0"
                      class="tabular-nums shrink-0 mr-2"
                      :class="
                        item.directions[di] === 'up'
                          ? 'text-red-500'
                          : item.directions[di] === 'down'
                            ? 'text-green-600'
                            : 'text-dunhuang-text/40'
                      "
                      >{{ item.diffs[di] > 0 ? "+" : ""
                      }}{{ formatPrice(item.diffs[di]) }}</span
                    >
                    <span
                      v-else
                      class="tabular-nums shrink-0 mr-2 text-dunhuang-text/40"
                      >-</span
                    >
                    <span
                      class="tabular-nums font-medium"
                      :class="
                        item.directions[di] === 'up'
                          ? 'text-red-500'
                          : item.directions[di] === 'down'
                            ? 'text-green-600'
                            : 'text-dunhuang-text/70'
                      "
                      >{{ formatPrice(item.prices[di]) }}</span
                    >
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div
            v-if="priceFluctuationData.length > 0"
            class="w-48 shrink-0 flex flex-col bg-gradient-to-b from-dunhuang-bg/50 to-dunhuang-bg/20 rounded-xl border border-dunhuang-yellow/15 overflow-hidden"
          >
            <div
              class="px-3 py-2 border-b border-dunhuang-yellow/10 text-xs font-bold text-dunhuang-blue flex-none"
            >
              单价浮动
              <span class="text-dunhuang-text/40 font-normal">(元)</span>
            </div>
            <div class="flex-1 overflow-y-auto">
              <div
                v-for="item in priceFluctuationData"
                :key="item.speciesId"
                class="px-3 py-1.5 border-b border-dunhuang-yellow/5 last:border-b-0 hover:bg-dunhuang-yellow/5 transition-colors"
              >
                <div
                  class="text-xs font-medium text-dunhuang-text truncate leading-tight"
                >
                  {{ item.name }}
                </div>
                <div class="flex items-center justify-between mt-0.5">
                  <span class="text-[10px] text-dunhuang-text/40">最低</span>
                  <span
                    class="text-[10px] text-dunhuang-text/60 tabular-nums"
                    >{{ formatPrice(item.minPrice) }}</span
                  >
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-[10px] text-dunhuang-text/40">最高</span>
                  <span
                    class="text-[10px] text-dunhuang-text/60 tabular-nums"
                    >{{ formatPrice(item.maxPrice) }}</span
                  >
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div
      class="bg-white rounded-2xl shadow-md border border-dunhuang-yellow/30 p-8 flex flex-col"
    >
      <div class="flex items-center justify-between mb-6 flex-none">
        <h3
          class="text-2xl font-serif text-dunhuang-blue flex items-center gap-3 font-bold"
        >
          放生统计
        </h3>
      </div>

      <div v-if="hasBillData" class="grid grid-cols-2 gap-5 mb-4 flex-none">
        <div
          class="relative overflow-hidden rounded-2xl bg-gradient-to-br from-dunhuang-bg to-dunhuang-card border border-dunhuang-yellow/25 px-5 py-3.5 shadow-sm"
        >
          <div
            class="absolute top-0 right-0 w-14 h-14 rounded-bl-full bg-dunhuang-blue/5 -mr-3 -mt-3"
          ></div>
          <div
            class="relative z-10 flex items-baseline gap-2 whitespace-nowrap"
          >
            <div
              class="w-1.5 h-1.5 rounded-full bg-dunhuang-blue shrink-0"
            ></div>
            <span class="text-xs text-dunhuang-text/40 tracking-wider uppercase"
              >总重量</span
            >
            <span class="text-xl font-bold text-dunhuang-blue tabular-nums">{{
              formatPrice(grandTotalWeight)
            }}</span>
            <span class="text-xs text-dunhuang-text/40">公斤</span>
          </div>
        </div>
        <div
          class="relative overflow-hidden rounded-2xl bg-gradient-to-br from-dunhuang-bg to-dunhuang-card border border-dunhuang-yellow/25 px-5 py-3.5 shadow-sm"
        >
          <div
            class="absolute top-0 right-0 w-14 h-14 rounded-bl-full bg-dunhuang-red/5 -mr-3 -mt-3"
          ></div>
          <div
            class="relative z-10 flex items-baseline gap-2 whitespace-nowrap"
          >
            <div
              class="w-1.5 h-1.5 rounded-full bg-dunhuang-red shrink-0"
            ></div>
            <span class="text-xs text-dunhuang-text/40 tracking-wider uppercase"
              >总金额</span
            >
            <span class="text-xl font-bold text-dunhuang-red tabular-nums">{{
              fmtYuan(grandTotalAmount)
            }}</span>
            <span class="text-xs text-dunhuang-text/40">元</span>
          </div>
        </div>
      </div>

      <div class="relative" style="height: 420px">
        <Transition name="fade">
          <div
            v-if="loading"
            class="absolute inset-0 flex items-center justify-center z-20 bg-white/50 backdrop-blur-sm rounded-xl"
          >
            <div
              class="animate-spin rounded-full h-12 w-12 border-b-2 border-dunhuang-blue"
            ></div>
          </div>
        </Transition>
        <Transition name="fade">
          <div
            v-if="!loading && !hasBillData && !billsErrorMsg"
            class="absolute inset-0 flex items-center justify-center text-dunhuang-text/50"
          >
            暂无放生统计数据
          </div>
        </Transition>
        <Transition name="fade">
          <div
            v-if="!loading && billsErrorMsg"
            class="absolute inset-0 flex items-center justify-center text-dunhuang-red"
          >
            {{ billsErrorMsg }}
          </div>
        </Transition>
        <div
          v-show="hasBillData"
          ref="billsChartRef"
          class="absolute inset-0 w-full h-full"
        ></div>
      </div>
    </div>

    <div
      class="bg-white rounded-2xl shadow-md border border-dunhuang-yellow/30 p-8 flex flex-col"
    >
      <div class="flex items-center justify-between mb-6 flex-none">
        <h3
          class="text-2xl font-serif text-dunhuang-blue flex items-center gap-3 font-bold"
        >
          物命总重量
        </h3>
      </div>

      <div class="relative flex-1" style="min-height: 480px">
        <Transition name="fade">
          <div
            v-if="loading"
            class="absolute inset-0 flex items-center justify-center z-20 bg-white/50 backdrop-blur-sm rounded-xl"
          >
            <div
              class="animate-spin rounded-full h-12 w-12 border-b-2 border-dunhuang-blue"
            ></div>
          </div>
        </Transition>
        <Transition name="fade">
          <div
            v-if="!loading && !hasSpeciesWeightData && !billsErrorMsg"
            class="absolute inset-0 flex items-center justify-center text-dunhuang-text/50"
          >
            暂无物命重量数据
          </div>
        </Transition>
        <Transition name="fade">
          <div
            v-if="!loading && billsErrorMsg"
            class="absolute inset-0 flex items-center justify-center text-dunhuang-red"
          >
            {{ billsErrorMsg }}
          </div>
        </Transition>
        <div
          v-show="hasSpeciesWeightData"
          ref="speciesWeightChartRef"
          class="absolute inset-0 w-full h-full"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from "vue";
import { useI18n } from "vue-i18n";
import * as echarts from "echarts";
import api from "../api";
import { isAuthError } from "../lib/error";

const { t } = useI18n();

const speciesList = ref<any[]>([]);
const trendDataMap = ref<Record<number, any[]>>({});
const billWeekMap = ref<
  Map<string, { total_amount: number; total_weight: number }>
>(new Map());
const speciesWeekWeightMap = ref<Map<string, Map<number, number>>>(new Map());
const loading = ref(false);
const trendErrorMsg = ref("");
const billsErrorMsg = ref("");

const currentYear = new Date().getFullYear();
const selectedYear = ref(currentYear);
const yearDropdownOpen = ref(false);

const toggleYearDropdown = () => {
  yearDropdownOpen.value = !yearDropdownOpen.value;
};

const closeYearDropdown = () => {
  yearDropdownOpen.value = false;
};

const availableYears = computed(() => {
  const years: number[] = [];
  for (let y = 2024; y <= currentYear + 3; y++) {
    years.push(y);
  }
  return years;
});

const hasTrendData = computed(() => {
  return Object.values(trendDataMap.value).some((data) => data.length > 0);
});

const hasBillData = computed(() => {
  return billWeekMap.value.size > 0;
});

const hasSpeciesWeightData = computed(() => {
  return speciesWeekWeightMap.value.size > 0;
});

const grandTotalWeight = computed(() => {
  let sum = 0;
  billWeekMap.value.forEach((v) => (sum += v.total_weight));
  return Number(sum.toFixed(2));
});

const grandTotalAmount = computed(() => {
  let sum = 0;
  billWeekMap.value.forEach((v) => (sum += v.total_amount));
  return Number(sum.toFixed(2));
});

const priceFluctuationData = computed(() => {
  const result: {
    speciesId: number;
    name: string;
    minPrice: number;
    maxPrice: number;
    avgPrice: number;
  }[] = [];

  for (const [spIdStr, dataArray] of Object.entries(trendDataMap.value)) {
    if (dataArray.length === 0) continue;
    const spId = Number(spIdStr);
    const sp = speciesList.value.find((s) => s.id === spId);
    if (!sp) continue;
    if (isPackagingItem(sp.name_zh)) continue;

    const prices = dataArray
      .map((item: any) => Number(item.avg_price))
      .filter((p: number) => !isNaN(p));
    if (prices.length === 0) continue;

    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const avgPrice =
      prices.reduce((a: number, b: number) => a + b, 0) / prices.length;

    result.push({
      speciesId: spId,
      name: sp.name_zh,
      minPrice: Number(minPrice.toFixed(2)),
      maxPrice: Number(maxPrice.toFixed(2)),
      avgPrice: Number(avgPrice.toFixed(2)),
    });
  }

  return result;
});

const priceTrendGrouped = computed(() => {
  const up: {
    speciesId: number;
    name: string;
    currentPrice: number;
    startPrice: number;
    change: number;
    changePercent: number;
    dates: string[];
    prices: number[];
    directions: ("up" | "down" | "flat")[];
    diffs: number[];
  }[] = [];
  const down: {
    speciesId: number;
    name: string;
    currentPrice: number;
    startPrice: number;
    change: number;
    changePercent: number;
    dates: string[];
    prices: number[];
    directions: ("up" | "down" | "flat")[];
    diffs: number[];
  }[] = [];

  for (const [spIdStr, dataArray] of Object.entries(trendDataMap.value)) {
    if (dataArray.length < 2) continue;
    const spId = Number(spIdStr);
    const sp = speciesList.value.find((s) => s.id === spId);
    if (!sp) continue;

    const sorted = [...dataArray]
      .filter((item: any) => item.date && item.avg_price != null)
      .sort((a: any, b: any) => a.date.localeCompare(b.date));
    if (sorted.length < 2) continue;

    const half = Math.ceil(sorted.length / 2);
    const firstHalf = sorted.slice(0, half);
    const secondHalf = sorted.slice(half);

    const firstAvg =
      firstHalf.reduce((s: number, i: any) => s + Number(i.avg_price), 0) /
      firstHalf.length;
    const secondAvg =
      secondHalf.reduce((s: number, i: any) => s + Number(i.avg_price), 0) /
      secondHalf.length;

    const startPrice = Number(
      firstHalf[firstHalf.length - 1].avg_price,
    ).toFixed(2);
    const currentPrice = Number(
      secondHalf[secondHalf.length - 1].avg_price,
    ).toFixed(2);
    const change = Number(
      (Number(currentPrice) - Number(startPrice)).toFixed(2),
    );
    const changePercent = Number(
      ((change / Number(startPrice)) * 100).toFixed(1),
    );
    const dates = sorted.map((i: any) => i.date);
    const prices = sorted.map((i: any) => Number(i.avg_price));

    const directions: ("up" | "down" | "flat")[] = [];
    const diffs: number[] = [];
    for (let i = 0; i < prices.length; i++) {
      const diff = i === 0 ? 0 : Number((prices[i] - prices[i - 1]).toFixed(2));
      diffs.push(diff);
      if (i === 0) {
        directions.push("flat");
      } else if (diff > 0) {
        directions.push("up");
      } else if (diff < 0) {
        directions.push("down");
      } else {
        directions.push("flat");
      }
    }

    const item = {
      speciesId: spId,
      name: sp.name_zh,
      currentPrice: Number(currentPrice),
      startPrice: Number(startPrice),
      change,
      changePercent,
      dates,
      prices,
      directions,
      diffs,
    };

    if (change > 0) {
      up.push(item);
    } else {
      down.push(item);
    }
  }

  return { up, down };
});

const priceTrendAll = computed(() => {
  const all = [...priceTrendGrouped.value.up, ...priceTrendGrouped.value.down];
  const filtered = all.filter((item) => !isPackagingItem(item.name));
  filtered.sort((a, b) => Math.abs(b.change) - Math.abs(a.change));
  return filtered;
});

const billsChartRef = ref<HTMLElement | null>(null);
const speciesWeightChartRef = ref<HTMLElement | null>(null);
let billsChartInstance: echarts.ECharts | null = null;
let speciesWeightChartInstance: echarts.ECharts | null = null;

const colorPalette = [
  "#8b6914",
  "#5a7d5a",
  "#c4a35a",
  "#5c4033",
  "#b87333",
  "#6b4a5d",
  "#a0522d",
  "#3b6b4a",
  "#7a5c45",
  "#4a5d6b",
];

const isPackagingItem = (name: string) => {
  const keywords = [
    "袋",
    "打包",
    "包装",
    "绳子",
    "胶带",
    "泡沫",
    "保温",
    "耗材",
  ];
  return keywords.some((kw) => name.includes(kw));
};

const dayLabel = (dateStr: string): string => {
  const [, m, d] = dateStr.split("-");
  return `${parseInt(m)}/${parseInt(d)}`;
};

const formatPrice = (value: number): string => {
  const strVal = String(value);
  const dotIndex = strVal.indexOf(".");
  if (dotIndex === -1) return `${strVal}.00`;
  return `${strVal.substring(0, dotIndex)}.${(strVal.substring(dotIndex + 1) + "00").substring(0, 2)}`;
};

const fmtYuan = (v: number) => `¥${formatPrice(v)}`;

// ---- 数据获取 ----

const fetchSpecies = async () => {
  loading.value = true;
  try {
    trendErrorMsg.value = "";
    billsErrorMsg.value = "";
    const res = await api.get("/species");
    speciesList.value = res.data || [];
    if (speciesList.value.length > 0) {
      await Promise.all([fetchAllTrends(), fetchBills()]);
    }
    if (hasBillData.value) renderBillsChart();
    if (hasSpeciesWeightData.value) renderSpeciesWeightChart();
  } catch (error: any) {
    if (isAuthError(error)) return;
    trendErrorMsg.value = "获取品种数据失败。";
  } finally {
    loading.value = false;
  }
};

const fetchAllTrends = async () => {
  try {
    let failedCount = 0;
    const total = speciesList.value.length;

    const promises = speciesList.value.map((sp) =>
      api
        .get(
          `/stats/price-trend?species_id=${sp.id}&year=${selectedYear.value}`,
        )
        .then((res) => ({ id: sp.id, data: res.data }))
        .catch((err) => {
          console.error(`Failed to fetch trend for species ${sp.id}`, err);
          failedCount++;
          return { id: sp.id, data: [] };
        }),
    );
    const results = await Promise.all(promises);

    if (failedCount === total && total > 0) {
      trendErrorMsg.value = "获取价格走势失败。";
      trendDataMap.value = {};
      return;
    }

    const newTrendDataMap: Record<number, any[]> = {};
    results.forEach((res) => {
      if (res.data && res.data.length > 0) newTrendDataMap[res.id] = res.data;
    });
    trendDataMap.value = newTrendDataMap;
  } catch (error: any) {
    console.error("Failed to fetch trends", error);
    if (!isAuthError(error)) {
      trendErrorMsg.value = "获取价格走势失败。";
      trendDataMap.value = {};
    }
  }
};

const fetchBills = async () => {
  try {
    const dateFrom = `${selectedYear.value}-01-01`;
    const dateTo = `${selectedYear.value}-12-31`;
    const res = await api.get(
      `/bills?limit=0&date_from=${dateFrom}&date_to=${dateTo}`,
    );
    const bills = res.data || [];
    const map = new Map<
      string,
      { total_amount: number; total_weight: number }
    >();
    const spWeightMap = new Map<string, Map<number, number>>();
    for (const b of bills) {
      if (!b.release_date) continue;
      const key = b.release_date.slice(0, 10);
      const cur = map.get(key) || { total_amount: 0, total_weight: 0 };
      cur.total_amount += Number(b.total_amount || 0);
      cur.total_weight += Number(b.weight || 0);
      map.set(key, cur);

      if (!spWeightMap.has(key)) spWeightMap.set(key, new Map());
      const spMap = spWeightMap.get(key)!;
      const spId = Number(b.species_id);
      spMap.set(spId, (spMap.get(spId) || 0) + Number(b.weight || 0));
    }
    billWeekMap.value = map;
    speciesWeekWeightMap.value = spWeightMap;
  } catch (error: any) {
    if (!isAuthError(error)) {
      billsErrorMsg.value = "获取放生数据失败。";
    }
  }
};

// ---- 年份切换 ----

const selectYear = async (y: number) => {
  yearDropdownOpen.value = false;
  if (selectedYear.value === y) return;
  selectedYear.value = y;
  await onYearChange();
};

const onYearChange = async () => {
  if (speciesList.value.length === 0) return;
  trendErrorMsg.value = "";
  billsErrorMsg.value = "";
  loading.value = true;
  try {
    await Promise.all([fetchAllTrends(), fetchBills()]);
  } finally {
    loading.value = false;
  }
  if (hasBillData.value) renderBillsChart();
  if (hasSpeciesWeightData.value) renderSpeciesWeightChart();
};

// ---- 图表2: 每周放生统计 ----

const renderBillsChart = () => {
  setTimeout(() => {
    if (!billsChartRef.value) return;
    if (billsChartInstance) billsChartInstance.dispose();

    billsChartInstance = echarts.init(billsChartRef.value);

    const allDaySet = new Set<string>();
    billWeekMap.value.forEach((_, k) => allDaySet.add(k));

    const dayKeys = Array.from(allDaySet).sort();
    if (dayKeys.length === 0) {
      return;
    }

    const dayLabels = dayKeys.map((k) => dayLabel(k));

    const weightData = dayKeys.map((dk) => {
      const b = billWeekMap.value.get(dk);
      return b ? Number(b.total_weight.toFixed(2)) : 0;
    });

    const amountData = dayKeys.map((dk) => {
      const b = billWeekMap.value.get(dk);
      return b ? Number(b.total_amount.toFixed(2)) : 0;
    });

    const labelOverflow2 = dayLabels.length > 20;
    const xDataCount = dayLabels.length;
    const option: any = {
      legend: {
        data: ["总重量", "总金额"],
        bottom: 0,
        textStyle: { color: "#3d3226", fontSize: 11 },
        icon: "circle",
      },
      tooltip: {
        trigger: "item",
        backgroundColor: "#fdfaf3",
        borderColor: "#c4a35a",
        textStyle: { color: "#3d3226", fontSize: 12 },
        formatter: (params: any) => {
          if (!params || params.value === null || params.value === undefined)
            return "";
          if (params.seriesIndex === 0) {
            return `${params.marker} 总重量：${formatPrice(params.value)} 公斤`;
          }
          return `${params.marker} 总金额：${fmtYuan(params.value)}`;
        },
      },
      grid: {
        left: "4%",
        right: "6%",
        bottom: labelOverflow2 ? "22%" : "15%",
        top: "8%",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        boundaryGap: true,
        data: dayLabels,
        axisLine: { lineStyle: { color: "#c4a35a" } },
        axisLabel: {
          color: "#3d3226",
          fontSize: 10,
          rotate: labelOverflow2 ? 35 : 0,
          interval: labelOverflow2
            ? Math.ceil(dayLabels.length / 20) - 1
            : "auto",
        },
        axisTick: { show: false },
      },
      yAxis: [
        {
          type: "value",
          name: "总重量 (公斤)",
          nameTextStyle: { color: "#3d322660", fontSize: 10 },
          axisLine: { show: true, lineStyle: { color: "#c4a35a" } },
          axisLabel: {
            color: "#3d3226",
            formatter: (v: number) => v.toFixed(1),
            fontSize: 10,
          },
          splitLine: {
            lineStyle: { color: "#c4a35a", type: "dashed", opacity: 0.2 },
          },
        },
        {
          type: "value",
          name: "总金额 (元)",
          nameTextStyle: { color: "#b8733360", fontSize: 10 },
          axisLine: { show: true, lineStyle: { color: "#b8733340" } },
          axisLabel: {
            color: "#b87333",
            formatter: (v: number) => fmtYuan(v),
            fontSize: 10,
          },
          splitLine: { show: false },
        },
      ],
      series: [
        {
          name: "总重量",
          type: "bar",
          yAxisIndex: 0,
          barWidth: "6%",
          itemStyle: {
            color: "#8b6914",
            borderRadius: [4, 4, 0, 0],
          },
          data: weightData,
        },
        {
          name: "总金额",
          type: "line",
          yAxisIndex: 1,
          smooth: true,
          connectNulls: true,
          symbol: "circle",
          symbolSize: 8,
          itemStyle: {
            color: "#b87333",
            borderColor: "#b87333",
            borderWidth: 1.5,
          },
          lineStyle: { width: 2.5, color: "#b87333" },
          data: amountData,
        },
      ],
      dataZoom:
        xDataCount > 25
          ? [
              {
                type: "slider",
                bottom: 0,
                height: 24,
                borderColor: "#c4a35a40",
                fillerColor: "#c4a35a20",
                handleStyle: { color: "#c4a35a" },
                textStyle: { color: "#3d3226", fontSize: 10 },
              },
            ]
          : [],
    };

    billsChartInstance.setOption(option);
  }, 100);
};

const renderSpeciesWeightChart = () => {
  setTimeout(() => {
    if (!speciesWeightChartRef.value) return;
    if (speciesWeightChartInstance) speciesWeightChartInstance.dispose();

    speciesWeightChartInstance = echarts.init(speciesWeightChartRef.value);

    const allDaySet = new Set<string>();
    speciesWeekWeightMap.value.forEach((_, k) => allDaySet.add(k));

    const dayKeys = Array.from(allDaySet).sort();
    if (dayKeys.length === 0) return;

    const dayLabels = dayKeys.map((k) => dayLabel(k));

    const activeSpeciesIds = new Set<number>();
    speciesWeekWeightMap.value.forEach((spMap) => {
      spMap.forEach((_, spId) => activeSpeciesIds.add(spId));
    });

    const activeSpecies = speciesList.value.filter((s) =>
      activeSpeciesIds.has(s.id),
    );

    if (activeSpecies.length === 0) return;

    const series: any[] = [];
    let colorIndex = 0;

    for (const sp of activeSpecies) {
      const data = dayKeys.map((dk) => {
        const spMap = speciesWeekWeightMap.value.get(dk);
        if (!spMap) return 0;
        return Number((spMap.get(sp.id) || 0).toFixed(2));
      });

      const color = colorPalette[colorIndex % colorPalette.length];
      colorIndex++;

      series.push({
        name: sp.name_zh,
        type: "bar",
        stack: "total",
        barWidth: "5%",
        itemStyle: { color },
        emphasis: { focus: "series" },
        data,
      });
    }

    const totalPerDay = dayKeys.map((dk) => {
      const spMap = speciesWeekWeightMap.value.get(dk);
      if (!spMap) return 0;
      let sum = 0;
      spMap.forEach((v) => (sum += v));
      return Number(sum.toFixed(2));
    });

    series.push({
      name: "合计",
      type: "bar",
      stack: "total",
      barWidth: "5%",
      itemStyle: { color: "transparent" },
      tooltip: { show: false },
      emphasis: { disabled: true },
      label: {
        show: true,
        position: "top",
        color: "#3d3226",
        fontSize: 11,
        fontWeight: "bold",
        formatter: (p: any) =>
          totalPerDay[p.dataIndex] > 0
            ? formatPrice(totalPerDay[p.dataIndex]) + " 公斤"
            : "",
      },
      data: totalPerDay.map(() => 0),
    });

    const labelOverflow3 = dayLabels.length > 20;
    const xDataCount3 = dayLabels.length;
    const option: any = {
      legend: { show: false },
      tooltip: {
        trigger: "item",
        backgroundColor: "#fdfaf3",
        borderColor: "#c4a35a",
        textStyle: { color: "#3d3226", fontSize: 12 },
        formatter: (params: any) => {
          if (!params || params.value === null || params.value === undefined)
            return "";
          return `${params.marker} ${params.seriesName}：${formatPrice(params.value)} 公斤`;
        },
      },
      grid: {
        left: "4%",
        right: "6%",
        bottom: labelOverflow3 ? "22%" : "10%",
        top: "8%",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        boundaryGap: true,
        data: dayLabels,
        axisLine: { lineStyle: { color: "#c4a35a" } },
        axisLabel: {
          color: "#3d3226",
          fontSize: 10,
          rotate: labelOverflow3 ? 35 : 0,
          interval: labelOverflow3
            ? Math.ceil(dayLabels.length / 20) - 1
            : "auto",
        },
        axisTick: { show: false },
      },
      yAxis: {
        type: "value",
        name: "重量 (公斤)",
        nameTextStyle: { color: "#3d322660", fontSize: 10 },
        axisLine: { show: true, lineStyle: { color: "#c4a35a" } },
        axisLabel: {
          color: "#3d3226",
          formatter: (v: number) => v.toFixed(1),
          fontSize: 10,
        },
        splitLine: {
          lineStyle: { color: "#c4a35a", type: "dashed", opacity: 0.2 },
        },
      },
      series,
      dataZoom:
        xDataCount3 > 25
          ? [
              {
                type: "slider",
                bottom: 0,
                height: 24,
                borderColor: "#c4a35a40",
                fillerColor: "#c4a35a20",
                handleStyle: { color: "#c4a35a" },
                textStyle: { color: "#3d3226", fontSize: 10 },
              },
            ]
          : [],
    };

    speciesWeightChartInstance.setOption(option);
  }, 100);
};

const handleResize = () => {
  billsChartInstance?.resize();
  speciesWeightChartInstance?.resize();
};

const cardScrollEl = ref<HTMLElement | null>(null);
let dragTarget: HTMLElement | null = null;
let dragLastY = 0;
let dragLastTime = 0;
let dragVelocity = 0;
let momentumHandle: number | null = null;

const findScrollable = (el: HTMLElement | null): HTMLElement | null => {
  while (el) {
    const style = getComputedStyle(el);
    const overflowY = style.overflowY;
    if (overflowY === "auto" || overflowY === "scroll") {
      if (el.scrollHeight > el.clientHeight) return el;
    }
    el = el.parentElement;
  }
  return null;
};

const onCardScrollMouseDown = (e: MouseEvent) => {
  const target = e.target as HTMLElement;
  if (target.closest("button, a, input, select, textarea, .echarts, canvas"))
    return;
  const scrollable = findScrollable(target);
  if (!scrollable) return;
  if (momentumHandle !== null) {
    cancelAnimationFrame(momentumHandle);
    momentumHandle = null;
  }
  dragTarget = scrollable;
  dragLastY = e.clientY;
  dragLastTime = performance.now();
  dragVelocity = 0;
  scrollable.style.cursor = "grabbing";
  window.addEventListener("mousemove", onDragMove);
  window.addEventListener("mouseup", onDragEnd);
};

const onDragMove = (e: MouseEvent) => {
  if (!dragTarget) return;
  const now = performance.now();
  const dt = now - dragLastTime;
  const dy = e.clientY - dragLastY;
  dragVelocity = dt > 0 ? (dy / dt) * 0.7 : 0;
  dragLastY = e.clientY;
  dragLastTime = now;
  dragTarget.scrollTop -= dy * 1.6;
};

const onDragEnd = () => {
  window.removeEventListener("mousemove", onDragMove);
  window.removeEventListener("mouseup", onDragEnd);
  if (!dragTarget) return;
  dragTarget.style.cursor = "";
  const v = dragVelocity;
  const target = dragTarget;
  dragTarget = null;
  if (Math.abs(v) < 0.2) return;
  startMomentum(target, v);
};

const startMomentum = (el: HTMLElement, v: number) => {
  const friction = 0.94;
  const step = () => {
    const scrollMax = el.scrollHeight - el.clientHeight;
    el.scrollTop += v;
    if (el.scrollTop <= 0 || el.scrollTop >= scrollMax) {
      el.scrollTop = el.scrollTop <= 0 ? 0 : scrollMax;
      momentumHandle = null;
      return;
    }
    v *= friction;
    if (Math.abs(v) > 0.3) {
      momentumHandle = requestAnimationFrame(step);
    } else {
      momentumHandle = null;
    }
  };
  momentumHandle = requestAnimationFrame(step);
};

onMounted(() => {
  fetchSpecies();
  window.addEventListener("resize", handleResize);
});

onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
  if (billsChartInstance) {
    billsChartInstance.dispose();
    billsChartInstance = null;
  }
  if (speciesWeightChartInstance) {
    speciesWeightChartInstance.dispose();
    speciesWeightChartInstance = null;
  }
});
</script>

<style scoped>
.dropdown-enter-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}
.dropdown-leave-active {
  transition:
    opacity 0.15s ease,
    transform 0.15s ease;
}
.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-6px) scale(0.96);
}
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.97);
}

.trend-scroll-left::-webkit-scrollbar,
.trend-scroll-left *::-webkit-scrollbar {
  width: 4px;
  height: 4px;
}

.trend-scroll-left::-webkit-scrollbar-track,
.trend-scroll-left *::-webkit-scrollbar-track {
  background: transparent;
  border-radius: 4px;
}

.trend-scroll-left::-webkit-scrollbar-thumb,
.trend-scroll-left *::-webkit-scrollbar-thumb {
  background: #c4a35a60;
  border-radius: 4px;
}

.trend-scroll-left::-webkit-scrollbar-thumb:hover,
.trend-scroll-left *::-webkit-scrollbar-thumb:hover {
  background: #c4a35a90;
}

.trend-scroll-left,
.trend-scroll-left * {
  scrollbar-width: thin;
  scrollbar-color: #c4a35a60 transparent;
}

.trend-scroll-container > :last-child::-webkit-scrollbar,
.trend-scroll-container > :last-child *::-webkit-scrollbar {
  width: 0;
  height: 0;
}

.trend-scroll-container > :last-child,
.trend-scroll-container > :last-child * {
  scrollbar-width: none;
}

.no-page-scrollbar::-webkit-scrollbar {
  display: none;
}

.no-page-scrollbar {
  scrollbar-width: none;
}

.card-no-scroll::-webkit-scrollbar {
  display: none;
}

.card-no-scroll {
  scrollbar-width: none;
}

.trend-scroll-left .card-dates-scroll::-webkit-scrollbar {
  width: 0;
  height: 0;
}

.trend-scroll-left .card-dates-scroll {
  scrollbar-width: none;
  -ms-overflow-style: none;
}
</style>
