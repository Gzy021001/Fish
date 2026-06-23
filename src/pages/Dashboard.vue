<template>
  <div class="h-full flex flex-col space-y-6 overflow-y-auto no-page-scrollbar">
    <div
      class="bg-white rounded-2xl shadow-md border border-dunhuang-yellow/30 p-8 flex flex-col card-no-scroll"
    >
      <div class="flex items-center justify-between mb-6 flex-none">
        <div class="flex items-center gap-4">
          <h3
            class="text-2xl font-serif text-dunhuang-blue font-bold"
          >
            {{ t("dashboard.price_trend") }}
          </h3>
          <div class="relative">
            <button
              class="flex items-center gap-2 bg-dunhuang-bg/50 rounded-lg border border-dunhuang-yellow/20 px-3 py-1.5 hover:border-dunhuang-yellow/40 transition-colors cursor-pointer"
              @click.stop="toggleYearDropdown"
              @blur="closeYearDropdown"
            >
              <svg
                class="w-3.5 h-3.5 text-dunhuang-blue/50 shrink-0"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2" stroke-linejoin="round" />
                <path d="M16 2v4M8 2v4M3 10h18" />
              </svg>
              <span class="text-sm font-bold text-dunhuang-blue tabular-nums">{{ selectedYear }} 年</span>
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
                class="absolute top-full mt-1 left-0 w-28 bg-white rounded-xl shadow-lg border border-dunhuang-yellow/25 py-1 z-50 overflow-hidden"
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
      </div>

      <div class="relative flex-1" style="min-height: 500px">
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
                class="bg-white rounded-xl border hover:border-dunhuang-yellow/40 transition-colors overflow-visible"
                :class="
                  item.change > 0 ? 'border-red-200/50' : 'border-green-200/50'
                "
              >
                <div class="px-4 pt-3 pb-2 border-b border-dunhuang-yellow/10 rounded-t-xl overflow-hidden">
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
                  :ref="(el: any) => setTrendRef(item.speciesId, el)"
                  class="w-full h-20"
                ></div>
              </div>
            </div>
          </div>
          <div
            v-if="priceFluctuationData.length > 0"
            class="w-56 shrink-0 flex flex-col bg-gradient-to-b from-dunhuang-bg/50 to-dunhuang-bg/20 rounded-xl border border-dunhuang-yellow/15"
          >
            <div
              class="px-3 py-2 border-b border-dunhuang-yellow/10 text-xs font-bold text-dunhuang-blue flex-none"
            >
              单价浮动
              <span class="text-dunhuang-text/40 font-normal">(元)</span>
            </div>
            <div class="flex-1 overflow-y-auto">
              <div
                ref="fluctuationChartRef"
                class="w-full"
                :style="{ height: `${fluctuationChartHeight}px` }"
              ></div>
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

      <div v-if="hasBillData" class="flex gap-5 mb-5 flex-none">
        <div
          class="bg-[#f9f9f6] rounded-2xl px-5 py-3 border-l-[3px] border-[#5c4033]/40 flex flex-col justify-center"
          style="flex: 0.82"
        >
          <div class="text-xs text-gray-500 mb-1.5 font-medium">总重量</div>
          <div class="flex items-baseline gap-1.5">
            <span class="text-2xl font-bold text-gray-800 tabular-nums">{{
              formatPrice(grandTotals.weight)
            }}</span>
            <span class="text-sm text-gray-500">公斤</span>
          </div>
        </div>
        <div
          class="bg-[#f9f9f6] rounded-2xl px-5 py-3 border-l-[3px] border-[#c49b4a]/50 flex flex-col justify-center"
          style="flex: 0.82"
        >
          <div class="text-xs text-gray-500 mb-1.5 font-medium">总金额</div>
          <div class="flex items-baseline gap-1.5">
            <span class="text-2xl font-bold text-dunhuang-red tabular-nums">{{
              fmtYuan(grandTotals.amount)
            }}</span>
            <span class="text-sm text-gray-500">元</span>
          </div>
        </div>
        <div
          class="flex-1 bg-[#f9f9f6] rounded-2xl px-5 py-3 border-l-[3px] border-dunhuang-blue/25"
        >
          <div class="flex items-baseline text-xs text-gray-500 mb-1.5">
            <span class="w-12 shrink-0"></span>
            <span class="flex-1 text-right font-medium">总重量(公斤)</span>
            <span class="w-28 text-right font-medium">总金额(元)</span>
          </div>
          <div class="flex items-baseline py-0.5">
            <span class="text-xs text-gray-600 w-12 shrink-0 font-medium">上半年</span>
            <span
              class="flex-1 text-right text-base font-bold text-gray-800 tabular-nums"
              >{{ formatPrice(halfYearStats.h1Weight) }}</span
            >
            <span
              class="w-28 text-right text-base font-bold text-dunhuang-red tabular-nums"
              >{{ fmtYuan(halfYearStats.h1Amount) }}</span
            >
          </div>
          <div
            class="flex items-baseline py-0.5 mt-1 border-t border-gray-200/80 pt-1.5"
          >
            <span class="text-xs text-gray-600 w-12 shrink-0 font-medium">下半年</span>
            <span
              class="flex-1 text-right text-base font-bold text-gray-800 tabular-nums"
              >{{ formatPrice(halfYearStats.h2Weight) }}</span
            >
            <span
              class="w-28 text-right text-base font-bold text-dunhuang-red tabular-nums"
              >{{ fmtYuan(halfYearStats.h2Amount) }}</span
            >
          </div>
        </div>
      </div>

      <div class="flex gap-5 mb-5" style="height: 400px">
        <div class="relative" style="flex: 0 0 58%">
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
        <div class="relative" style="flex: 0 0 38%">
          <div
            v-show="hasBillData"
            ref="pieChart"
            class="absolute inset-0 w-full h-full"
          ></div>
        </div>
      </div>

      <div class="relative" style="height: 480px">
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
import { ref, shallowRef, onMounted, onUnmounted, computed, nextTick, watch } from "vue";
import { useI18n } from "vue-i18n";
import * as echarts from "echarts/core";
import { BarChart, LineChart, PieChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  DataZoomComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import api from "../api";
import { isAuthError, apiErrorMessage } from "../lib/error";
import { isPackagingItem, formatMoney, getSpeciesCategory, dayLabel } from "../lib/utils";

echarts.use([
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  DataZoomComponent,
  BarChart,
  LineChart,
  PieChart,
  CanvasRenderer,
]);

const { t } = useI18n();

const speciesList = shallowRef<any[]>([]);
const trendDataMap = shallowRef<Record<number, any[]>>({});
const billWeekMap = shallowRef<
  Map<string, { total_amount: number; total_weight: number }>
>(new Map());
const speciesWeekWeightMap = shallowRef<Map<string, Map<number, number>>>(
  new Map(),
);
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

const grandTotals = computed(() => {
  let weight = 0;
  let amount = 0;
  billWeekMap.value.forEach((v) => {
    weight += v.total_weight;
    amount += v.total_amount;
  });
  return {
    weight: Number(weight.toFixed(2)),
    amount: Number(amount.toFixed(2)),
  };
});

const halfYearStats = computed(() => {
  let h1Weight = 0;
  let h1Amount = 0;
  let h2Weight = 0;
  let h2Amount = 0;
  billWeekMap.value.forEach((v, dateKey) => {
    const month = parseInt(dateKey.split("-")[1]) || 0;
    if (month >= 1 && month <= 6) {
      h1Weight += v.total_weight;
      h1Amount += v.total_amount;
    } else {
      h2Weight += v.total_weight;
      h2Amount += v.total_amount;
    }
  });
  return {
    h1Weight: Number(h1Weight.toFixed(2)),
    h1Amount: Number(h1Amount.toFixed(2)),
    h2Weight: Number(h2Weight.toFixed(2)),
    h2Amount: Number(h2Amount.toFixed(2)),
  };
});

const priceFluctuationData = computed(() => {
  if (!Array.isArray(speciesList.value)) return [];
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
  if (!Array.isArray(speciesList.value)) return { up: [], down: [] };
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
const pieChart = ref<HTMLElement | null>(null);
const fluctuationChartRef = ref<HTMLElement | null>(null);
let billsChartInstance: echarts.ECharts | null = null;
let speciesWeightChartInstance: echarts.ECharts | null = null;
let pieChartInstance: echarts.ECharts | null = null;
let fluctuationChartInstance: echarts.ECharts | null = null;
const trendChartRefs = new Map<number, HTMLElement>();
const trendChartInstances = new Map<number, echarts.ECharts>();
const setTrendRef = (id: number, el: any) => {
  if (el) trendChartRefs.set(id, el as HTMLElement);
};

watch(priceTrendAll, () => {
  nextTick(() => renderTrendMiniCharts());
});

watch(priceFluctuationData, () => {
  nextTick(() => renderFluctuationChart());
});

const fluctuationChartHeight = ref(0);

const categoryDefs = [
  { key: "鱼类", label: "鱼类", color: "#5c4033" },
  { key: "贝类", label: "贝类", color: "#c49b4a" },
  { key: "螺类", label: "螺类", color: "#4a7c59" },
  { key: "龟鳖类", label: "龟鳖类", color: "#8b5e3c" },
  { key: "虾蟹类", label: "虾蟹类", color: "#c4633a" },
  { key: "其他", label: "其他", color: "#6b7280" },
];

const catLineColors: Record<string, string> = {
  鱼类: "#5c4033",
  贝类: "#c49b4a",
  螺类: "#4a7c59",
  龟鳖类: "#8b5e3c",
  虾蟹类: "#c4633a",
  其他: "#6b7280",
};

const formatPrice = (value: number): string => formatMoney(value);

const fmtYuan = (v: number) => `¥${formatPrice(v)}`;

const renderTrendMiniCharts = () => {
  priceTrendAll.value.forEach((item: any) => {
    const el = trendChartRefs.get(item.speciesId);
    if (!el) return;
    const old = trendChartInstances.get(item.speciesId);
    if (old) old.dispose();
    const chart = echarts.init(el);
    trendChartInstances.set(item.speciesId, chart);

    const prices: number[] = item.prices;
    const dates: string[] = item.dates;
    const isUp = item.change > 0;
    const color = isUp ? "#ef4444" : "#16a34a";
    const areaColor = isUp
      ? ["rgba(239,68,68,0.12)", "rgba(239,68,68,0)"]
      : ["rgba(22,163,74,0.12)", "rgba(22,163,74,0)"];

    chart.setOption({
      grid: { left: 28, right: 28, top: 20, bottom: 8 },
      xAxis: { type: "category", data: prices.map((_, i) => i), show: false },
      yAxis: { type: "value", show: false, scale: true },
      tooltip: {
        trigger: "axis",
        appendToBody: true,
        backgroundColor: "#ffffff",
        borderColor: "#e5e7eb",
        borderWidth: 1,
        padding: [6, 10],
        textStyle: { color: "#374151", fontSize: 11 },
        formatter: (params: any) => {
          const p = Array.isArray(params) ? params[0] : params;
          if (!p || p.value == null) return "";
          const idx = p.dataIndex;
          return `<div style="font-weight:bold;margin-bottom:2px;color:${color};">${dayLabel(dates[idx])}</div>¥${formatPrice(p.value)}`;
        },
      },
      series: [
        {
          type: "line",
          data: prices,
          smooth: true,
          symbol: "circle",
          symbolSize: 4,
          lineStyle: { width: 1.5, color },
          itemStyle: { color },
          emphasis: {
            itemStyle: { borderColor: color, borderWidth: 2 },
            symbolSize: 7,
          },
          areaStyle: {
            color: {
              type: "linear", x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: areaColor[0] },
                { offset: 1, color: areaColor[1] },
              ],
            },
          },
          label: {
            show: true,
            position: "top",
            fontSize: 8,
            color: "#6b7280",
            formatter: (p: any) => `¥${formatPrice(p.value)}`,
          },
        },
      ],
    });
  });
};

// ---- 数据获取 ----

const fetchSpecies = async () => {
  loading.value = true;
  try {
    trendErrorMsg.value = "";
    billsErrorMsg.value = "";
    const res = await api.get("/species");
    speciesList.value = Array.isArray(res.data) ? res.data : [];
    if (speciesList.value.length > 0) {
      await Promise.all([fetchAllTrends(), fetchBills()]);
    }
    if (hasBillData.value) {
      renderBillsChart();
      renderPieChart();
    }
    if (hasSpeciesWeightData.value) renderSpeciesWeightChart();
  } catch (error: any) {
    if (isAuthError(error)) return;
    trendErrorMsg.value = apiErrorMessage(error, "获取品种数据");
  } finally {
    loading.value = false;
  }
};

const fetchAllTrends = async () => {
  if (!Array.isArray(speciesList.value) || speciesList.value.length === 0) {
    trendDataMap.value = {};
    return;
  }

  try {
    const ids = speciesList.value.map((sp) => sp.id).join(",");
    const res = await api.get(
      `/stats/price-trend-batch?species_ids=${ids}&year=${selectedYear.value}`,
    );

    const newTrendDataMap: Record<number, any[]> = {};
    if (res.data) {
      // res.data is Record<string, any[]> where keys are species IDs
      Object.entries(res.data).forEach(([id, data]) => {
        newTrendDataMap[Number(id)] = data as any[];
      });
    }
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
      `/bills?limit=0&page_size=-1&date_from=${dateFrom}&date_to=${dateTo}`,
    );
    let bills = [];
    if (res.data && typeof res.data.total === "number") {
      bills = res.data.items || [];
    } else {
      bills = Array.isArray(res.data) ? res.data : [];
    }
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
  if (hasBillData.value) {
    renderBillsChart();
    renderPieChart();
  }
  if (hasSpeciesWeightData.value) renderSpeciesWeightChart();
};

// ---- 单价浮动柱状图 ----

const renderFluctuationChart = () => {
  if (!fluctuationChartRef.value) return;
  const data = priceFluctuationData.value;
  if (data.length === 0) return;

  const sorted = [...data]
    .filter((d) => d.maxPrice > 0)
    .sort((a, b) => b.maxPrice - a.maxPrice);

  const names = sorted.map((d) => d.name);
  const maxVals = sorted.map((d) => d.maxPrice);
  const minVals = sorted.map((d) => d.minPrice);

  const rowH = 24;
  fluctuationChartHeight.value = names.length * rowH + 4;

  nextTick(() => {
    if (!fluctuationChartRef.value) return;
    if (fluctuationChartInstance) fluctuationChartInstance.dispose();

    fluctuationChartInstance = echarts.init(fluctuationChartRef.value);

  fluctuationChartInstance.setOption({
    grid: { left: 4, right: 52, top: 4, bottom: 2, containLabel: true },
    xAxis: {
      type: "value",
      axisLabel: { show: false },
      splitLine: { show: false },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    yAxis: {
      type: "category",
      data: names,
      axisLabel: {
        fontSize: 10,
        color: "#374151",
        fontWeight: "bold",
        width: 72,
        overflow: "truncate",
      },
      axisLine: { show: false },
      axisTick: { show: false },
      inverse: true,
    },
    series: [
      {
        type: "bar",
        data: maxVals.map((max, i) => ({
          value: max,
          minPrice: minVals[i],
          maxPrice: maxVals[i],
        })),
        itemStyle: {
          color: {
            type: "linear", x: 0, y: 0, x2: 1, y2: 0,
            colorStops: [
              { offset: 0, color: "rgba(196,155,74,0.25)" },
              { offset: 1, color: "#c49b4a" },
            ],
          },
          borderRadius: [0, 4, 4, 0],
        },
        barWidth: "60%",
        emphasis: {
          itemStyle: {
            color: {
              type: "linear", x: 0, y: 0, x2: 1, y2: 0,
              colorStops: [
                { offset: 0, color: "rgba(196,155,74,0.45)" },
                { offset: 1, color: "#e0b860" },
              ],
            },
          },
        },
        label: {
          show: true,
          position: "right",
          distance: 4,
          color: "#5c4033",
          fontSize: 10,
          fontWeight: "bold",
          formatter: (p: any) => `¥${formatPrice(p.data.maxPrice)}`,
        },
      },
    ],
    tooltip: {
      trigger: "axis",
      appendToBody: true,
      backgroundColor: "#ffffff",
      borderColor: "#e5e7eb",
      borderWidth: 1,
      padding: [8, 12],
      textStyle: { color: "#374151", fontSize: 11 },
      formatter: (params: any) => {
        const p = Array.isArray(params) ? params[0] : params;
        if (!p || !p.data) return "";
        return `<div style="font-weight:bold;margin-bottom:3px;">${p.name}</div>`
          + `<div>最低：<b>¥${formatPrice(p.data.minPrice)}</b></div>`
          + `<div>最高：<b>¥${formatPrice(p.data.maxPrice)}</b></div>`;
      },
    },
  });
  });
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
    const showDataZoom = xDataCount > 25;
    // 自适应柱宽：数据越少柱子越宽
    const barWidth =
      xDataCount <= 7
        ? "30%"
        : xDataCount <= 15
          ? "18%"
          : xDataCount <= 30
            ? "10%"
            : "6%";
    // dataZoom slider 出现时 legend 上移避免重叠，grid bottom 预留空间
    const legendBottom = showDataZoom ? 24 : 0;
    const gridBottom = showDataZoom ? "24%" : labelOverflow2 ? "22%" : "15%";
    const option: any = {
      labelLayout: { hideOverlap: true },
      legend: {
        data: ["总重量", "总金额"],
        bottom: legendBottom,
        textStyle: { color: "#6b7280", fontSize: 11 },
        icon: "roundRect",
        itemWidth: 12,
        itemHeight: 4,
      },
      tooltip: {
        trigger: "axis",
        axisPointer: {
          type: "cross",
          crossStyle: { color: "#9ca3af" },
          label: {
            backgroundColor: "#5c4033",
            color: "#fff",
          },
        },
        backgroundColor: "#ffffff",
        borderColor: "#e5e7eb",
        borderWidth: 1,
        padding: [10, 14],
        textStyle: { color: "#374151", fontSize: 13 },
        formatter: (params: any) => {
          if (!Array.isArray(params) || params.length === 0) return "";
          const weight = params.find((p: any) => p.seriesName === "总重量");
          const amount = params.find((p: any) => p.seriesName === "总金额");
          let html = `<div style="font-weight:bold;margin-bottom:5px;color:#374151;">${params[0].axisValue}</div>`;
          if (weight && weight.value != null) {
            html += `<div>${weight.marker} 总重量：<b>${formatPrice(weight.value)}</b> 公斤</div>`;
          }
          if (amount && amount.value != null) {
            html += `<div>${amount.marker} 总金额：<b>${fmtYuan(amount.value)}</b></div>`;
          }
          return html;
        },
      },
      grid: {
        left: "4%",
        right: "6%",
        bottom: gridBottom,
        top: "14%",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        boundaryGap: true,
        data: dayLabels,
        axisLine: { lineStyle: { color: "#d1d5db" } },
        axisLabel: {
          color: "#9ca3af",
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
          boundaryGap: [0, 0.08],
          nameTextStyle: { color: "#9ca3af", fontSize: 10 },
          axisLine: { show: true, lineStyle: { color: "#d1d5db" } },
          axisLabel: {
            color: "#9ca3af",
            formatter: (v: number) => v.toFixed(1),
            fontSize: 10,
          },
          splitLine: {
            lineStyle: { color: "#e5e7eb", type: "solid" },
          },
        },
        {
          type: "value",
          name: "总金额 (元)",
          scale: true,
          boundaryGap: [0, 0.08],
          nameTextStyle: { color: "#9ca3af", fontSize: 10 },
          axisLine: { show: true, lineStyle: { color: "#d1d5db" } },
          axisLabel: {
            color: "#9ca3af",
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
          barWidth,
          z: 2,
          itemStyle: {
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: "#7a5544" },
                { offset: 1, color: "#4a2c1e" },
              ],
            },
            borderRadius: [4, 4, 0, 0],
          },
          emphasis: {
            itemStyle: {
              color: {
                type: "linear",
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: "#8b6248" },
                  { offset: 1, color: "#5c4033" },
                ],
              },
            },
          },
          label: {
            show: true,
            position: "top",
            distance: 4,
            color: "#4a2c1e",
            fontSize: 10,
            fontWeight: "bold",
            formatter: (p: any) =>
              p.value > 0 ? formatPrice(p.value) : "",
          },
          data: weightData,
        },
        {
          name: "总金额",
          type: "line",
          yAxisIndex: 1,
          z: 1,
          smooth: true,
          connectNulls: true,
          symbol: "emptyCircle",
          symbolSize: 6,
          itemStyle: {
            color: "#c49b4a",
            borderColor: "#c49b4a",
            borderWidth: 2,
          },
          lineStyle: { width: 2.5, color: "#c49b4a" },
          emphasis: {
            focus: "series",
            itemStyle: {
              color: "#e0b860",
              borderColor: "#e0b860",
              borderWidth: 3,
            },
            lineStyle: { width: 3.5, color: "#e0b860" },
            areaStyle: {
              color: {
                type: "linear",
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: "rgba(224,184,96,0.25)" },
                  { offset: 1, color: "rgba(224,184,96,0.03)" },
                ],
              },
            },
          },
          areaStyle: {
            color: {
              type: "linear",
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: "rgba(196,155,74,0.15)" },
                { offset: 1, color: "rgba(196,155,74,0.01)" },
              ],
            },
          },
          data: amountData,
        },
      ],
      dataZoom: showDataZoom
        ? [
            {
              type: "slider",
              bottom: 0,
              height: 24,
              borderColor: "#d1d5db40",
              fillerColor: "#d1d5db20",
              handleStyle: { color: "#d1d5db" },
              textStyle: { color: "#9ca3af", fontSize: 10 },
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

    const cats = categoryDefs.map((d) => ({
      key: d.key,
      label: d.label,
      color: d.color,
      data: dayKeys.map(() => 0),
    }));

    const spIdCatKeyMap = new Map<number, string>();
    speciesWeekWeightMap.value.forEach((spMap) => {
      spMap.forEach((_, spId) => {
        if (spIdCatKeyMap.has(spId)) return;
        const sp = speciesList.value.find((s: any) => s.id === spId);
        if (!sp) return;
        spIdCatKeyMap.set(spId, getSpeciesCategory(sp.name_zh));
      });
    });

    dayKeys.forEach((dk, di) => {
      const spMap = speciesWeekWeightMap.value.get(dk);
      if (!spMap) return;
      spMap.forEach((weight, spId) => {
        const cat = spIdCatKeyMap.get(spId);
        if (!cat) return;
        const c = cats.find((c) => c.key === cat);
        if (c) c.data[di] += weight;
      });
    });

    cats.forEach((c) => {
      c.data = c.data.map((v) => Number(v.toFixed(2)));
    });

    // 过滤掉全为 0 的分类（避免图例和折线冗余）
    const activeCats = cats.filter((c) => c.key !== "其他" && c.data.some((v) => v > 0));

    const series: any[] = activeCats.map((c) => ({
      name: c.label,
      type: "line",
      smooth: true,
      connectNulls: true,
      symbol: "circle",
      symbolSize: 4,
      lineStyle: { width: 2, color: catLineColors[c.key] || c.color },
      itemStyle: { color: catLineColors[c.key] || c.color },
      emphasis: { focus: "series" },
      data: c.data,
    }));

    const labelOverflow3 = dayLabels.length > 20;
    const legendNames = activeCats.map((c) => c.label);

    const option: any = {
      legend: {
        orient: "horizontal",
        bottom: 0,
        left: "center",
        itemGap: 14,
        itemWidth: 20,
        itemHeight: 3,
        icon: "roundRect",
        textStyle: { color: "#6b7280", fontSize: 11 },
        data: legendNames,
      },
      tooltip: {
        trigger: "axis",
        backgroundColor: "#ffffff",
        borderColor: "#e5e7eb",
        borderWidth: 1,
        padding: [10, 14],
        textStyle: { color: "#374151", fontSize: 12 },
        formatter: (params: any) => {
          if (!Array.isArray(params) || params.length === 0) return "";
          const items = params
            .filter((p: any) => p.value != null && p.value > 0)
            .sort((a: any, b: any) => b.value - a.value);
          if (items.length === 0) return "";
          let html = `<div style="font-weight:bold;margin-bottom:5px;color:#5c4033;">${items[0].axisValue}</div>`;
          let total = 0;
          for (const p of items) {
            total += Number(p.value);
            html += `<div style="display:flex;justify-content:space-between;gap:24px;"><span>${p.marker} ${p.seriesName}</span><b style="color:#374151;">${formatPrice(p.value)} 公斤</b></div>`;
          }
          html += `<div style="margin-top:4px;padding-top:4px;border-top:1px solid #e5e7eb;display:flex;justify-content:space-between;"><span style="color:#9ca3af;">合计</span><b style="color:#374151;">${formatPrice(Number(total.toFixed(2)))} 公斤</b></div>`;
          return html;
        },
      },
      grid: {
        left: 45,
        right: 10,
        bottom: labelOverflow3 ? 44 : 28,
        top: 10,
        containLabel: false,
      },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: dayLabels,
        axisLine: { lineStyle: { color: "#d1d5db" } },
        axisLabel: {
          color: "#9ca3af",
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
        scale: true,
        name: "重量 (公斤)",
        nameTextStyle: { color: "#9ca3af", fontSize: 10 },
        axisLine: { show: true, lineStyle: { color: "#d1d5db" } },
        axisLabel: {
          color: "#9ca3af",
          formatter: (v: number) => v.toFixed(1),
          fontSize: 10,
        },
        splitLine: {
          lineStyle: { color: "#e5e7eb", type: "solid" },
        },
      },
      series,
    };

    speciesWeightChartInstance.setOption(option);
  }, 100);
};

const renderPieChart = () => {
  setTimeout(() => {
    if (!pieChart.value) return;
    if (pieChartInstance) pieChartInstance.dispose();
    pieChartInstance = echarts.init(pieChart.value);

    const speciesTotalWeight = new Map<number, number>();
    speciesWeekWeightMap.value.forEach((spMap) => {
      spMap.forEach((weight, spId) => {
        speciesTotalWeight.set(
          spId,
          (speciesTotalWeight.get(spId) || 0) + weight,
        );
      });
    });

    if (speciesTotalWeight.size === 0 || !Array.isArray(speciesList.value))
      return;

    // 按分类汇总重量
    const categoryWeight = new Map<string, number>();
    let totalWeight = 0;
    speciesTotalWeight.forEach((weight, spId) => {
      const sp = speciesList.value.find((s: any) => s.id === spId);
      if (!sp) return;
      const cat = getSpeciesCategory(sp.name_zh);
      if (cat === "其他") return;
      const w = Number(weight.toFixed(2));
      categoryWeight.set(cat, (categoryWeight.get(cat) || 0) + w);
      totalWeight += w;
    });

    const pieData = categoryDefs
      .filter((def) => categoryWeight.has(def.key))
      .map((def) => ({
        name: def.label,
        value: categoryWeight.get(def.key) || 0,
        itemStyle: { color: def.color },
      }))
      .filter((d) => d.value > 0)
      .sort((a, b) => b.value - a.value);

    if (pieData.length === 0) return;

    const option: any = {
      // 中心文字：总重量
      graphic: [
        {
          type: "text",
          left: "center",
          top: "38%",
          style: {
            text: formatPrice(totalWeight),
            textAlign: "center",
            fill: "#374151",
            fontSize: 20,
            fontWeight: "bold",
            fontFamily:
              "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace",
          },
        },
        {
          type: "text",
          left: "center",
          top: "52%",
          style: {
            text: "公斤",
            textAlign: "center",
            fill: "#9ca3af",
            fontSize: 12,
          },
        },
      ],
      legend: {
        orient: "horizontal",
        bottom: 0,
        left: "center",
        itemGap: 14,
        itemWidth: 8,
        itemHeight: 8,
        borderRadius: 4,
        textStyle: {
          color: "#6b7280",
          fontSize: 11,
        },
      },
      tooltip: {
        trigger: "item",
        backgroundColor: "#ffffff",
        borderColor: "#e5e7eb",
        borderWidth: 1,
        padding: [10, 14],
        textStyle: { color: "#374151", fontSize: 13 },
        formatter: (params: any) => {
          return `<div style="font-size:14px;font-weight:bold;margin-bottom:5px;">${params.marker} ${params.name}</div>
                  <div style="color:#6b7280;">放生重量：<b style="color:#374151;">${formatPrice(params.value)}</b> 公斤</div>
                  <div style="color:#6b7280;">占比：<b style="color:#374151;">${params.percent}%</b></div>`;
        },
      },
      series: [
        {
          type: "pie",
          radius: ["50%", "78%"],
          center: ["50%", "45%"],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 6,
            borderColor: "#fff",
            borderWidth: 3,
          },
          label: {
            show: true,
            position: "inside",
            formatter: (p: any) => {
              if (p.percent < 6) return "";
              return `{pct|${p.percent}%}`;
            },
            rich: {
              pct: {
                fontSize: 14,
                fontWeight: "bold",
                color: "#ffffff",
                textShadowColor: "rgba(0,0,0,0.3)",
                textShadowBlur: 4,
              },
            },
          },
          emphasis: {
            scaleSize: 6,
            itemStyle: {
              shadowBlur: 20,
              shadowOffsetX: 0,
              shadowOffsetY: 6,
              shadowColor: "rgba(0,0,0,0.15)",
            },
            label: {
              show: true,
              fontSize: 16,
              fontWeight: "bold",
            },
          },
          data: pieData,
          animationType: "scale",
          animationEasing: "elasticOut",
          animationDelay: (idx: number) => idx * 120,
        },
      ],
    };

    pieChartInstance.setOption(option);
  }, 100);
};

const handleResize = () => {
  billsChartInstance?.resize();
  speciesWeightChartInstance?.resize();
  pieChartInstance?.resize();
  fluctuationChartInstance?.resize();
  trendChartInstances.forEach((c) => c.resize());
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
  if (pieChartInstance) {
    pieChartInstance.dispose();
    pieChartInstance = null;
  }
  if (fluctuationChartInstance) {
    fluctuationChartInstance.dispose();
    fluctuationChartInstance = null;
  }
  trendChartInstances.forEach((c) => c.dispose());
  trendChartInstances.clear();
  trendChartRefs.clear();
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
