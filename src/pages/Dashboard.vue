<template>
  <div class="h-full flex flex-col space-y-6">
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
      class="bg-white rounded-2xl shadow-md border border-dunhuang-yellow/30 p-8 flex flex-col"
    >
      <div class="flex items-center justify-between mb-6 flex-none">
        <h3
          class="text-2xl font-serif text-dunhuang-blue flex items-center gap-3 font-bold"
        >
          {{ t("dashboard.price_trend") }}
        </h3>
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
          ref="priceChartRef"
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

      <div
        v-if="hasSpeciesWeightData"
        class="relative overflow-hidden rounded-2xl bg-gradient-to-br from-dunhuang-bg to-dunhuang-card border border-dunhuang-yellow/25 px-5 py-3.5 shadow-sm mb-4 flex-none self-start"
      >
        <div
          class="absolute top-0 right-0 w-14 h-14 rounded-bl-full bg-dunhuang-blue/5 -mr-3 -mt-3"
        ></div>
        <div class="relative z-10 flex items-baseline gap-2 whitespace-nowrap">
          <div class="w-1.5 h-1.5 rounded-full bg-dunhuang-blue shrink-0"></div>
          <span class="text-xs text-dunhuang-text/40 tracking-wider uppercase"
            >总重量</span
          >
          <span class="text-xl font-bold text-dunhuang-blue tabular-nums">{{
            formatPrice(grandTotalWeight)
          }}</span>
          <span class="text-xs text-dunhuang-text/40">公斤</span>
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

const priceChartRef = ref<HTMLElement | null>(null);
const billsChartRef = ref<HTMLElement | null>(null);
const speciesWeightChartRef = ref<HTMLElement | null>(null);
let priceChartInstance: echarts.ECharts | null = null;
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

const dayLabel = (dateStr: string): string => {
  const d = new Date(dateStr);
  return `${d.getMonth() + 1}/${d.getDate()}`;
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
    if (hasTrendData.value) renderPriceChart();
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
    const promises = speciesList.value.map((sp) =>
      api
        .get(
          `/stats/price-trend?species_id=${sp.id}&year=${selectedYear.value}`,
        )
        .then((res) => ({ id: sp.id, data: res.data }))
        .catch((err) => {
          console.error(`Failed to fetch trend for species ${sp.id}`, err);
          return { id: sp.id, data: [] };
        }),
    );
    const results = await Promise.all(promises);
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
    const res = await api.get("/bills?limit=0");
    const bills = res.data || [];
    const map = new Map<
      string,
      { total_amount: number; total_weight: number }
    >();
    const spWeightMap = new Map<string, Map<number, number>>();
    for (const b of bills) {
      if (!b.created_at) continue;
      const d = new Date(b.created_at);
      if (d.getFullYear() !== selectedYear.value) continue;
      const key = d.toISOString().slice(0, 10);
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
  if (hasTrendData.value) renderPriceChart();
  if (hasBillData.value) renderBillsChart();
  if (hasSpeciesWeightData.value) renderSpeciesWeightChart();
};

// ---- 日数据提取 ----

const computeDayData = () => {
  const allDaySet = new Set<string>();
  Object.values(trendDataMap.value).forEach((dataArray) => {
    dataArray.forEach((item) => {
      if (item.date) {
        allDaySet.add(item.date);
      }
    });
  });
  billWeekMap.value.forEach((_, k) => allDaySet.add(k));

  const dayKeys = Array.from(allDaySet).sort();
  const dayLabels = dayKeys.map((k) => dayLabel(k));

  return { dayKeys, dayLabels };
};

// ---- 图表1: 价格走势 ----

const renderPriceChart = () => {
  setTimeout(() => {
    if (!priceChartRef.value) return;
    if (priceChartInstance) priceChartInstance.dispose();

    priceChartInstance = echarts.init(priceChartRef.value);

    const { dayKeys, dayLabels } = computeDayData();

    if (dayKeys.length === 0) return;

    const series: any[] = [];
    const legendData: string[] = [];
    let colorIndex = 0;

    for (const [spIdStr, dataArray] of Object.entries(trendDataMap.value)) {
      const spId = Number(spIdStr);
      const sp = speciesList.value.find((s) => s.id === spId);
      if (!sp) continue;

      const spName = sp.name_zh;
      legendData.push(spName);

      const dayPriceMap = new Map<string, number>();
      dataArray.forEach((item: any) => {
        if (!item.date || item.avg_price == null) return;
        dayPriceMap.set(item.date, Number(item.avg_price));
      });

      const prices = dayKeys.map((dk) => {
        const price = dayPriceMap.get(dk);
        return price != null ? Number(price.toFixed(2)) : null;
      });

      const color = colorPalette[colorIndex % colorPalette.length];
      colorIndex++;

      series.push({
        name: spName,
        type: "line",
        smooth: true,
        symbol: "circle",
        symbolSize: 8,
        itemStyle: { color, borderColor: color, borderWidth: 1.5 },
        lineStyle: { width: 2.5, color },
        data: prices,
        unit: sp.default_unit ?? "",
      });
    }

    if (series.length === 0) return;

    const option: any = {
      legend: {
        data: legendData,
        bottom: 8,
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
          const unit = option.series?.[params.seriesIndex]?.unit ?? "";
          const unitSuffix = unit ? ` /${unit}` : "";
          return `${params.marker} ${params.seriesName}:${formatPrice(params.value)}${unitSuffix}`;
        },
      },
      grid: {
        left: "4%",
        right: "6%",
        bottom: "12%",
        top: "10%",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        boundaryGap: true,
        data: dayLabels,
        axisLine: { lineStyle: { color: "#c4a35a" } },
        axisLabel: { color: "#3d3226", fontSize: 10 },
        axisTick: { show: false },
      },
      yAxis: {
        type: "value",
        name: "均价 (元)",
        nameTextStyle: { color: "#3d322660", fontSize: 10 },
        axisLine: { show: true, lineStyle: { color: "#c4a35a" } },
        axisLabel: {
          color: "#3d3226",
          formatter: (v: number) => formatPrice(v),
          fontSize: 10,
        },
        splitLine: {
          lineStyle: { color: "#c4a35a", type: "dashed", opacity: 0.2 },
        },
      },
      series,
    };

    priceChartInstance.setOption(option);
  }, 100);
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
    if (dayKeys.length === 0) return;

    const dayLabels = dayKeys.map((k) => dayLabel(k));

    const weightData = dayKeys.map((dk) => {
      const b = billWeekMap.value.get(dk);
      return b ? Number(b.total_weight.toFixed(2)) : 0;
    });

    const amountData = dayKeys.map((dk) => {
      const b = billWeekMap.value.get(dk);
      return b ? Number(b.total_amount.toFixed(2)) : 0;
    });

    const option: any = {
      legend: {
        data: ["总重量", "总金额"],
        bottom: 8,
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
        bottom: "12%",
        top: "10%",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        boundaryGap: true,
        data: dayLabels,
        axisLine: { lineStyle: { color: "#c4a35a" } },
        axisLabel: { color: "#3d3226", fontSize: 10 },
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
    };

    billsChartInstance.setOption(option);
  }, 100);
};

// ---- 图表3: 每周物命总重量 ----

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
    const legendData: string[] = [];
    let colorIndex = 0;

    for (const sp of activeSpecies) {
      const spName = sp.name_zh;
      legendData.push(spName);

      const data = dayKeys.map((dk) => {
        const spMap = speciesWeekWeightMap.value.get(dk);
        if (!spMap) return 0;
        return Number((spMap.get(sp.id) || 0).toFixed(2));
      });

      const color = colorPalette[colorIndex % colorPalette.length];
      colorIndex++;

      series.push({
        name: spName,
        type: "bar",
        stack: "total",
        barWidth: "8%",
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
      barWidth: "8%",
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

    const option: any = {
      legend: {
        data: legendData,
        bottom: 8,
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
          return `${params.marker} ${params.seriesName}：${formatPrice(params.value)} 公斤`;
        },
      },
      grid: {
        left: "4%",
        right: "6%",
        bottom: "12%",
        top: "10%",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        boundaryGap: true,
        data: dayLabels,
        axisLine: { lineStyle: { color: "#c4a35a" } },
        axisLabel: { color: "#3d3226", fontSize: 10 },
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
    };

    speciesWeightChartInstance.setOption(option);
  }, 100);
};

const handleResize = () => {
  priceChartInstance?.resize();
  billsChartInstance?.resize();
  speciesWeightChartInstance?.resize();
};

onMounted(() => {
  fetchSpecies();
  window.addEventListener("resize", handleResize);
});

onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
  if (priceChartInstance) {
    priceChartInstance.dispose();
    priceChartInstance = null;
  }
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
</style>
