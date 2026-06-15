<template>
  <div class="h-full flex flex-col space-y-6">
    <div
      class="bg-white rounded-2xl shadow-md border border-dunhuang-yellow/30 p-8 flex-1 flex flex-col"
    >
      <div
        class="flex items-center justify-between mb-8 border-b-2 border-dunhuang-yellow/30 pb-4 shrink-0"
      >
        <div class="flex items-center gap-4">
          <button
            @click="goBack"
            class="text-dunhuang-text/60 hover:text-dunhuang-blue transition-colors flex items-center justify-center w-8 h-8 rounded-full hover:bg-dunhuang-yellow/20"
            title="返回物命"
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
              ></path>
            </svg>
          </button>
          <h2
            class="text-2xl font-serif text-dunhuang-blue m-0 flex items-center gap-3 font-bold"
          >
            批量导入单据
          </h2>
        </div>
        <div class="flex gap-3">
          <button
            @click="downloadTemplate"
            class="bg-dunhuang-blue hover:bg-dunhuang-green text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            下载模板
          </button>
          <div>
            <input
              type="file"
              ref="fileInput"
              accept=".xlsx, .xls"
              class="hidden"
              @change="handleFileUpload"
            />
            <button
              @click="triggerFileInput"
              type="button"
              class="bg-dunhuang-blue hover:bg-dunhuang-green text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
            >
              选择 Excel 文件
            </button>
          </div>
        </div>
      </div>

      <Transition name="switch-fade" mode="out-in">
        <div
          v-if="!showPreview"
          class="flex-1 flex flex-col items-center justify-center relative z-10"
        >
          <div class="text-dunhuang-text/60 text-center space-y-4">
            <svg
              class="w-16 h-16 mx-auto text-dunhuang-yellow/50"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.5"
                d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <p class="text-lg font-serif">请选择要导入的 Excel 文件</p>
            <p class="text-sm">支持 .xlsx 或 .xls 格式</p>
          </div>
        </div>

        <div v-else class="flex-1 flex flex-col min-h-0 relative z-10">
          <div class="mb-3 shrink-0 flex items-center gap-3 text-xs text-dunhuang-text/50 bg-dunhuang-bg/50 rounded-lg px-4 py-2">
            <span>识别列：</span>
            <template v-for="(col, key) in detectedColumns" :key="key">
              <span v-if="col" class="text-dunhuang-green font-medium">{{ keyLabels[key] + " → " + col }}</span>
              <span v-else class="text-dunhuang-red/60">{{ keyLabels[key] + "=未识别" }}</span>
            </template>
          </div>
          <div class="mb-4 flex justify-between items-center shrink-0">
            <h4 class="text-lg font-serif text-dunhuang-blue">预览导入数据</h4>
            <div class="text-sm text-dunhuang-text/70">
              共
              <span class="font-bold text-dunhuang-blue">{{
                importRows.length
              }}</span>
              条
            </div>
          </div>

          <div
            class="flex-1 border border-dunhuang-yellow/30 rounded-lg mb-6 min-h-0 overflow-hidden" :class="{ 'max-h-[55vh]': importRows.length > 10 }"
          >
            <div class="h-full overflow-y-auto thin-scrollbar">
            <table class="w-full text-left border-collapse whitespace-nowrap">
              <thead class="sticky top-0 bg-dunhuang-bg">
                <tr class="bg-dunhuang-yellow/20 text-dunhuang-blue font-serif">
                  <th class="p-3 border-b border-dunhuang-yellow/40 w-16">
                    序号
                  </th>
                  <th class="p-3 border-b border-dunhuang-yellow/40">品种</th>
                  <th class="p-3 border-b border-dunhuang-yellow/40">
                    重量（公斤）
                  </th>
                  <th class="p-3 border-b border-dunhuang-yellow/40">
                    单价（元）
                  </th>
                  <th class="p-3 border-b border-dunhuang-yellow/40">
                    服务费（元）
                  </th>
                  <th class="p-3 border-b border-dunhuang-yellow/40">
                    放生日期
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(row, index) in importRows"
                  :key="index"
                  class="border-b border-dunhuang-yellow/20 hover:bg-dunhuang-yellow/5 transition-colors"
                >
                  <td class="p-3 text-dunhuang-text/50">{{ index + 1 }}</td>
                  <td class="p-3">{{ row.name_zh }}</td>
                  <td class="p-3 tabular-nums">
                    {{ formatMoney(row.weight) }}
                  </td>
                  <td class="p-3 tabular-nums">
                    {{ formatMoney(row.unit_price) }}
                  </td>
                  <td class="p-3 tabular-nums">
                    {{ formatMoney(row.fee_value) }}
                  </td>
                  <td class="p-3 text-sm">
                    {{ dateStr(row.release_date) || "-" }}
                  </td>
                </tr>
                <tr v-if="importRows.length === 0">
                  <td colspan="6" class="p-8 text-center text-dunhuang-text/50">
                    未解析到有效数据
                  </td>
                </tr>
              </tbody>
            </table>
            </div>
          </div>

          <div class="flex justify-end gap-3 shrink-0">
            <button
              type="button"
              @click="cancelImport"
              class="px-6 py-2 border border-dunhuang-yellow text-dunhuang-text rounded-lg hover:bg-dunhuang-yellow/20 transition-colors"
              :disabled="importing"
            >
              取消
            </button>
            <button
              type="button"
              @click="confirmImport"
              class="px-6 py-2 bg-dunhuang-red text-white rounded-lg hover:bg-dunhuang-red/90 transition-colors disabled:opacity-70"
              :disabled="importRows.length === 0 || importing"
            >
              {{ importing ? "导入中..." : "确认导入" }}
            </button>
          </div>
    </div>
      </Transition>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, shallowRef } from "vue";
import { useRouter } from "vue-router";
import * as XLSX from "xlsx";
import { apiErrorMessage, isAuthError } from "../lib/error";
import { dateStr, formatMoney } from "../lib/utils";
import { useToast } from "../composables/useToast";
import { saveImportedRowsBatch } from "../services/billingEntryService";
import {
  detectColumns,
  parseImportRows,
  parseSheetDate,
  type ParsedRow,
  type SkippedRow,
} from "../lib/importUtils";

const router = useRouter();
const toast = useToast();

const fileInput = ref<HTMLInputElement | null>(null);
const showPreview = ref(false);
const importing = ref(false);
const importRows = shallowRef<any[]>([]);
const detectedColumns = shallowRef<Record<string, string | null>>({});

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
  const templateData = [
    {
      品种: "东星斑",
      "重量（公斤）": "10.00",
      "单价（元）": "120.00",
      "服务费（元）": "20.00",
      "放生日期": "2025-01-15",
    },
    {
      品种: "老虎斑",
      "重量（公斤）": "15.00",
      "单价（元）": "85.00",
      "服务费（元）": "15.00",
      "放生日期": "2025-01-15",
    },
  ];

  const worksheet = XLSX.utils.json_to_sheet(templateData);

  worksheet["!cols"] = [
    { wch: 15 },
    { wch: 12 },
    { wch: 12 },
    { wch: 12 },
    { wch: 14 },
  ];

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "导入模板");
  XLSX.writeFile(workbook, "单据导入模板.xlsx");
};

const cancelImport = () => {
  showPreview.value = false;
  importRows.value = [];
};

/** Auto-detect the header row by scanning for known column keywords. */
function getSheetHeaders(worksheet: XLSX.WorkSheet): { headers: string[]; headerRow: number } {
  const range = XLSX.utils.decode_range(worksheet["!ref"] || "A1");
  const headerKeywords = ['品种', '品名', '名称', '物种', '重量', '公斤', '斤', '单价', '价格', '总计', '实付', '服务费', '日期'];

  // Scan first 10 rows for header-like content
  for (let r = range.s.r; r <= Math.min(range.s.r + 10, range.e.r); r++) {
    const rowValues: string[] = [];
    let keywordMatches = 0;
    for (let c = range.s.c; c <= range.e.c; c++) {
      const addr = XLSX.utils.encode_cell({ r, c });
      const cell = worksheet[addr];
      const val = cell ? String(cell.v ?? "").trim() : "";
      rowValues.push(val);
      if (headerKeywords.some(k => val.includes(k))) {
        keywordMatches++;
      }
    }
    if (keywordMatches >= 2) {
      return { headers: rowValues, headerRow: r };
    }
  }

  // Fallback: use row 1
  const fallback: string[] = [];
  for (let c = range.s.c; c <= range.e.c; c++) {
    const addr = XLSX.utils.encode_cell({ r: range.s.r, c });
    const cell = worksheet[addr];
    fallback.push(cell ? String(cell.v ?? "").trim() : "");
  }
  return { headers: fallback, headerRow: range.s.r };
}

const handleFileUpload = (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target?.result as ArrayBuffer);
      const workbook = XLSX.read(data, { type: "array" });

      const allValid: any[] = [];
      const allSkipped: any[] = [];
      let firstColumns: Record<string, string | null> | null = null;

      // Process ALL sheets
      for (const sheetName of workbook.SheetNames) {
        const worksheet = workbook.Sheets[sheetName];
        if (!worksheet || !worksheet["!ref"]) continue;

        // Parse release date from sheet tab name (e.g., "1月3日" → "2026-01-03")
        const sheetDate = parseSheetDate(sheetName, 2026);

        // Detect header row automatically
        const { headers, headerRow } = getSheetHeaders(worksheet);
        const columns = detectColumns(headers);
        if (!firstColumns) {
          firstColumns = columns;
          detectedColumns.value = columns;
        }

        // Read raw rows and build properly-keyed objects
        const rawRows = XLSX.utils.sheet_to_json(worksheet, { header: 1, defval: "" }) as unknown[][];
        const dataStartRow = headerRow + 1;
        const jsonData = rawRows.slice(dataStartRow).map(row => {
          const obj: Record<string, unknown> = {};
          headers.forEach((h, i) => {
            if (h) obj[h] = (row as unknown[])[i];
          });
          // Force release_date from sheet tab if not already present
          if (sheetDate && !obj[columns.release_date || '']) {
            obj[columns.release_date || '放生日期'] = sheetDate;
          }
          return obj;
        });

        const result = parseImportRows(
          jsonData as Record<string, unknown>[],
          columns,
          sheetDate, // fallback: date from sheet tab if no date column in headers
        );
        allValid.push(...result.validRows);
        allSkipped.push(...result.skippedRows);
      }

      importRows.value = allValid;

      showPreview.value = true;
    } catch (error) {
      console.error("Failed to parse Excel", error);
      toast.error("解析 Excel 失败，请检查文件格式是否正确。");
    }
  };
  reader.readAsArrayBuffer(file);
};

const confirmImport = async () => {
  importing.value = true;
  try {
    const result = await saveImportedRowsBatch(importRows.value, true);
    if (result.skip_count > 0) {
      toast.success(`成功导入 ${result.success_count} 条，${result.skip_count} 条被跳过`);
    } else {
      toast.success(`成功导入 ${result.success_count} 条`);
    }
    router.push("/billing");
  } catch (error: any) {
    if (isAuthError(error)) return;
    console.error("Import failed", error);
    toast.error(apiErrorMessage(error, "导入单据"));
  } finally {
    importing.value = false;
  }
};

</script>
