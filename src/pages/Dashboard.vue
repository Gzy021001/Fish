<template>
  <div class="h-full flex flex-col">
    <div
      class="bg-white rounded-2xl shadow-md border border-dunhuang-yellow/30 p-8 flex-1 flex flex-col"
    >
      <div class="flex items-center justify-between mb-8 flex-none">
        <h3
          class="text-2xl font-serif text-dunhuang-blue flex items-center gap-3 font-bold"
        >
          {{ t("dashboard.price_trend") }}
        </h3>
      </div>

      <div class="flex-1 relative min-h-[400px]">
        <div
          v-if="loading"
          class="absolute inset-0 flex items-center justify-center z-20 bg-white/50 backdrop-blur-sm rounded-xl"
        >
          <div
            class="animate-spin rounded-full h-12 w-12 border-b-2 border-dunhuang-blue"
          ></div>
        </div>
        <div
          v-else-if="!hasTrendData && !errorMsg"
          class="absolute inset-0 flex items-center justify-center text-dunhuang-text/50"
        >
          最近暂无价格走势数据
        </div>
        <div
          v-else-if="errorMsg"
          class="absolute inset-0 flex items-center justify-center text-dunhuang-red"
        >
          {{ errorMsg }}
        </div>
        <div
          v-show="hasTrendData"
          ref="chartRef"
          class="absolute inset-0 w-full h-full"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useI18n } from "vue-i18n";
import * as echarts from "echarts";
import api from "../api";
import { isAuthError } from "../lib/error";

// ============================================================
//  仪表盘：品种价格趋势图表
// ============================================================

const { t } = useI18n();

const speciesList = ref<any[]>([]);
// Use an object to store trend data for multiple species: { species_id: trendDataArray }
const trendDataMap = ref<Record<number, any[]>>({});
const loading = ref(false);
const errorMsg = ref("");

const hasTrendData = computed(() => {
  return Object.values(trendDataMap.value).some((data) => data.length > 0);
});

const chartRef = ref<HTMLElement | null>(null);
let chartInstance: echarts.ECharts | null = null;

// Define a color palette for different species lines
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

const fetchSpecies = async () => {
  try {
    errorMsg.value = "";
    const res = await api.get("/species");
    speciesList.value = res.data || [];
    if (speciesList.value.length > 0) {
      await fetchAllTrends();
    }
  } catch (error: any) {
    if (isAuthError(error)) return;
    console.error("Failed to fetch species", error);
    if (error.response && error.response.status === 404) {
      errorMsg.value = "请求的品种数据接口不存在，请检查后端路由。";
    } else if (error.message?.includes("timeout")) {
      errorMsg.value = "请求品种数据超时，请检查网络。";
    } else {
      errorMsg.value = "获取品种数据失败。";
    }
  }
};

const fetchAllTrends = async () => {
  loading.value = true;
  errorMsg.value = "";
  try {
    // Fetch trends for all species concurrently
    const promises = speciesList.value.map((sp) =>
      api
        .get(`/stats/price-trend?species_id=${sp.id}`)
        .then((res) => ({ id: sp.id, data: res.data }))
        .catch((err) => {
          console.error(`Failed to fetch trend for species ${sp.id}`, err);
          return { id: sp.id, data: [] };
        }),
    );

    const results = await Promise.all(promises);
    const newTrendDataMap: Record<number, any[]> = {};

    results.forEach((res) => {
      if (res.data && res.data.length > 0) {
        newTrendDataMap[res.id] = res.data;
      }
    });

    trendDataMap.value = newTrendDataMap;

    if (hasTrendData.value) {
      renderChart();
    }
  } catch (error: any) {
    console.error("Failed to fetch trends", error);
    if (isAuthError(error)) {
      // Let the global interceptor handle the redirect
    } else {
      errorMsg.value = "获取价格走势失败。";
    }
  } finally {
    loading.value = false;
  }
};

const renderChart = () => {
  setTimeout(() => {
    if (!chartRef.value) return;
    if (chartInstance) {
      chartInstance.dispose();
    }

    chartInstance = echarts.init(chartRef.value);

    // Collect all unique dates across all species to form a unified x-axis
    const allDatesSet = new Set<string>();
    Object.values(trendDataMap.value).forEach((dataArray) => {
      dataArray.forEach((item) => allDatesSet.add(item.date));
    });

    // Sort dates chronologically
    const dates = Array.from(allDatesSet).sort(
      (a, b) => new Date(a).getTime() - new Date(b).getTime(),
    );

    // Build series data
    const series = [];
    const legendData = [];

    let colorIndex = 0;

    for (const [spIdStr, dataArray] of Object.entries(trendDataMap.value)) {
      const spId = Number(spIdStr);
      const sp = speciesList.value.find((s) => s.id === spId);
      if (!sp) continue;

      const spName = sp.name_zh;
      legendData.push(spName);

      // Map data to the unified dates array. If a date is missing for this species, it will be null (breaking the line) or we could carry over previous price.
      // ECharts handles nulls well by breaking the line, which is often more accurate than interpolating.
      const pricesMap = new Map<string, number>();
      dataArray.forEach((item) => pricesMap.set(item.date, item.avg_price));

      const prices = dates.map((d) =>
        pricesMap.has(d)
          ? {
              value: pricesMap.get(d),
              label: {
                show: false,
                formatter: (params: any) => params.value.toFixed(2),
              },
            }
          : null,
      );

      const color = colorPalette[colorIndex % colorPalette.length];
      colorIndex++;

      series.push({
        name: spName,
        type: "line",
        smooth: true,
        symbol: "circle",
        symbolSize: 6,
        itemStyle: {
          color: color,
          borderColor: "#faf5ea",
          borderWidth: 1,
        },
        lineStyle: {
          width: 3,
          color: color,
        },
        data: prices,
      });
    }

    const option = {
      legend: {
        data: legendData,
        bottom: 0,
        textStyle: { color: "#3d3226" },
        icon: "circle",
      },
      tooltip: {
        trigger: "axis",
        backgroundColor: "#fdfaf3",
        borderColor: "#c4a35a",
        textStyle: { color: "#3d3226" },
        valueFormatter: (value: number | string) => {
          if (value === null || value === undefined || value === "") return "-";
          // 直接截取两位小数，不进行四舍五入
          const strVal = String(value);
          const dotIndex = strVal.indexOf(".");
          if (dotIndex === -1) {
            return `${strVal}.00`;
          }
          const intPart = strVal.substring(0, dotIndex);
          const decPart = strVal.substring(dotIndex + 1);
          return `${intPart}.${(decPart + "00").substring(0, 2)}`;
        },
      },
      grid: {
        left: "3%",
        right: "4%",
        bottom: "10%",
        top: "5%",
        containLabel: true,
      },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: dates,
        axisLine: { lineStyle: { color: "#c4a35a" } },
        axisLabel: { color: "#3d3226" },
      },
      yAxis: {
        type: "value",
        axisLine: { show: true, lineStyle: { color: "#c4a35a" } },
        axisLabel: {
          color: "#3d3226",
          formatter: (value: number) => {
            const strVal = String(value);
            const dotIndex = strVal.indexOf(".");
            if (dotIndex === -1) {
              return `${strVal}.00`;
            }
            const intPart = strVal.substring(0, dotIndex);
            const decPart = strVal.substring(dotIndex + 1);
            return `${intPart}.${(decPart + "00").substring(0, 2)}`;
          },
        },
        splitLine: {
          lineStyle: { color: "#c4a35a", type: "dashed", opacity: 0.3 },
        },
      },
      series: series,
    };

    chartInstance.setOption(option);
  }, 100);
};

onMounted(() => {
  fetchSpecies();

  window.addEventListener("resize", () => {
    chartInstance?.resize();
  });
});
</script>
