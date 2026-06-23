<template>
  <div class="h-full flex flex-col">
    <div class="bg-white rounded-2xl shadow-md border border-dunhuang-yellow/30 p-8 flex-1 flex flex-col">
      <div class="flex items-center justify-between mb-8 border-b-2 border-dunhuang-yellow/30 pb-4 shrink-0">
        <div class="flex items-center gap-4">
          <button @click="goBack" class="text-dunhuang-text/60 hover:text-dunhuang-blue transition-colors flex items-center justify-center w-8 h-8 rounded-full hover:bg-dunhuang-yellow/20" title="返回">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/></svg>
          </button>
          <h2 class="text-2xl font-serif text-dunhuang-blue m-0 font-bold">批量导入单据</h2>
        </div>
        <button @click="downloadTemplate" class="bg-dunhuang-blue hover:bg-dunhuang-green text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
          下载模板
        </button>
      </div>

      <div class="flex-1 flex flex-col min-h-0">
        <!-- Step 1: Upload -->
        <div v-if="currentStep === 1" class="flex-1 flex flex-col items-center justify-center">
          <div class="text-center">
            <div class="border-2 border-dashed border-dunhuang-yellow/40 rounded-2xl p-14 text-center hover:border-dunhuang-blue hover:bg-dunhuang-yellow/5 transition-all duration-200 cursor-pointer" @click="triggerFileInput">
              <input type="file" ref="fileInput" accept=".xlsx, .xls" class="hidden" @change="handleFileUpload" />
              <div class="bg-dunhuang-yellow/10 rounded-full w-16 h-16 mx-auto mb-5 flex items-center justify-center">
                <svg class="w-8 h-8 text-dunhuang-yellow/70" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
              </div>
              <p class="text-base font-serif text-dunhuang-text/70 mb-1">点击或拖拽文件到此处上传</p>
              <p class="text-sm text-dunhuang-text/40">支持 .xlsx、.xls 格式</p>
            </div>
          </div>
        </div>

        <!-- Step 2: Column Mapping + Preview -->
        <div v-else-if="currentStep === 2" class="flex-1 flex flex-col min-h-0 space-y-5">
          <!-- Column Mapping Card -->
          <div class="bg-white rounded-xl border border-dunhuang-yellow/20 p-5 shrink-0">
            <h3 class="text-sm font-semibold text-dunhuang-blue mb-3 font-serif">列映射</h3>
            <div class="grid grid-cols-5 gap-3">
              <div v-for="(label, key) in keyLabels" :key="key" class="flex flex-col gap-1 p-3 rounded-lg border border-dunhuang-yellow/15 bg-dunhuang-yellow/5">
                <span class="text-xs text-dunhuang-text/50 font-medium">{{ label }}</span>
                <span v-if="detectedColumns[key]" class="text-sm text-dunhuang-green font-semibold truncate">{{ detectedColumns[key] }}</span>
                <span v-else-if="key === 'release_date' && sheetDateLabel" class="text-sm text-dunhuang-yellow font-semibold truncate">{{ sheetDateLabel }} (Sheet)</span>
                <span v-else class="text-sm text-dunhuang-red/70">未识别</span>
              </div>
            </div>
          </div>

          <!-- Preview Table -->
          <div class="flex-1 min-h-0 border border-dunhuang-yellow/30 rounded-xl overflow-hidden flex flex-col">
            <div class="flex items-center justify-between px-4 py-3 bg-dunhuang-yellow/10 border-b border-dunhuang-yellow/20 shrink-0">
              <span class="text-sm font-semibold text-dunhuang-blue font-serif">预览数据</span>
              <span class="text-xs text-dunhuang-text/60">共 <b class="text-dunhuang-blue">{{ importRows.length }}</b> 条</span>
            </div>
            <div class="flex-1 overflow-y-auto thin-scrollbar">
              <table class="w-full text-left border-collapse text-sm">
                <thead class="sticky top-0 z-10">
                  <tr>
                    <th class="px-3 py-2.5 border-b border-dunhuang-yellow/30 bg-dunhuang-bg/95 w-12 text-center text-xs font-medium text-dunhuang-text/50">#</th>
                    <th class="px-4 py-2.5 border-b border-dunhuang-yellow/30 bg-dunhuang-bg/95 text-xs font-medium text-dunhuang-text/60">品种</th>
                    <th class="px-4 py-2.5 border-b border-dunhuang-yellow/30 bg-dunhuang-bg/95 text-right text-xs font-medium text-dunhuang-text/60">重量(公斤)</th>
                    <th class="px-4 py-2.5 border-b border-dunhuang-yellow/30 bg-dunhuang-bg/95 text-right text-xs font-medium text-dunhuang-text/60">单价(元)</th>
                    <th class="px-4 py-2.5 border-b border-dunhuang-yellow/30 bg-dunhuang-bg/95 text-right text-xs font-medium text-dunhuang-text/60">服务费</th>
                    <th class="px-4 py-2.5 border-b border-dunhuang-yellow/30 bg-dunhuang-bg/95 text-xs font-medium text-dunhuang-text/60">放生日期</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-dunhuang-yellow/10">
                  <tr v-for="(row, index) in importRows" :key="index" class="hover:bg-dunhuang-yellow/5 transition-colors duration-150" :class="index % 2 === 1 ? 'bg-dunhuang-yellow/3' : 'bg-white'">
                    <td class="px-3 py-2.5 text-center text-xs text-dunhuang-text/40 tabular-nums">{{ index + 1 }}</td>
                    <td class="px-4 py-2.5 text-sm text-dunhuang-text font-medium">{{ row.name_zh }}</td>
                    <td class="px-4 py-2.5 text-right text-sm tabular-nums text-dunhuang-text/80">{{ formatMoney(row.weight) }}</td>
                    <td class="px-4 py-2.5 text-right text-sm tabular-nums text-dunhuang-text/80">{{ formatMoney(row.unit_price) }}</td>
                    <td class="px-4 py-2.5 text-right text-sm tabular-nums" :class="row.fee_value > 0 ? 'text-dunhuang-orange' : 'text-dunhuang-text/40'">{{ formatMoney(row.fee_value) }}</td>
                    <td class="px-4 py-2.5 text-xs text-dunhuang-text/60 whitespace-nowrap">{{ dateStr(row.release_date) || '-' }}</td>
                  </tr>
                  <tr v-if="importRows.length === 0">
                    <td colspan="6" class="px-4 py-16 text-center text-sm text-dunhuang-text/40">未解析到有效数据</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Step 2 Actions -->
          <div class="flex justify-between items-center shrink-0 pt-1">
            <button @click="cancelImport" class="px-6 py-2 border border-dunhuang-yellow text-dunhuang-text rounded-lg hover:bg-dunhuang-yellow/20 transition-colors text-sm">取消</button>
            <button @click="currentStep = 3" class="px-6 py-2 bg-dunhuang-red text-white rounded-lg hover:bg-dunhuang-red/90 transition-colors text-sm disabled:opacity-70" :disabled="importRows.length === 0">确认导入</button>
          </div>
        </div>

        <!-- Step 3: Result -->
        <div v-else-if="currentStep === 3" class="flex-1 flex flex-col items-center justify-center text-center">
          <div v-if="importing" class="space-y-5">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-dunhuang-blue mx-auto"></div>
            <p class="text-base font-serif text-dunhuang-text/70">正在导入数据...</p>
          </div>
          <div v-else class="space-y-5">
            <div v-if="importResult" class="space-y-3">
              <div class="w-16 h-16 mx-auto rounded-full flex items-center justify-center" :class="importResult.errors.length > 0 ? 'bg-dunhuang-yellow/20' : 'bg-dunhuang-green/20'">
                <svg v-if="importResult.errors.length === 0" class="w-8 h-8 text-dunhuang-green" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
                <svg v-else class="w-8 h-8 text-dunhuang-yellow" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>
              </div>
              <p class="text-xl font-serif text-dunhuang-blue font-bold">导入完成</p>
              <div class="text-sm text-dunhuang-text/70 space-y-1">
                <p>成功导入 <b class="text-dunhuang-green">{{ importResult.success_count }}</b> 条</p>
                <p v-if="importResult.skip_count > 0">跳过 <b class="text-dunhuang-yellow">{{ importResult.skip_count }}</b> 条</p>
              </div>
              <div v-if="importResult.errors.length > 0" class="max-h-32 overflow-y-auto mt-3 text-left text-xs bg-dunhuang-yellow/5 rounded-lg p-3">
                <div v-for="(err, i) in importResult.errors" :key="i" class="text-dunhuang-text/60 py-0.5 border-b border-dunhuang-yellow/10 last:border-0">{{ err }}</div>
              </div>
            </div>
            <div class="flex gap-3 mt-6">
              <button @click="currentStep = 1; cancelImport()" class="px-6 py-2 border border-dunhuang-yellow text-dunhuang-text rounded-lg hover:bg-dunhuang-yellow/20 transition-colors text-sm">继续导入</button>
              <button @click="goBack" class="px-6 py-2 bg-dunhuang-blue text-white rounded-lg hover:bg-dunhuang-green transition-colors text-sm">返回列表</button>
            </div>
          </div>
        </div>
      </div>
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
import { detectColumns, parseImportRows, parseSheetDate, type ParsedRow, type SkippedRow } from "../lib/importUtils";

const router = useRouter();
const toast = useToast();
const currentStep = ref(1);
const fileInput = ref<HTMLInputElement | null>(null);
const showPreview = ref(false);
const importing = ref(false);
const importResult = ref<{ success_count: number; skip_count: number; errors: string[] } | null>(null);
const importRows = shallowRef<any[]>([]);
const detectedColumns = shallowRef<Record<string, string | null>>({});
const sheetDateLabel = ref<string | null>(null);

const keyLabels: Record<string, string> = { species: "品种", weight: "重量", unit_price: "单价", fee_value: "服务费", release_date: "日期" };

const goBack = () => { router.push("/billing"); };

const triggerFileInput = () => { if (fileInput.value) { fileInput.value.value = ""; fileInput.value.click(); } };

const downloadTemplate = () => { const a = document.createElement("a"); a.href = "/单据导入模板.xlsx"; a.download = "单据导入模板.xlsx"; a.click(); };

const cancelImport = () => { showPreview.value = false; importRows.value = []; detectedColumns.value = {}; sheetDateLabel.value = null; importResult.value = null; };

function getSheetHeaders(worksheet) {
  const range = XLSX.utils.decode_range(worksheet["!ref"] || "A1");
  const kw = ["品种","品名","名称","物种","重量","公斤","斤","单价","价格","总计","实付","服务费","日期","鱼"];
  for (let r = range.s.r; r <= Math.min(range.s.r + 10, range.e.r); r++) {
    const vals = []; let m = 0;
    for (let c = range.s.c; c <= range.e.c; c++) { const cell = worksheet[XLSX.utils.encode_cell({ r, c })]; const v = cell ? String(cell.v ?? "").trim() : ""; vals.push(v); if (kw.some(k => v.includes(k))) m++; }
    if (m >= 2) return { headers: vals, headerRow: r };
  }
  const fb = [];
  for (let c = range.s.c; c <= range.e.c; c++) { const cell = worksheet[XLSX.utils.encode_cell({ r: range.s.r, c })]; fb.push(cell ? String(cell.v ?? "").trim() : ""); }
  return { headers: fb, headerRow: range.s.r };
}

const handleFileUpload = (event) => {
  const f = event.target.files?.[0]; if (!f) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const wb = XLSX.read(new Uint8Array(e.target?.result as ArrayBuffer), { type: "array" });
      const allValid = []; let firstCols = null;
      for (const sn of wb.SheetNames) {
        const ws = wb.Sheets[sn]; if (!ws || !ws["!ref"]) continue;
        const sd = parseSheetDate(sn, 2026);
        const { headers, headerRow } = getSheetHeaders(ws);
        const cols = detectColumns(headers);
        if (!firstCols) { firstCols = cols; detectedColumns.value = cols; if (sd) sheetDateLabel.value = sd; }
        const rawRows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: "" });
        const jsonData = rawRows.slice(headerRow + 1).map(row => { const obj = {}; headers.forEach((h,i) => { if (h) obj[h] = row[i]; }); if (sd && !obj[cols.release_date || ""]) obj[cols.release_date || "放生日期"] = sd; return obj; });
        const result = parseImportRows(jsonData, cols, sd);
        allValid.push(...result.validRows);
      }
      importRows.value = allValid; showPreview.value = true; currentStep.value = 2;
    } catch (err) { console.error(err); toast.error("解析 Excel 失败，请检查文件格式"); }
  };
  reader.readAsArrayBuffer(f);
};

const confirmImport = async () => {
  if (importRows.value.length === 0) return;
  importing.value = true; importResult.value = null; currentStep.value = 3;
  try {
    const result = await saveImportedRowsBatch(importRows.value, true);
    importResult.value = { success_count: result.success_count, skip_count: result.skip_count, errors: result.errors || [] };
    toast.success("成功导入 " + result.success_count + " 条" + (result.skip_count > 0 ? "，" + result.skip_count + " 条被跳过" : ""));
  } catch (err) {
    if (isAuthError(err)) return; console.error(err);
    importResult.value = { success_count: 0, skip_count: 0, errors: [apiErrorMessage(err, "导入单据")] };
    toast.error(apiErrorMessage(err, "导入单据"));
  } finally { importing.value = false; }
};
</script>