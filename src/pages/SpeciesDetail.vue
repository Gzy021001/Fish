<template>
  <div class="h-full flex flex-col space-y-6">
    <div
      v-if="errorMsg"
      class="mb-4 p-3 bg-dunhuang-red/10 text-dunhuang-red rounded border border-dunhuang-red/20 text-sm shrink-0"
    >
      {{ errorMsg }}
    </div>

    <div
      v-if="loading"
      class="bg-white/80 backdrop-blur rounded-2xl shadow-sm border border-dunhuang-yellow/30 p-10 text-center text-dunhuang-text/60 flex-1"
    >
      正在加载品种详情...
    </div>

    <div
      v-else-if="species"
      class="bg-white rounded-2xl shadow-md border border-dunhuang-yellow/30 p-8 flex-1 flex flex-col"
    >
      <div
        class="flex items-center justify-between mb-8 border-b-2 border-dunhuang-yellow/30 pb-4 shrink-0"
      >
        <div class="flex items-center gap-4">
          <button
            @click="goBack"
            class="text-dunhuang-text/60 hover:text-dunhuang-blue transition-colors flex items-center justify-center w-8 h-8 rounded-full hover:bg-dunhuang-yellow/20"
            title="返回物命品种库"
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
            {{ isEditing ? "编辑品种" : "品种详情" }}
          </h2>
        </div>
        <button
          v-if="isEditing"
          @click="removeSpecies"
          class="px-3 py-1.5 rounded bg-dunhuang-red/10 text-dunhuang-red hover:bg-dunhuang-red hover:text-white transition-colors text-xs border border-dunhuang-red/20 hover:border-transparent"
        >
          删除
        </button>
        <button
          v-if="!isEditing"
          @click="isEditing = true"
          class="px-3 py-1.5 rounded bg-dunhuang-blue text-white hover:bg-dunhuang-green transition-colors text-xs border border-transparent"
        >
          编辑品种
        </button>
      </div>

      <div
        class="relative z-10 flex-1 overflow-y-auto custom-scrollbar pr-2 pb-4"
      >
        <form @submit.prevent="saveSpecies" class="space-y-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- 图片区域 -->
            <div class="md:col-span-2 flex items-center justify-start p-0 mb-4">
              <div
                class="w-96 h-64 rounded-xl overflow-hidden border-2 border-dunhuang-yellow/30 bg-white flex items-center justify-center shadow-inner relative group shrink-0"
                :class="{
                  'cursor-pointer hover:border-dunhuang-blue transition-colors':
                    isEditing,
                }"
                @click="isEditing && fileInputRef?.click()"
              >
                <img
                  v-if="species.image_url"
                  :src="species.image_url"
                  :alt="species.name_zh"
                  class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                />
                <div
                  v-else
                  class="w-full h-full bg-dunhuang-yellow/5 border border-dunhuang-yellow/30 text-dunhuang-blue flex items-center justify-center transition-transform duration-500 group-hover:scale-105"
                >
                  <span class="text-6xl font-bold opacity-30">{{ species.name_zh ? species.name_zh.charAt(0) : '?' }}</span>
                </div>

                <!-- Hover Overlay for Editing -->
                <div
                  v-if="isEditing"
                  class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                >
                  <svg
                    class="w-6 h-6 text-white"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                    ></path>
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
                    ></path>
                  </svg>
                </div>

                <input
                  type="file"
                  accept="image/*"
                  ref="fileInputRef"
                  @change="handleImageUpload"
                  class="hidden"
                />
              </div>
            </div>

            <!-- 表单字段 -->
            <div v-if="isEditing" class="space-y-2">
              <label class="block text-sm font-medium text-dunhuang-text"
                >品种编号</label
              >
              <input
                :value="'#' + species.id"
                disabled
                class="w-full border border-dunhuang-yellow/50 rounded-lg px-4 py-3 bg-dunhuang-bg outline-none disabled:opacity-60 disabled:cursor-not-allowed text-dunhuang-blue font-bold font-mono"
              />
            </div>

            <div class="space-y-2">
              <label class="block text-sm font-medium text-dunhuang-text"
                >品种名称</label
              >
              <input
                v-model="form.name_zh"
                :disabled="!isEditing || saving"
                required
                class="w-full border border-dunhuang-yellow/50 rounded-lg px-4 py-3 bg-dunhuang-bg outline-none focus:ring-2 focus:ring-dunhuang-red disabled:opacity-60 disabled:cursor-not-allowed transition-shadow"
              />
            </div>

            <div class="space-y-2">
              <label class="block text-sm font-medium text-dunhuang-text"
                >单价 (¥)</label
              >
              <input
                type="number"
                step="0.01"
                min="0"
                v-model.number="form.default_price"
                @blur="form.default_price = Number((form.default_price || 0).toFixed(2))"
                :disabled="!isEditing || saving"
                required
                class="w-full border border-dunhuang-yellow/50 rounded-lg px-4 py-3 bg-dunhuang-bg outline-none focus:ring-2 focus:ring-dunhuang-red disabled:opacity-60 disabled:cursor-not-allowed transition-shadow font-mono text-dunhuang-red [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
              />
            </div>

            <div class="space-y-2">
              <label class="block text-sm font-medium text-dunhuang-text"
                >默认单位</label
              >
              <input
                v-model="form.default_unit"
                :disabled="!isEditing || saving"
                required
                class="w-full border border-dunhuang-yellow/50 rounded-lg px-4 py-3 bg-dunhuang-bg outline-none focus:ring-2 focus:ring-dunhuang-red disabled:opacity-60 disabled:cursor-not-allowed transition-shadow"
              />
            </div>
          </div>

          <div
            v-if="isEditing"
            class="mt-8 pt-6 border-t border-dunhuang-yellow/30 flex justify-end"
          >
            <button
              type="submit"
              :disabled="saving"
              class="px-3 py-1.5 bg-dunhuang-blue text-white rounded hover:bg-dunhuang-green transition-colors text-xs disabled:opacity-50"
            >
              {{ saving ? "保存中..." : "保存修改" }}
            </button>
          </div>
        </form>

        <!-- 操作记录 -->
        <div
          v-if="!isEditing && logs.length > 0"
          class="mt-8 pt-8 border-t border-dunhuang-yellow/20"
        >
          <h4
            class="text-lg font-serif text-dunhuang-blue font-bold mb-4 border-b border-dunhuang-yellow/10 pb-2"
          >
            操作记录
          </h4>
          <div class="space-y-4">
            <div
              v-for="log in logs"
              :key="log.id"
              class="bg-transparent border-b border-dunhuang-yellow/20 py-4 text-sm last:border-0"
            >
              <div class="flex justify-between items-center mb-3">
                <span
                  :class="[
                    'px-2 py-1 rounded text-xs font-medium',
                    log.action === 'CREATE'
                      ? 'bg-dunhuang-green/10 text-dunhuang-green'
                      : log.action === 'UPDATE'
                        ? 'bg-dunhuang-blue/10 text-dunhuang-blue'
                        : 'bg-dunhuang-red/10 text-dunhuang-red',
                  ]"
                  >{{ formatAction(log.action) }}</span
                >
                <span class="text-dunhuang-text/50 text-xs">{{
                  dateTimeStr(log.created_at)
                }}</span>
              </div>
              <div
                v-if="log.action === 'UPDATE'"
                class="text-dunhuang-text/80 text-xs space-y-2"
              >
                <div
                  class="text-dunhuang-text/50 mb-1 border-b border-dunhuang-yellow/10 pb-1"
                >
                  数据变更明细：
                </div>
                <div
                  v-for="item in formatUpdateDiff(log.old_data, log.new_data)"
                  :key="item.label"
                  class="flex gap-2"
                >
                  <span class="w-20 shrink-0 text-dunhuang-text/60"
                    >{{ item.label }}:</span
                  >
                  <span class="line-through text-dunhuang-red/60">{{
                    item.old
                  }}</span>
                  <span class="text-dunhuang-blue">→</span>
                  <span class="text-dunhuang-green">{{ item.new }}</span>
                </div>
              </div>
              <div
                v-else-if="log.action === 'CREATE'"
                class="text-dunhuang-text/60 text-xs"
              >
                创建了该品种
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <ConfirmDialog
      :show="showDeleteConfirm"
      @cancel="showDeleteConfirm = false"
      @confirm="executeDeleteSpecies"
    >
      即将删除品种：<span class="font-bold">{{ species?.name_zh }}</span
      ><br />此操作不可撤销，确定要删除吗？
    </ConfirmDialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "../api";
import { apiErrorMessage, isAuthError } from "../lib/error";
import { dateTimeStr, diffFields } from "../lib/utils";
import ConfirmDialog from "../components/ConfirmDialog.vue";

// ============================================================
//  品种详情：查看 / 编辑 / 上传图片 / 操作日志
// ============================================================

interface SpeciesItem {
  id: number;
  name_zh: string;
  default_unit: string;
  default_price: number;
  image_url?: string | null;
}

const route = useRoute();
const router = useRouter();

const loading = ref(true);
const saving = ref(false);
const errorMsg = ref("");
const species = ref<SpeciesItem | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);
const isEditing = ref(route.query.mode === "edit");
const showDeleteConfirm = ref(false);
const logs = ref<any[]>([]);
const form = ref({
  name_zh: "",
  default_price: 0,
  default_unit: "kg",
  image_url: null as string | null,
});

const speciesId = () => Number(route.params.id);



const syncForm = (data: SpeciesItem) => {
  form.value = {
    name_zh: data.name_zh,
    default_price: data.default_price || 0,
    default_unit: data.default_unit,
    image_url: data.image_url || null,
  };
};

const formatAction = (action: string) => {
  const map: Record<string, string> = {
    CREATE: "新增品种",
    UPDATE: "修改品种",
    DELETE: "删除品种",
  };
  return map[action] || action;
};

const formatUpdateDiff = (
  oldDataStr: string | null,
  newDataStr: string | null,
) => {
  return diffFields(oldDataStr, newDataStr, [
    { key: "name_zh", label: "品种名称" },
    { key: "default_price", label: "默认单价", format: (v) => `¥${v}` },
    { key: "default_unit", label: "默认单位" },
  ]);
};

const fetchSpeciesDetail = async () => {
  loading.value = true;
  errorMsg.value = "";
  try {
    const res = await api.get(`/species/${speciesId()}`);
    species.value = res.data;
    if (species.value) {
      syncForm(species.value);
    }

    // Fetch logs
    const logsRes = await api.get(`/logs/species/${speciesId()}`);
    logs.value = logsRes.data || [];
  } catch (error: any) {
    if (isAuthError(error)) return;
    console.error("Failed to fetch species detail", error);
    errorMsg.value = apiErrorMessage(error, "加载品种详情");
  } finally {
    loading.value = false;
  }
};

const saveSpecies = async () => {
  if (form.value.default_price <= 0) {
    alert("单价必须大于0");
    return;
  }
  saving.value = true;
  errorMsg.value = "";
  try {
    const res = await api.put(`/species/${speciesId()}`, form.value);
    species.value = res.data;
    syncForm(res.data);
    router.push("/species");
  } catch (error: any) {
    if (isAuthError(error)) return;
    console.error("Failed to save species", error);
    errorMsg.value = apiErrorMessage(error, "保存品种");
  } finally {
    saving.value = false;
  }
};

const handleImageUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("image", file);

  try {
    const res = await api.post(`/species/${speciesId()}/image`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    species.value = res.data;
    syncForm(res.data);
  } catch (error: any) {
    if (isAuthError(error)) return;
    console.error("Failed to upload image", error);
    errorMsg.value = apiErrorMessage(error, "图片上传");
  } finally {
    input.value = "";
  }
};

const removeSpecies = () => {
  showDeleteConfirm.value = true;
};

const executeDeleteSpecies = async () => {
  try {
    await api.delete(`/species/${speciesId()}`);
    showDeleteConfirm.value = false;
    router.push("/species");
  } catch (error: any) {
    if (isAuthError(error)) return;
    errorMsg.value = apiErrorMessage(error, "删除品种");
    showDeleteConfirm.value = false;
  }
};

const goBack = () => {
  router.push("/species");
};

watch(
  () => route.query.mode,
  (value) => {
    isEditing.value = value === "edit";
  },
);

watch(
  () => route.params.id,
  () => {
    fetchSpeciesDetail();
  },
);

onMounted(fetchSpeciesDetail);
</script>
