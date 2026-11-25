<template>
  <div class="h-full flex flex-col gap-3 sm:gap-4 min-h-0">
    <!-- 四类合计：支付宝 / 微信1 / 微信2 / 随喜放生 -->
    <div class="shrink-0 grid grid-cols-2 xl:grid-cols-4 gap-3 sm:gap-4">
      <div
        v-for="card in summaryCards"
        :key="card.label"
        class="relative overflow-hidden bg-dunhuang-card rounded-2xl pl-5 pr-4 py-4 sm:py-5 border border-dunhuang-yellow/25 shadow-[0_1px_2px_rgba(74,52,40,0.04),0_14px_28px_-22px_rgba(74,52,40,0.4)] flex flex-col justify-center min-w-0"
      >
        <span class="absolute inset-y-0 left-0 w-[3px]" :class="card.bar"></span>
        <div
          class="text-xs font-medium tracking-wide mb-1.5"
          :class="card.labelClass"
        >
          {{ card.label }}
        </div>
        <div class="flex items-baseline gap-1.5">
          <span
            class="text-[24px] sm:text-[28px] leading-none font-bold tabular-nums"
            :class="card.valueClass"
            >{{ formatMoney(card.value) }}</span
          >
          <span class="text-xs font-medium text-dunhuang-text/40">元</span>
        </div>
      </div>
    </div>

    <!-- 明细列表：页面不滚动，只有表格区域内部滚动 -->
    <div
      class="flex-1 min-h-0 flex flex-col bg-white rounded-2xl shadow-md border border-dunhuang-yellow/30 p-4 sm:p-5"
    >
      <div class="shrink-0 flex flex-wrap items-center justify-between gap-3 mb-3">
        <div class="flex flex-wrap items-center gap-2.5">
          <div class="w-1 h-5 rounded-full bg-dunhuang-yellow shrink-0"></div>
          <h3 class="font-serif font-bold text-dunhuang-blue text-base">
            按放生日期汇总
          </h3>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <DateRangeInput
            v-model:from="filterDateFrom"
            v-model:to="filterDateTo"
            class="w-[264px]"
          />
          <button
            @click="applyFilters"
            class="h-9 px-5 rounded-lg text-sm font-semibold transition-all duration-200 bg-dunhuang-blue text-white shadow-sm hover:bg-dunhuang-blue/90 hover:shadow-md active:scale-[0.98]"
          >
            查询
          </button>
          <button
            @click="resetFilters"
            class="h-9 px-4 rounded-lg text-sm font-medium transition-all duration-200 bg-white text-dunhuang-text/60 border border-dunhuang-yellow/30 shadow-sm hover:text-dunhuang-blue hover:border-dunhuang-blue/30 hover:bg-dunhuang-blue/[0.03] active:scale-[0.98]"
          >
            重置
          </button>
        </div>
      </div>

      <div
        class="flex-1 min-h-0 rounded-lg border border-dunhuang-yellow/30 overflow-hidden flex flex-col"
      >
        <!-- 表头（固定） -->
        <div
          class="shrink-0 grid suixi-grid bg-[#f9f3e7] text-dunhuang-blue font-sans font-bold text-sm"
        >
          <div class="px-3 py-2.5 text-center whitespace-nowrap">序号</div>
          <div class="px-4 py-2.5 text-center whitespace-nowrap">放生日期</div>
          <div class="px-4 py-2.5 text-center whitespace-nowrap">
            支付宝（元）
          </div>
          <div class="px-4 py-2.5 text-center whitespace-nowrap">微信1（元）</div>
          <div class="px-4 py-2.5 text-center whitespace-nowrap">微信2（元）</div>
          <div class="px-4 py-2.5 text-center whitespace-nowrap">
            随喜放生（元）
          </div>
          <div class="px-4 py-2.5 text-center whitespace-nowrap">
            车费/船费（元）
          </div>
        </div>

        <!-- 表体（区域内滚动） -->
        <div class="flex-1 min-h-0 overflow-auto panel-scrollbar">
          <template
            v-for="(row, index) in rows"
            :key="row.release_date ?? `row-${index}`"
          >
            <div
              class="grid suixi-grid text-sm border-b border-dunhuang-yellow/15 hover:bg-[#fbf6ec] transition-colors"
            >
              <div
                class="px-3 py-2 text-center text-dunhuang-text/80 tabular-nums"
              >
                {{ (currentPage - 1) * pageSize + index + 1 }}
              </div>
              <div class="px-4 py-2 text-center font-medium whitespace-nowrap">
                {{ dateStr(row.release_date) || "—" }}
              </div>
              <div class="px-4 py-2 text-center tabular-nums">
                {{ formatMoney(row.alipay_amount) }}
              </div>
              <div class="px-4 py-2 text-center tabular-nums">
                {{ formatMoney(row.wechat1_amount) }}
              </div>
              <div class="px-4 py-2 text-center tabular-nums">
                {{ formatMoney(row.wechat2_amount) }}
              </div>
              <div
                class="px-4 py-2 text-center tabular-nums text-dunhuang-red font-medium"
              >
                {{ formatMoney(row.suixi_amount) }}
              </div>
              <div class="px-4 py-2 text-center tabular-nums text-dunhuang-text/35">
                {{ row.expense_total ? formatMoney(row.expense_total) : "—" }}
              </div>
            </div>

            <!-- 车费/船费：模板表尾的费用行，按天单独列出 -->
            <div
              v-for="item in dayExpenses(row)"
              :key="`${row.release_date}-${item.label}`"
              class="grid suixi-grid text-xs border-b border-dashed border-dunhuang-yellow/20 bg-[#fdf9f1]"
            >
              <div></div>
              <div class="px-4 py-1.5 pl-6 text-dunhuang-text/55">
                └ {{ item.label }}
              </div>
              <div class="col-span-4"></div>
              <div
                class="px-4 py-1.5 text-center tabular-nums"
                :class="item.cls"
              >
                {{ formatMoney(item.value) }}
              </div>
            </div>
          </template>
          <div
            v-if="rows.length === 0"
            class="py-12 text-center text-sm text-dunhuang-text/40"
          >
            {{ loading ? "加载中..." : "暂无随喜记录" }}
          </div>
        </div>

        <!-- 总计（固定底部） -->
        <div
          v-if="rows.length > 0"
          class="shrink-0 grid suixi-grid bg-[#fbf7ee] border-t border-dunhuang-yellow/30 text-xs"
        >
          <div class="px-3 py-2"></div>
          <div class="px-4 py-2 text-center text-dunhuang-text/60 font-medium">
            总计
          </div>
          <div class="px-4 py-2 text-center tabular-nums text-dunhuang-blue">
            {{ formatMoney(sumAlipay) }}
          </div>
          <div class="px-4 py-2 text-center tabular-nums text-dunhuang-green">
            {{ formatMoney(sumWechat1) }}
          </div>
          <div class="px-4 py-2 text-center tabular-nums text-dunhuang-orange">
            {{ formatMoney(sumWechat2) }}
          </div>
          <div class="px-4 py-2 text-center tabular-nums text-dunhuang-red">
            {{ formatMoney(sumSuixi) }}
          </div>
          <div class="px-4 py-2 text-center tabular-nums text-dunhuang-orange">
            {{ formatMoney(sumExpense) }}
          </div>
        </div>
      </div>

      <div class="shrink-0 flex items-center justify-between flex-wrap gap-3 mt-3">
        <div class="text-sm text-dunhuang-text/70">
          共
          <span class="font-bold text-dunhuang-blue">{{ totalItems }}</span>
          天
        </div>

        <Pagination
          v-model:currentPage="currentPage"
          v-model:pageSize="pageSize"
          :totalPages="totalPages"
          :showPageSizeSelect="true"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import DateRangeInput from "../components/DateRangeInput.vue";
import Pagination from "../components/Pagination.vue";
import { dateStr, formatMoney } from "../lib/utils";
import { useSuixiSummary } from "../composables/useSuixiSummary";

const {
  rows,
  filterDateFrom,
  filterDateTo,
  currentPage,
  pageSize,
  totalItems,
  totalPages,
  loading,
  sumAlipay,
  sumWechat1,
  sumWechat2,
  sumSuixi,
  sumExpense,
  fetchSummary,
  applyFilters,
  resetFilters,
} = useSuixiSummary();

/** 当天要单独列出的费用行（车费/船费/其它耗材），没有就不渲染 */
const dayExpenses = (row: {
  expense_car?: number;
  expense_ship?: number;
  expense_other?: number;
}) => {
  const items: { label: string; value: number; cls: string }[] = [
    { label: "车费", value: row.expense_car || 0, cls: "text-dunhuang-orange/85" },
    { label: "船费", value: row.expense_ship || 0, cls: "text-dunhuang-orange/85" },
    { label: "其它支出", value: row.expense_other || 0, cls: "text-dunhuang-text/50" },
  ];
  return items.filter((item) => item.value);
};

// 四张合计卡：标签/强调色随分类走，颜色类名保持字面量以便 Tailwind 扫描
const summaryCards = computed(() => [
  {
    label: "支付宝",
    value: sumAlipay.value,
    bar: "bg-dunhuang-blue",
    labelClass: "text-dunhuang-blue/70",
    valueClass: "text-dunhuang-ink",
  },
  {
    label: "微信1",
    value: sumWechat1.value,
    bar: "bg-dunhuang-green",
    labelClass: "text-dunhuang-green/80",
    valueClass: "text-dunhuang-ink",
  },
  {
    label: "微信2",
    value: sumWechat2.value,
    bar: "bg-dunhuang-orange",
    labelClass: "text-dunhuang-orange/80",
    valueClass: "text-dunhuang-ink",
  },
  {
    label: "随喜放生",
    value: sumSuixi.value,
    bar: "bg-dunhuang-red",
    labelClass: "text-dunhuang-red/80",
    valueClass: "text-dunhuang-red",
  },
]);

onMounted(() => {
  fetchSummary();
});
</script>

<style scoped>
/* 表头 / 数据行 / 总计行共用同一套列宽，保证三处对齐 */
.suixi-grid {
  grid-template-columns:
    64px minmax(88px, 1.15fr) repeat(4, minmax(72px, 1fr))
    minmax(96px, 0.95fr);
}
</style>
