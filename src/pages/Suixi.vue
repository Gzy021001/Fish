<template>
  <div class="h-full flex flex-col gap-3 sm:gap-4 min-h-0">
    <!-- 六类合计：支付宝 / 微信1 / 微信2 / 随喜放生 / 车费 / 船费 -->
    <div class="shrink-0 grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-3 sm:gap-4">
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
        <div class="flex items-baseline gap-1 min-w-0">
          <span
            class="text-[19px] sm:text-[21px] leading-none font-bold tabular-nums whitespace-nowrap"
            :class="card.valueClass"
            >{{ formatMoney(card.value) }}</span
          >
          <span class="text-[11px] font-medium text-dunhuang-text/40">元</span>
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
              class="grid suixi-grid text-sm transition-all duration-200 border-b border-dunhuang-yellow/15"
              :class="
                expandedKeys.has(rowKey(row, index))
                  ? 'bg-[#fdf7ea] shadow-[inset_3px_0_0_rgba(191,160,95,0.75)]'
                  : row.expense_total
                    ? 'cursor-pointer hover:bg-[#fbf6ec]'
                    : 'hover:bg-[#fbf6ec]'
              "
              :title="row.expense_total ? '点击展开/收起当天费用明细' : ''"
              @click="row.expense_total && toggleExpanded(rowKey(row, index))"
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
              <div
                class="px-4 py-2 flex items-center justify-center gap-1.5 tabular-nums"
                :class="
                  row.expense_total ? 'text-dunhuang-text/80' : 'text-dunhuang-text/30'
                "
              >
                <span>{{
                  row.expense_total ? formatMoney(row.expense_total) : "—"
                }}</span>
                <span
                  v-if="row.expense_total"
                  class="w-[18px] h-[18px] shrink-0 rounded-full flex items-center justify-center transition-colors duration-200"
                  :class="
                    expandedKeys.has(rowKey(row, index))
                      ? 'bg-dunhuang-yellow/30 text-dunhuang-blue'
                      : 'bg-dunhuang-yellow/12 text-dunhuang-text/45'
                  "
                >
                  <svg
                    class="w-3 h-3 transition-transform duration-200"
                    :class="
                      expandedKeys.has(rowKey(row, index)) ? 'rotate-90' : ''
                    "
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2.5"
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </span>
              </div>
            </div>

            <!-- 车费/船费/耗材：点日期行展开，缩进 + 色点标识 -->
            <template v-if="expandedKeys.has(rowKey(row, index))">
              <div
                v-for="(item, subIndex) in dayExpenses(row)"
                :key="`${rowKey(row, index)}-${item.label}`"
                class="grid suixi-grid text-xs bg-[#fdfaf2] border-b border-dunhuang-yellow/10 last-of-type:border-dunhuang-yellow/25"
              >
                <div
                  class="flex items-center justify-center"
                  :class="subIndex === 0 ? 'border-l-[3px]' : 'border-l-[3px]'"
                  :style="{ borderLeftColor: 'rgba(191,160,95,0.35)' }"
                >
                  <span class="w-1 h-1 rounded-full bg-dunhuang-yellow/50"></span>
                </div>
                <div class="px-4 py-1.5 pl-5 flex items-center gap-1.5">
                  <span
                    class="w-1.5 h-1.5 rounded-full shrink-0"
                    :class="item.dot"
                  ></span>
                  <span class="text-dunhuang-text/60" :title="item.tip">{{
                    item.label
                  }}</span>
                </div>
                <div
                  v-if="item.detail"
                  class="col-span-4 px-3 py-1.5 text-[11px] text-dunhuang-text/40 truncate"
                  :title="item.detail"
                >
                  {{ item.detail }}
                </div>
                <div v-else class="col-span-4"></div>
                <div
                  class="px-4 py-1.5 text-center tabular-nums"
                  :class="item.cls"
                >
                  {{ formatMoney(item.value) }}
                </div>
              </div>
            </template>
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
import { computed, onMounted, ref } from "vue";
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
  sumExpenseCar,
  sumExpenseShip,
  sumExpense,
  fetchSummary,
  applyFilters,
  resetFilters,
} = useSuixiSummary();

/** 当天要单独列出的费用行（车费/船费/耗材），没有就不渲染 */
const dayExpenses = (row: {
  expense_car?: number;
  expense_ship?: number;
  expense_other?: number;
  expense_other_items?: { name: string; amount: number }[];
}) => {
  const items: {
    label: string;
    value: number;
    cls: string;
    dot: string;
    detail?: string;
    tip?: string;
  }[] = [
    {
      label: "车费",
      value: row.expense_car || 0,
      cls: "text-dunhuang-orange/85",
      dot: "bg-dunhuang-orange/70",
    },
    {
      label: "船费",
      value: row.expense_ship || 0,
      cls: "text-dunhuang-green/80",
      dot: "bg-dunhuang-green/60",
    },
    {
      label: "耗材",
      value: row.expense_other || 0,
      cls: "text-dunhuang-text/60",
      dot: "bg-dunhuang-yellow/70",
      // 具体是哪些：冰块/大冰块/空运袋…… 名称+金额，小字展示
      detail: (row.expense_other_items || [])
        .map((item) => `${item.name} ${formatMoney(item.amount)}`)
        .join(" · "),
      tip: "模板里没有对应物命单据的支出（冰块/打包袋等耗材）",
    },
  ];
  return items.filter((item) => item.value);
};

/** 行的稳定键：同一天一行，没有日期时退回序号 */
const rowKey = (
  row: { release_date: string | null },
  index: number,
): string => row.release_date || `row-${index}`;

/** 展开中的日期行（点整行切换） */
const expandedKeys = ref<Set<string>>(new Set());
const toggleExpanded = (key: string) => {
  const next = new Set(expandedKeys.value);
  if (next.has(key)) {
    next.delete(key);
  } else {
    next.add(key);
  }
  expandedKeys.value = next;
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
  {
    label: "车费",
    value: sumExpenseCar.value,
    bar: "bg-dunhuang-orange",
    labelClass: "text-dunhuang-orange/80",
    valueClass: "text-dunhuang-ink",
  },
  {
    label: "船费",
    value: sumExpenseShip.value,
    bar: "bg-dunhuang-yellow",
    labelClass: "text-dunhuang-yellow/90",
    valueClass: "text-dunhuang-ink",
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
