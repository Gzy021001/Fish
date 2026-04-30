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
            条数据，包含
            <span class="font-bold text-dunhuang-red">{{
              importRows.filter((r) => r.isNewSpecies).length
            }}</span>
            个新品种。
          </div>
        </div>

        <div
          class="flex-1 overflow-auto border border-dunhuang-yellow/30 rounded-lg mb-6 min-h-0"
        >
          <table class="w-full text-left border-collapse whitespace-nowrap">
            <thead class="sticky top-0 bg-dunhuang-bg">
              <tr class="bg-dunhuang-yellow/20 text-dunhuang-blue font-serif">
                <th class="p-3 border-b border-dunhuang-yellow/40">状态</th>
                <th class="p-3 border-b border-dunhuang-yellow/40">品种名称</th>
                <th class="p-3 border-b border-dunhuang-yellow/40">重量</th>
                <th class="p-3 border-b border-dunhuang-yellow/40">单价</th>
                <th class="p-3 border-b border-dunhuang-yellow/40">服务费</th>
                <th class="p-3 border-b border-dunhuang-yellow/40">总计</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(row, index) in importRows"
                :key="index"
                class="border-b border-dunhuang-yellow/20 hover:bg-dunhuang-yellow/5 transition-colors"
              >
                <td class="p-3">
                  <span
                    v-if="row.isNewSpecies"
                    class="text-xs bg-dunhuang-red/10 text-dunhuang-red px-2 py-1 rounded"
                    >新建品种</span
                  >
                  <span
                    v-else
                    class="text-xs bg-dunhuang-green/10 text-dunhuang-green px-2 py-1 rounded"
                    >已有品种</span
                  >
                </td>
                <td class="p-3">{{ row.name_zh }}</td>
                <td class="p-3">{{ row.weight.toFixed(2) }}</td>
                <td class="p-3 font-mono">¥ {{ row.unit_price.toFixed(2) }}</td>
                <td class="p-3">
                  {{
                    row.fee_type === "PERCENTAGE"
                      ? row.fee_value + "%"
                      : "+ ¥ " + row.fee_value.toFixed(2)
                  }}
                </td>
                <td class="p-3 font-bold text-dunhuang-red">
                  ¥ {{ calculateRowTotal(row).toFixed(2) }}
                </td>
              </tr>
              <tr v-if="importRows.length === 0">
                <td colspan="7" class="p-8 text-center text-dunhuang-text/50">
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import * as XLSX from "xlsx";
import api from "../api";
import { apiErrorMessage, isAuthError } from "../lib/error";

// ============================================================
//  批量导入：Excel 解析 → 品种自动创建 → 单据批量创建
// ============================================================

const router = useRouter();
const speciesList = ref<any[]>([]);

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
      品种名称: "东星斑",
      重量: "1.5",
      单价: "120.00",
      服务费类型: "按比例",
      服务费: "5",
    },
    {
      品种名称: "老虎斑",
      重量: "2.0",
      单价: "85.00",
      服务费类型: "固定金额",
      服务费: "10",
    },
  ];

  const worksheet = XLSX.utils.json_to_sheet(templateData);

  // Set column widths for better readability
  worksheet["!cols"] = [
    { wch: 15 }, // 品种名称
    { wch: 10 }, // 重量
    { wch: 10 }, // 单价
    { wch: 12 }, // 服务费类型
    { wch: 10 }, // 服务费
  ];

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "导入模板");
  XLSX.writeFile(workbook, "单据导入模板.xlsx");
};

const calculateRowTotal = (row: any) => {
  const sub = row.weight * row.unit_price;
  let f = 0;
  if (row.fee_type === "PERCENTAGE") {
    f = sub * (row.fee_value / 100);
  } else {
    f = row.fee_value;
  }
  return Number((sub + f).toFixed(2));
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
          const name_zh =
            row["品种名称"] || row["国语名称"] || row["NameZH"] || "";
          const weight = parseFloat(row["重量"] || row["Weight"] || 0);
          const unit_price = parseFloat(row["单价"] || row["UnitPrice"] || 0);
          const currency = "CNY";
          const fee_type =
            (row["服务费类型"] || row["FeeType"]) === "固定金额"
              ? "FIXED"
              : "PERCENTAGE";
          const fee_value = parseFloat(
            row["服务费"] || row["服务费数值"] || row["FeeValue"] || 0,
          );

          const existingSpecies = speciesList.value.find(
            (s) => s.name_zh === name_zh,
          );

          return {
            name_zh,
            weight,
            unit_price,
            currency,
            fee_type,
            fee_value,
            species_id: existingSpecies ? existingSpecies.id : null,
            isNewSpecies: !existingSpecies,
          };
        })
        .filter((r) => r.name_zh && r.weight > 0 && r.unit_price > 0);

      showPreview.value = true;
    } catch (error) {
      console.error("Failed to parse Excel", error);
      alert("解析 Excel 失败，请检查文件格式是否正确。");
    }
  };
  reader.readAsArrayBuffer(file);
};

const confirmImport = async () => {
  importing.value = true;
  try {
    for (const row of importRows.value) {
      let speciesId = row.species_id;

      // 如果是新品种，先创建
      if (row.isNewSpecies) {
        const spRes = await api.post("/species", {
          name_zh: row.name_zh,
          default_price: row.unit_price,
          default_unit: "kg",
        });
        speciesId = spRes.data.id;

        // 动态同步到当前列表，避免后续遇到同名重复创建
        speciesList.value.push(spRes.data);
        importRows.value.forEach((r) => {
          if (r.name_zh === row.name_zh) {
            r.species_id = speciesId;
            r.isNewSpecies = false;
          }
        });
      }

      // 创建单据
      await api.post("/bills", {
        species_id: speciesId,
        weight: row.weight,
        unit_price: row.unit_price,
        currency: row.currency,
        fee_type: row.fee_type,
        fee_value: row.fee_value,
      });
    }

    alert(`成功导入 ${importRows.value.length} 条单据！`);
    router.push("/billing");
  } catch (error: any) {
    if (isAuthError(error)) return;
    console.error("Import failed", error);
    alert(apiErrorMessage(error, "导入单据"));
  } finally {
    importing.value = false;
  }
};

const fetchSpecies = async () => {
  try {
    const res = await api.get("/species");
    speciesList.value = res.data || [];
  } catch (error: any) {
    if (isAuthError(error)) return;
    console.error("Failed to fetch species", error);
  }
};

onMounted(() => {
  fetchSpecies();
});
</script>
