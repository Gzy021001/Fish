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
            class="flex-1 overflow-auto custom-scrollbar border border-dunhuang-yellow/30 rounded-lg mb-6 min-h-0"
          >
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
                    {{ row.release_date || "-" }}
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
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import * as XLSX from "xlsx";
import { apiErrorMessage, isAuthError } from "../lib/error";
import { formatMoney } from "../lib/utils";
import { useSpecies } from "../composables/useSpecies";
import { useToast } from "../composables/useToast";
import { saveImportedRows } from "../services/billingEntryService";

const router = useRouter();
const toast = useToast();
const { speciesList, fetchSpecies } = useSpecies();

const fileInput = ref<HTMLInputElement | null>(null);
const showPreview = ref(false);
const importing = ref(false);
const importRows = ref<any[]>([]);

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

const handleFileUpload = (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const data = new Uint8Array(e.target?.result as ArrayBuffer);
      const workbook = XLSX.read(data, { type: "array" });
      const firstSheetName = workbook.SheetNames[0];
      const worksheet = workbook.Sheets[firstSheetName];

      const jsonData = XLSX.utils.sheet_to_json(worksheet);

      importRows.value = jsonData
        .map((row: any) => {
          const name_zh = row["品种"] || row["名称"] || "";
          const weight = parseFloat(row["重量（公斤）"] || row["重量"] || 0);
          const unit_price = parseFloat(row["单价（元）"] || row["单价"] || 0);
          const fee_value = parseFloat(row["服务费（元）"] || row["服务费"] || 0);
          const release_date = row["放生日期"] || row["日期"] || "";

          return {
            name_zh,
            weight,
            unit_price,
            fee_value,
            release_date: release_date ? String(release_date).trim() : undefined,
          };
        })
        .filter((r) => r.name_zh && r.unit_price > 0);

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
    const saved = await saveImportedRows(importRows.value, speciesList.value);
    toast.success(`成功导入 ${saved} 条`);
    router.push("/billing");
  } catch (error: any) {
    if (isAuthError(error)) return;
    console.error("Import failed", error);
    toast.error(apiErrorMessage(error, "导入单据"));
  } finally {
    importing.value = false;
  }
};

onMounted(() => {
  fetchSpecies();
});
</script>
