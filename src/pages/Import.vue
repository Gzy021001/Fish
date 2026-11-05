<template>
  <div class="h-full flex flex-col">
    <div
      class="bg-white rounded-2xl shadow-md border border-dunhuang-yellow/30 p-8 flex-1 flex flex-col min-h-0"
    >
      <div
        class="flex items-center justify-between mb-8 border-b-2 border-dunhuang-yellow/30 pb-4 shrink-0"
      >
        <div class="flex items-center gap-4">
          <button
            @click="goBack"
            class="text-dunhuang-text/60 hover:text-dunhuang-blue transition-colors flex items-center justify-center w-8 h-8 rounded-full hover:bg-dunhuang-yellow/20"
            title="返回"
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
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
          </button>
          <h2 class="text-2xl font-serif text-dunhuang-blue m-0 font-bold">
            批量导入单据
          </h2>
        </div>
        <button
          @click="downloadTemplate"
          class="h-10 px-5 bg-dunhuang-blue hover:bg-dunhuang-green text-white rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5"
        >
          <svg
            class="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            />
          </svg>
          下载模板
        </button>
      </div>

      <div class="flex-1 flex flex-col min-h-0">
        <!-- Step 1: Upload -->
        <div
          v-if="currentStep === 1"
          class="flex-1 flex flex-col items-center justify-center"
        >
          <div class="text-center">
            <div
              class="border-2 border-dashed rounded-2xl p-14 text-center transition-all duration-200 cursor-pointer"
              :class="
                parsing
                  ? 'pointer-events-none opacity-60 border-dunhuang-yellow/40'
                  : isDragging
                    ? 'border-dunhuang-blue bg-dunhuang-blue/5'
                    : 'border-dunhuang-yellow/40 hover:border-dunhuang-blue hover:bg-dunhuang-yellow/5'
              "
              @click="triggerFileInput"
              @dragover.prevent="isDragging = true"
              @dragleave="onDragLeave"
              @drop.prevent="onDrop"
            >
              <input
                type="file"
                ref="fileInput"
                accept=".xlsx, .xls"
                class="hidden"
                @change="handleFileUpload"
              />
              <div
                class="bg-dunhuang-yellow/10 rounded-full w-16 h-16 mx-auto mb-5 flex items-center justify-center transition-transform duration-200"
                :class="isDragging ? 'scale-110' : ''"
              >
                <svg
                  class="w-8 h-8 text-dunhuang-yellow/70"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.5"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
              </div>
              <p class="text-base font-serif text-dunhuang-text/70 mb-1">
                点击或拖拽文件到此处上传
              </p>
              <p class="text-sm text-dunhuang-text/40">支持 .xlsx、.xls 格式</p>
            </div>
            <div
              v-if="parsing"
              class="mt-4 flex items-center justify-center gap-2 text-sm text-dunhuang-text/60"
            >
              <span
                class="animate-spin rounded-full h-4 w-4 border-2 border-dunhuang-yellow/30 border-t-dunhuang-blue"
              ></span>
              正在解析 Excel 文件...
            </div>
          </div>
        </div>

        <!-- Step 2: Column Mapping + Preview -->
        <div
          v-else-if="currentStep === 2"
          class="flex-1 flex flex-col min-h-0 space-y-5"
        >
          <!-- Column Mapping Card -->
          <div
            class="bg-white rounded-xl border border-dunhuang-yellow/20 shrink-0 overflow-hidden"
          >
            <div
              class="flex items-center justify-between px-5 py-3 bg-dunhuang-yellow/10 border-b border-dunhuang-yellow/20"
            >
              <span class="text-sm font-semibold text-dunhuang-blue font-serif"
                >列映射</span
              >
              <span class="text-xs text-dunhuang-text/50"
                >已根据表头自动识别，未识别的列不会导入</span
              >
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 p-4">
              <div
                v-for="(label, key) in keyLabels"
                :key="key"
                class="flex flex-col gap-1.5 px-3 py-2.5 rounded-lg border bg-dunhuang-yellow/[0.04]"
                :class="
                  detectedColumns[key] ||
                  (key === 'release_date' && sheetDateLabel)
                    ? 'border-dunhuang-yellow/25'
                    : 'border-dunhuang-red/15'
                "
              >
                <span class="text-[11px] text-dunhuang-text/50 font-medium">{{
                  label
                }}</span>
                <span
                  v-if="detectedColumns[key]"
                  class="flex items-center gap-1.5 text-sm text-dunhuang-green font-semibold min-w-0"
                >
                  <svg
                    class="w-3.5 h-3.5 shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2.5"
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                  <span class="truncate">{{ detectedColumns[key] }}</span>
                </span>
                <span
                  v-else-if="key === 'release_date' && sheetDateLabel"
                  class="flex items-center gap-1.5 text-sm text-dunhuang-orange font-semibold min-w-0"
                >
                  <svg
                    class="w-3.5 h-3.5 shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                    />
                  </svg>
                  <span class="truncate">{{ sheetDateLabel }}（Sheet 标题）</span>
                </span>
                <span
                  v-else
                  class="flex items-center gap-1.5 text-sm text-dunhuang-red/70"
                >
                  <svg
                    class="w-3.5 h-3.5 shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                  未识别
                </span>
              </div>
            </div>
          </div>

          <!-- Preview Table -->
          <div
            class="flex-1 min-h-0 border border-dunhuang-yellow/30 rounded-xl overflow-hidden flex flex-col"
          >
            <div
              class="flex items-center justify-between gap-3 px-4 py-3 bg-dunhuang-yellow/10 border-b border-dunhuang-yellow/20 shrink-0"
            >
              <span class="text-sm font-semibold text-dunhuang-blue font-serif"
                >预览数据</span
              >
              <div class="flex items-center gap-4">
                <span class="text-xs text-dunhuang-text/60"
                  >共
                  <b class="text-dunhuang-blue">{{ importRows.length }}</b>
                  条</span
                >
                <span
                  v-if="skippedRows.length > 0"
                  class="flex items-center gap-1.5 text-xs text-dunhuang-text/60"
                >
                  <span class="w-1 h-3 rounded-full bg-dunhuang-orange/60 shrink-0"></span>
                  跳过
                  <b class="text-dunhuang-orange">{{ skippedRows.length }}</b>
                  行
                  <button
                    @click="showSkipped = !showSkipped"
                    class="ml-1 text-dunhuang-blue hover:text-dunhuang-green font-medium transition-colors"
                  >
                    {{ showSkipped ? "收起原因" : "查看原因" }}
                  </button>
                </span>
                <span
                  v-if="newSpeciesNames.length > 0"
                  class="flex items-center gap-1.5 text-xs text-dunhuang-text/60"
                >
                  <span class="w-1 h-3 rounded-full bg-dunhuang-orange/60 shrink-0"></span>
                  将自动新建
                  <b class="text-dunhuang-orange">{{ newSpeciesNames.length }}</b>
                  个品种
                </span>
              </div>
            </div>
            <div
              v-if="showSkipped && skippedRows.length > 0"
              class="shrink-0 max-h-36 overflow-y-auto panel-scrollbar bg-dunhuang-yellow/5 px-4 py-2 border-b border-dunhuang-yellow/20"
            >
              <div
                v-for="(s, i) in skippedRows.slice(0, 100)"
                :key="i"
                class="text-xs text-dunhuang-text/60 py-1 border-b border-dunhuang-yellow/10 last:border-0"
              >
                第 {{ s.rowIndex }} 行：{{ s.reason }}
              </div>
            </div>
            <div class="flex-1 overflow-y-auto panel-scrollbar">
              <table class="w-full table-fixed text-left border-collapse">
                <colgroup>
                  <col style="width: 56px" />
                  <col />
                  <col style="width: 15%" />
                  <col style="width: 12%" />
                  <col style="width: 12%" />
                  <col style="width: 16%" />
                </colgroup>
                <thead class="sticky top-0 z-10">
                  <tr class="bg-[#fbf6ec] text-dunhuang-blue">
                    <th class="px-3 py-2.5 border-b border-dunhuang-yellow/40 text-center text-xs font-semibold">#</th>
                    <th class="px-4 py-2.5 border-b border-dunhuang-yellow/40 text-center text-xs font-semibold">品种</th>
                    <th class="px-4 py-2.5 border-b border-dunhuang-yellow/40 text-center text-xs font-semibold">重量（公斤）</th>
                    <th class="px-4 py-2.5 border-b border-dunhuang-yellow/40 text-center text-xs font-semibold">单价（元）</th>
                    <th class="px-4 py-2.5 border-b border-dunhuang-yellow/40 text-center text-xs font-semibold">服务费（元）</th>
                    <th class="px-4 py-2.5 border-b border-dunhuang-yellow/40 text-center text-xs font-semibold">放生日期</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="(row, index) in importRows"
                    :key="index"
                    class="transition-colors hover:bg-dunhuang-yellow/10"
                    :class="
                      index % 2 === 1 ? 'bg-dunhuang-yellow/[0.04]' : 'bg-white'
                    "
                  >
                    <td class="px-3 py-2.5 text-center text-xs text-dunhuang-text/40 tabular-nums border-b border-dunhuang-yellow/10">
                      {{ index + 1 }}
                    </td>
                    <td class="px-4 py-2.5 text-center text-sm text-dunhuang-text font-medium border-b border-dunhuang-yellow/10">
                      <span class="inline-flex max-w-full items-center gap-1">
                        <span class="truncate">{{ row.name_zh }}</span>
                        <span
                          v-if="isNewSpecies(row.name_zh)"
                          class="shrink-0 text-[10px] leading-none px-1 py-0.5 rounded bg-dunhuang-orange/10 text-dunhuang-orange border border-dunhuang-orange/25"
                          >新建</span
                        >
                      </span>
                    </td>
                    <td class="px-4 py-2.5 text-center text-sm tabular-nums text-dunhuang-text/80 border-b border-dunhuang-yellow/10">
                      {{ formatMoney(row.weight) }}
                    </td>
                    <td class="px-4 py-2.5 text-center text-sm tabular-nums text-dunhuang-text/80 border-b border-dunhuang-yellow/10">
                      {{ formatMoney(row.unit_price) }}
                    </td>
                    <td
                      v-if="feeMergeMap.get(index) !== 0"
                      class="px-4 py-2.5 text-center text-sm tabular-nums align-middle border border-dunhuang-yellow/10"
                      :rowspan="feeMergeMap.get(index) || undefined"
                      :class="
                        row.fee_value > 0
                          ? 'text-dunhuang-orange font-semibold bg-dunhuang-orange/[0.06]'
                          : 'text-dunhuang-text/40'
                      "
                    >
                      {{ formatMoney(row.fee_value) }}
                    </td>
                    <td class="px-4 py-2.5 text-center text-sm text-dunhuang-text/60 whitespace-nowrap border-b border-dunhuang-yellow/10">
                      {{ dateStr(row.release_date) || "-" }}
                    </td>
                  </tr>
                  <tr v-if="importRows.length === 0">
                    <td
                      colspan="6"
                      class="px-4 py-16 text-center text-sm text-dunhuang-text/40"
                    >
                      未解析到有效数据
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Step 2 Actions -->
          <div class="flex justify-between items-center shrink-0 pt-1 gap-3">
            <button
              @click="cancelImport"
              class="h-10 px-6 border border-dunhuang-yellow text-dunhuang-text rounded-lg hover:bg-dunhuang-yellow/20 transition-colors text-sm"
            >
              取消
            </button>
            <div class="flex items-center gap-4">
              <span class="text-xs text-dunhuang-text/50 hidden sm:block">
                将导入
                <b class="text-dunhuang-blue">{{ importRows.length }}</b>
                条单据
              </span>
              <label
                class="flex items-center gap-1.5 text-xs text-dunhuang-text/60 cursor-pointer select-none"
              >
                <input
                  type="checkbox"
                  v-model="overwriteSameDate"
                  class="custom-checkbox text-dunhuang-blue outline-none"
                />
                覆盖同日已有单据
              </label>
              <button
                @click="confirmImport"
                class="h-10 px-6 bg-dunhuang-red text-white rounded-lg hover:bg-dunhuang-red/90 transition-colors text-sm disabled:opacity-70"
                :disabled="importRows.length === 0"
              >
                确认导入
              </button>
            </div>
          </div>
        </div>

        <!-- Step 3: Result -->
        <div
          v-else-if="currentStep === 3"
          class="flex-1 flex flex-col items-center justify-center text-center"
        >
          <div v-if="importing" class="w-full max-w-md">
            <div
              class="bg-white rounded-2xl border border-dunhuang-yellow/30 shadow-sm px-8 py-10 flex flex-col items-center gap-5"
            >
              <div class="relative w-14 h-14">
                <div class="absolute inset-0 rounded-full bg-dunhuang-blue/10"></div>
                <div
                  class="absolute inset-0 animate-spin rounded-full border-[3px] border-dunhuang-yellow/25 border-t-dunhuang-blue"
                ></div>
              </div>
              <div class="text-center space-y-1.5">
                <p class="text-base font-serif font-semibold text-dunhuang-blue">
                  正在导入数据
                </p>
                <p class="text-sm text-dunhuang-text/50">
                  {{ importProgress || "正在连接服务器..." }}
                </p>
                <p class="text-xs text-dunhuang-text/40">请勿关闭或刷新页面</p>
              </div>
              <div class="w-full">
                <div
                  class="flex items-center justify-between text-xs text-dunhuang-text/50 mb-1.5"
                >
                  <span class="tabular-nums">
                    {{
                      importTotal > 0
                        ? `第 ${importDone}/${importTotal} 批`
                        : "准备中"
                    }}
                  </span>
                  <span class="tabular-nums">{{ importPercent }}%</span>
                </div>
                <div
                  class="h-2 w-full rounded-full bg-dunhuang-yellow/15 overflow-hidden"
                >
                  <div
                    class="h-full rounded-full bg-dunhuang-blue transition-all duration-300 ease-out"
                    :style="{ width: importPercent + '%' }"
                  ></div>
                </div>
                <p class="mt-2.5 text-xs text-dunhuang-text/40 text-center">
                  共 {{ importRows.length }} 条单据，分批导入中
                </p>
              </div>
            </div>
          </div>
          <div v-else class="space-y-5">
            <div v-if="importResult" class="space-y-3">
              <div
                class="w-16 h-16 mx-auto rounded-full flex items-center justify-center"
                :class="
                  importResult.errors.length > 0
                    ? 'bg-dunhuang-yellow/20'
                    : 'bg-dunhuang-green/20'
                "
              >
                <svg
                  v-if="importResult.errors.length === 0"
                  class="w-8 h-8 text-dunhuang-green"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                <svg
                  v-else
                  class="w-8 h-8 text-dunhuang-yellow"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
                  />
                </svg>
              </div>
              <p class="text-xl font-serif text-dunhuang-blue font-bold">
                导入完成
              </p>
              <div class="text-sm text-dunhuang-text/70 space-y-1">
                <p>
                  成功导入
                  <b class="text-dunhuang-green">{{
                    importResult.success_count
                  }}</b>
                  条
                </p>
                <p v-if="importResult.skip_count > 0">
                  跳过
                  <b class="text-dunhuang-yellow">{{
                    importResult.skip_count
                  }}</b>
                  条
                </p>
              </div>
              <div
                v-if="importResult.errors.length > 0"
                class="max-h-32 overflow-y-auto mt-3 text-left text-xs bg-dunhuang-yellow/5 rounded-lg p-3"
              >
                <div
                  v-for="(err, i) in importResult.errors"
                  :key="i"
                  class="text-dunhuang-text/60 py-0.5 border-b border-dunhuang-yellow/10 last:border-0"
                >
                  {{ err }}
                </div>
              </div>
            </div>
            <div class="flex gap-3 mt-6">
              <button
                @click="
                  currentStep = 1;
                  cancelImport();
                "
                class="h-10 px-6 border border-dunhuang-yellow text-dunhuang-text rounded-lg hover:bg-dunhuang-yellow/20 transition-colors text-sm"
              >
                继续导入
              </button>
              <button
                @click="goBack"
                class="h-10 px-6 bg-dunhuang-blue text-white rounded-lg hover:bg-dunhuang-green transition-colors text-sm"
              >
                返回列表
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, shallowRef, onMounted } from "vue";
import { useRouter } from "vue-router";
import * as XLSX from "xlsx";
import { apiErrorMessage, isAuthError } from "../lib/error";
import { dateStr, formatMoney } from "../lib/utils";
import { useToast } from "../composables/useToast";
import { useSpecies } from "../composables/useSpecies";
import { saveImportedRowsBatch, saveImportedRowsChunked } from "../services/billingEntryService";
import api from "../api";
import {
  detectColumns,
  parseImportRows,
  parseExcelDate,
  normalizeSpeciesName,
  extractRowPayments,
  type ParsedRow,
  type SkippedRow,
} from "../lib/importUtils";

// 本地辅助函数：从填满的二维数组中寻找表头
function getMatrixHeaders(matrix: any[][]) {
  const kw = [
    "品种",
    "品名",
    "名称",
    "物种",
    "重量",
    "公斤",
    "斤",
    "单价",
    "价格",
    "总计",
    "实付",
    "服务费",
    "日期",
    "鱼",
  ];
  for (let r = 0; r < Math.min(15, matrix.length); r++) {
    const row = matrix[r];
    if (!row) continue;
    const vals: string[] = [];
    const matched = new Set<string>();
    for (let c = 0; c < row.length; c++) {
      const v = String(row[c] ?? "").trim();
      vals.push(v);
      for (const k of kw) {
        if (v.includes(k)) matched.add(k);
      }
    }
    // 必须命中 2 个以上**不同**的关键字才算表头行
    if (matched.size >= 2) return { headers: vals, headerRow: r };
  }
  return { headers: [], headerRow: 0 };
}

const router = useRouter();
const toast = useToast();
const { speciesList, fetchSpecies } = useSpecies();
const currentStep = ref(1);
const fileInput = ref<HTMLInputElement | null>(null);
const showPreview = ref(false);
const importing = ref(false);
const overwriteSameDate = ref(true); // 覆盖同日已有单据（默认开启）
const importResult = ref<{
  success_count: number;
  skip_count: number;
  errors: string[];
} | null>(null);
const importRows = shallowRef<any[]>([]);
const detectedColumns = shallowRef<Record<string, string | null>>({});
const sheetDateLabel = ref<string | null>(null);
const importProgress = ref("");  // 分片导入进度文字
const importDone = ref(0);   // 已完成的导入批次
const importTotal = ref(0);  // 总批次
const importPercent = computed(() =>
  importTotal.value > 0
    ? Math.round((importDone.value / importTotal.value) * 100)
    : 0,
);
// 服务费合并单元格：key=行索引, value=rowspan（0 表示该行被上方合并覆盖，跳过渲染）
const feeMergeMap = shallowRef<Map<number, number>>(new Map());
// 拖拽上传高亮
const isDragging = ref(false);
// 解析 Excel 中（文件较大时主线程解析需要时间，给用户反馈）
const parsing = ref(false);
// 未通过校验的行（含原因），供预览区提示
const skippedRows = shallowRef<SkippedRow[]>([]);
const showSkipped = ref(false);

// ===== 品种库校验：标注不在品种库中的品种（导入时后端会自动新建） =====
const existingSpeciesNames = computed(() => {
  const names = new Set<string>()
  for (const sp of speciesList.value) {
    names.add(normalizeSpeciesName(sp.name_zh))
  }
  return names
});

const isNewSpecies = (name: string) =>
  !!name && !existingSpeciesNames.value.has(normalizeSpeciesName(name));

const newSpeciesNames = computed(() => {
  const names = new Set<string>()
  for (const row of importRows.value as ParsedRow[]) {
    const nm = normalizeSpeciesName(row.name_zh ?? "")
    if (nm && !existingSpeciesNames.value.has(nm)) names.add(nm)
  }
  return Array.from(names)
});

onMounted(() => {
  // 进入页面时提前唤醒服务器，避免后续导入时因冷启动导致超时
  api.get("/health").catch(() => {});
  // 预取品种库，用于预览区标注"将自动新建"的品种
  fetchSpecies();
});

const keyLabels: Record<string, string> = {
  species: "品种",
  weight: "重量",
  unit_price: "单价",
  fee_value: "服务费",
  release_date: "日期",
};

const goBack = () => {
  router.push("/billing");
};

const triggerFileInput = () => {
  if (fileInput.value) {
    fileInput.value.value = "";
    fileInput.value.click();
  }
};

const downloadTemplate = () => {
  const a = document.createElement("a");
  a.href = "/单据导入模板.xlsx";
  a.download = "单据导入模板.xlsx";
  a.click();
};

const cancelImport = () => {
  showPreview.value = false;
  importRows.value = [];
  detectedColumns.value = {};
  sheetDateLabel.value = null;
  importResult.value = null;
  feeMergeMap.value = new Map();
  importProgress.value = "";
  importDone.value = 0;
  importTotal.value = 0;
  skippedRows.value = [];
  showSkipped.value = false;
  isDragging.value = false;
  parsing.value = false;
};

// --- Matrix helpers ---

const GAP_CUTOFF = 5;

function cellVal(ws: XLSX.WorkSheet, r: number, c: number): any {
  const cell = ws[XLSX.utils.encode_cell({ r, c })];

  return cell && cell.v !== undefined ? cell.v : "";
}

function buildMatrix(
  ws: XLSX.WorkSheet,
  range: XLSX.Range,
  maxCols: number,
): { matrix: any[][]; lastRow: number } {
  const matrix: any[][] = [];

  let emptyRun = 0;

  let lastNonEmpty = range.s.r;

  for (let r = range.s.r; r <= range.e.r; r++) {
    const row: any[] = [];

    let hasContent = false;

    for (let c = 0; c < maxCols; c++) {
      const v = cellVal(ws, r, c);

      row.push(v);

      if (v !== "" && v !== null && v !== undefined) hasContent = true;
    }

    matrix.push(row);

    if (hasContent) {
      lastNonEmpty = r;
      emptyRun = 0;
    } else {
      emptyRun++;
      if (emptyRun >= GAP_CUTOFF) break;
    }
  }

  return { matrix, lastRow: lastNonEmpty };
}

const processFile = (f: File) => {
  // 提取文件名中的年份作为强力兜底（例如："2025年账单.xlsx" -> 2025）
  let fileYear: number | null = null;
  const fileYearMatch = f.name.match(/(20\d{2})/);
  if (fileYearMatch) {
    fileYear = parseInt(fileYearMatch[1]);
  }

  const reader = new FileReader();
  reader.onload = async (e) => {
    parsing.value = true;
    // 让浏览器先渲染"正在解析"提示，再执行同步解析（大文件解析会占用主线程）
    await new Promise((resolve) => setTimeout(resolve, 30));
    try {
      const wb = XLSX.read(new Uint8Array(e.target?.result as ArrayBuffer), {
        type: "array",
      });
      const allValid = [];
      const allSkipped = [];
      let firstCols = null;

      for (const sn of wb.SheetNames) {
        const ws = wb.Sheets[sn];
        if (!ws || !ws["!ref"]) continue;

        // 1. 生成原始的二维数组（扩展列数到 50，防止 !ref 漏掉右侧的合并单元格列）
        const range = XLSX.utils.decode_range(ws["!ref"] || "A1");

        const maxCols = Math.max(range.e.c + 1, 50);

        const { matrix, lastRow } = buildMatrix(ws, range, maxCols);

        // 2. 将所有合并单元格的值向下、向右广播——但**只填充空白格**，绝不覆盖已有值
        if (ws["!merges"]) {
          ws["!merges"].forEach((merge) => {
            const startRow = merge.s.r;
            const startCol = merge.s.c;
            const endRow = merge.e.r;
            const endCol = merge.e.c;
            if (startRow < matrix.length && matrix[startRow]) {
              const val = matrix[startRow][startCol];
              for (let r = startRow; r <= endRow; r++) {
                if (!matrix[r]) matrix[r] = [];
                for (let c = startCol; c <= endCol; c++) {
                  // 只填充真正的空值，保留已有数据
                  if (
                    matrix[r][c] === undefined ||
                    matrix[r][c] === null ||
                    matrix[r][c] === ""
                  ) {
                    matrix[r][c] = val;
                  }
                }
              }
            }
          });
        }

        // 3. 从完美填满的 matrix 中提取表头，绝对不会因为合并单元格漏掉关键字
        const { headers, headerRow } = getMatrixHeaders(matrix);

        // 4. 从 matrix 的前 10 行扫描大标题日期
        let sheetFullDate: string | null = null;
        let sheetYear: number | null = null;
        let sheetShortDate: { m: number; d: number } | null = null;

        for (let r = 0; r < Math.min(15, matrix.length); r++) {
          const row = matrix[r];
          if (!row) continue;
          for (let c = 0; c < row.length; c++) {
            const text = String(row[c] || "").trim();
            if (text) {
              // 优先匹配完整年月日: "2025年1月25日"
              const matchFull = text.match(
                /(\d{4})\s*[\u5e74\/\.\-]\s*(\d{1,2})\s*[\u6708\/\.\-]\s*(\d{1,2})/,
              );
              if (matchFull && !sheetFullDate) {
                sheetFullDate =
                  matchFull[1] +
                  "-" +
                  String(parseInt(matchFull[2])).padStart(2, "0") +
                  "-" +
                  String(parseInt(matchFull[3])).padStart(2, "0");
              }
              // 提取文本中的独立年份: "2025年"
              const matchYear = text.match(
                /(20\d{2})(?:\s*[\u5e74\/\.\-]|\s*[\u4e00-\u9fa5]|$)/,
              );
              if (matchYear && !sheetYear) {
                sheetYear = parseInt(matchYear[1]);
              }
              // 提取文本中的月日: "1月25日"
              const matchShort = text.match(
                /(\d{1,2})\s*[\u6708\/\.\-]\s*(\d{1,2})/,
              );
              if (matchShort && !sheetShortDate) {
                sheetShortDate = {
                  m: parseInt(matchShort[1]),
                  d: parseInt(matchShort[2]),
                };
              }
            }
          }
        }

        let sd = sheetFullDate;
        // 如果没有找到完整日期，但找到了月日，则拼接年份
        // 年份优先级：文件名年份 > Sheet大标题年份 > 系统当前年份
        if (!sd && sheetShortDate) {
          const y = fileYear || sheetYear || new Date().getFullYear();
          sd =
            y +
            "-" +
            String(sheetShortDate.m).padStart(2, "0") +
            "-" +
            String(sheetShortDate.d).padStart(2, "0");
        }

        const cols = detectColumns(headers);
        const hasValidCols = Object.values(cols).some((v) => v !== null);

        // ====== 诊断日志 ======
        console.log(`\n=== Sheet: "${sn}" ===`);
        console.log("headers:", headers);
        console.log("headerRow:", headerRow);
        console.log("cols:", cols);
        console.log("sd:", sd);
        console.log("matrix rows:", matrix.length, "cols:", matrix[0]?.length);

        // 累积列映射：跨 Sheet 合并列信息，不会因为第一个 Sheet 缺少某列就永远"未识别"
        if (!firstCols) {
          firstCols = { ...cols };
        } else {
          for (const k of Object.keys(cols) as (keyof typeof cols)[]) {
            if (!firstCols[k] && cols[k]) firstCols[k] = cols[k];
          }
        }
        if (hasValidCols) {
          detectedColumns.value = firstCols;
          if (sd && !sheetDateLabel.value) sheetDateLabel.value = sd;
        }

        // 5. 提取数据行，映射成 JSON
        const jsonData = matrix.slice(headerRow + 1).map((row) => {
          const obj: Record<string, any> = {};
          headers.forEach((h, i) => {
            if (h) obj[h] = row[i];
          });
          if (sd && !obj[cols.release_date || ""])
            obj[cols.release_date || "放生日期"] = sd;
          return obj;
        });
        const result = parseImportRows(jsonData, cols, sd);

        // 收款区逐笔行按出现顺序对应到当天单据（第 1 笔→第 1 张、第 2 笔→第 2 张……），
        // 不依赖行号对齐（有些模板收款区从表头行开始，与数据行错开一行）
        // 同时把收款类型写到单据的"随喜类型"上，列表里类型和金额才能对得上
        const receipts = extractRowPayments(matrix);
        receipts.forEach((pay, i) => {
          const target = result.validRows[i];
          if (!target) return;
          if (pay.kind === "alipay") {
            target.alipay_amount = pay.amount;
            target.payment_method = "支付宝";
          } else if (pay.kind === "wechat") {
            target.wechat_amount = pay.amount;
            target.payment_method = "微信";
          } else {
            target.suixi_amount = pay.amount;
            target.payment_method = "随喜放生";
          }
        });

        console.log(
          `validRows: ${result.validRows.length}, skippedRows: ${result.skippedRows.length}`,
        );
        if (result.validRows.length > 0) {
          console.log("first valid row:", JSON.stringify(result.validRows[0]));
          console.log(
            "last valid row:",
            JSON.stringify(result.validRows[result.validRows.length - 1]),
          );
        }
        if (result.skippedRows.length > 0) {
          console.log(
            "first 5 skipped reasons:",
            result.skippedRows
              .slice(0, 5)
              .map((s) => `[${s.rowIndex}] ${s.reason}`),
          );
        }
        console.log("first jsonData row keys:", Object.keys(jsonData[0] || {}));
        console.log("first jsonData row:", JSON.stringify(jsonData[0] || {}));
        allValid.push(...result.validRows);
        allSkipped.push(...result.skippedRows);
      }
      importRows.value = allValid;
      skippedRows.value = allSkipped;
      // 服务费合并单元格：连续相同的 fee_value > 0 归为一组，首行保留原值，其余行清零
      {
        const m = new Map<number, number>();
        let i = 0;
        while (i < allValid.length) {
          const fee = (allValid[i] as any).fee_value;
          if (fee > 0) {
            let span = 1;
            while (
              i + span < allValid.length &&
              (allValid[i + span] as any).fee_value === fee
            ) {
              span++;
            }
            if (span >= 2) {
              m.set(i, span);
              for (let j = 1; j < span; j++) {
                m.set(i + j, 0);
                (allValid[i + j] as any).fee_value = 0;
              }
            }
            i += span;
          } else {
            i++;
          }
        }
        feeMergeMap.value = m;
      }
      showPreview.value = true;
      currentStep.value = 2;
    } catch (err) {
      console.error(err);
      toast.error("解析 Excel 失败，请检查文件格式");
    } finally {
      parsing.value = false;
    }
  };
  reader.readAsArrayBuffer(f);
};

const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const f = target.files?.[0];
  if (!f) return;
  processFile(f);
};

const onDrop = (event: DragEvent) => {
  isDragging.value = false;
  const f = event.dataTransfer?.files?.[0];
  if (!f) return;
  processFile(f);
};

const onDragLeave = (event: DragEvent) => {
  const target = event.currentTarget as HTMLElement | null;
  const related = event.relatedTarget as Node | null;
  if (!target || !related || !target.contains(related)) {
    isDragging.value = false;
  }
};

const confirmImport = async () => {
  if (importRows.value.length === 0) return;
  importing.value = true;
  importResult.value = null;
  currentStep.value = 3;
  importDone.value = 0;
  importTotal.value = 0;
  importProgress.value = "正在连接服务器...";
  window.scrollTo({ top: 0 });
  try {
    const result = await saveImportedRowsChunked(
      importRows.value,
      (done, total) => {
        importDone.value = done;
        importTotal.value = total;
        importProgress.value = `正在导入 ${done}/${total} 批...`;
      },
      { replace: overwriteSameDate.value },
    );
    importResult.value = {
      success_count: result.success_count,
      skip_count: result.skip_count,
      errors: result.errors || [],
    };
    importProgress.value = "";
    toast.success(
      "成功导入 " +
        result.success_count +
        " 条" +
        (result.skip_count > 0 ? "，" + result.skip_count + " 条被跳过" : ""),
    );
  } catch (err) {
    if (isAuthError(err)) return;
    console.error(err);
    importProgress.value = "";
    importResult.value = {
      success_count: 0,
      skip_count: 0,
      errors: [apiErrorMessage(err, "导入单据")],
    };
    toast.error(apiErrorMessage(err, "导入单据"));
  } finally {
    importing.value = false;
  }
};
</script>
