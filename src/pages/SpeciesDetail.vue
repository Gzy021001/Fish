<template>
  <div class="h-full flex flex-col relative">
    <Transition name="fade">
      <div
        v-if="errorMsg"
        class="absolute top-4 left-1/2 -translate-x-1/2 z-50 max-w-md w-auto px-5 py-2.5 bg-dunhuang-red/95 text-white rounded-lg text-sm shadow-lg backdrop-blur"
      >
        {{ errorMsg }}
      </div>
    </Transition>

    <Transition name="switch-fade" mode="out-in">
      <div
        v-if="loading"
        class="bg-white/80 backdrop-blur rounded-2xl shadow-sm border border-dunhuang-yellow/30 p-10 text-center text-dunhuang-text/60 flex-1"
      >
        正在加载品种详情...
      </div>

      <div
        v-else-if="species"
        class="bg-white rounded-2xl shadow-lg ring-1 ring-dunhuang-yellow/10 p-8 flex-1 min-h-0 flex flex-col"
      >
        <div
          class="flex items-center justify-between mb-8 border-b border-dunhuang-yellow/20 pb-4 shrink-0"
        >
          <div class="flex items-center gap-4">
            <button
              @click="isEditing ? cancelEdit() : goBack()"
              class="text-dunhuang-text/60 hover:text-dunhuang-blue transition-colors flex items-center justify-center w-8 h-8 rounded-full hover:bg-dunhuang-yellow/20"
              :title="isEditing ? '取消编辑' : '返回物命品种库'"
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
        </div>

        <div class="relative z-10 flex-1 min-h-0 overflow-hidden flex flex-col">
          <Transition name="fade">
            <div
              v-if="saveSuccess"
              class="absolute top-3 left-1/2 -translate-x-1/2 z-50 px-5 py-2.5 bg-dunhuang-green/95 text-white rounded-lg text-sm shadow-lg backdrop-blur"
            >
              品种信息已保存
            </div>
          </Transition>
          <div class="flex-1 flex gap-6 min-h-0">
            <template v-if="isEditing">
              <div
                class="flex-1 grid grid-cols-1 md:grid-cols-[7fr_3fr] gap-10 min-h-0"
              >
                <div class="w-full flex items-start justify-center">
                  <div class="w-full">
                    <SpeciesImageUpload
                      ref="imageUploadRef"
                      :image-url="species.image_url"
                      :name-zh="species.name_zh"
                      @select="onImageSelect"
                    />
                  </div>
                </div>

                <div
                  class="flex flex-col justify-center min-h-0 overflow-y-auto custom-scrollbar pr-1"
                >
                  <div class="flex flex-col space-y-5 w-full">
                    <div class="flex gap-3">
                      <div class="flex-1">
                        <span class="block text-xs text-dunhuang-text/50 mb-1.5"
                          >品种名称</span
                        >
                        <input
                          v-model="editForm.name_zh"
                          required
                          placeholder="例如：草鱼、鲤鱼、鲈鱼"
                          class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2.5 px-4 focus:ring-2 focus:ring-dunhuang-blue outline-none text-sm transition-shadow"
                        />
                      </div>
                      <div class="w-24 shrink-0">
                        <span class="block text-xs text-dunhuang-text/50 mb-1.5"
                          >单价（元/公斤）</span
                        >
                        <input
                          type="text"
                          inputmode="decimal"
                          v-model="editForm.default_price"
                          @blur="
                            editForm.default_price = (
                              +editForm.default_price || 0
                            ).toFixed(2)
                          "
                          placeholder="0.00"
                          class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2.5 px-2 text-center font-mono text-sm focus:ring-2 focus:ring-dunhuang-blue outline-none transition-shadow"
                        />
                      </div>
                    </div>
                    <div>
                      <span class="block text-xs text-dunhuang-text/50 mb-1.5"
                        >商家名称</span
                      >
                      <input
                        v-model="editForm.supplier_name"
                        placeholder="水产品供应商或商家名称"
                        class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2.5 px-4 focus:ring-2 focus:ring-dunhuang-blue outline-none text-sm transition-shadow"
                      />
                    </div>
                    <div>
                      <span class="block text-xs text-dunhuang-text/50 mb-1.5"
                        >商家介绍</span
                      >
                      <textarea
                        v-model="editForm.supplier_note"
                        rows="4"
                        placeholder="商家简介、产地、特色等信息"
                        class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2.5 px-4 focus:ring-2 focus:ring-dunhuang-blue outline-none text-sm transition-shadow resize-none custom-scrollbar"
                      ></textarea>
                    </div>
                  </div>
                </div>
              </div>
            </template>

            <template v-else>
              <!-- 左侧：品种信息 -->
              <div class="flex-1 min-w-0 space-y-5">
                <div
                  class="w-full max-w-lg sm:max-w-xl lg:max-w-2xl aspect-[16/11] rounded-xl overflow-hidden border-2 border-dunhuang-yellow/30 bg-white flex items-center justify-center shadow-sm relative group"
                  :class="{
                    'cursor-pointer hover:border-dunhuang-orange':
                      species.image_url,
                  }"
                  @click="openImagePreview"
                >
                  <img
                    v-if="species.image_url"
                    :src="species.image_url"
                    :alt="species.name_zh"
                    class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                  />
                  <div
                    v-else
                    class="w-full h-full bg-dunhuang-yellow/5 border border-dunhuang-yellow/30 text-dunhuang-blue flex items-center justify-center"
                  >
                    <span class="text-4xl font-bold opacity-30">{{
                      species.name_zh ? species.name_zh.charAt(0) : "?"
                    }}</span>
                  </div>
                </div>

                <div class="space-y-4">
                  <div>
                    <span class="block text-xs text-dunhuang-text/50 mb-1"
                      >品种</span
                    >
                    <p class="text-base font-medium text-dunhuang-blue">
                      {{ species.name_zh }}
                    </p>
                  </div>
                  <div>
                    <span class="block text-xs text-dunhuang-text/50 mb-1"
                      >单价（元/{{ species.default_unit || "公斤" }}）</span
                    >
                    <p class="text-base font-mono text-dunhuang-red">
                      {{ formatMoney(species.default_price) }}
                    </p>
                  </div>
                  <div v-if="species.supplier_name">
                    <span class="block text-xs text-dunhuang-text/50 mb-1"
                      >商家名称</span
                    >
                    <p class="text-base text-dunhuang-text">
                      {{ species.supplier_name }}
                    </p>
                  </div>
                  <div v-if="species.supplier_note">
                    <span class="block text-xs text-dunhuang-text/50 mb-1"
                      >商家介绍</span
                    >
                    <p
                      class="text-sm text-dunhuang-text/70 whitespace-pre-line"
                    >
                      {{ species.supplier_note }}
                    </p>
                  </div>
                </div>
              </div>

              <!-- 右侧：操作记录 -->
              <div
                v-if="filteredLogs.length > 0"
                class="flex-1 min-h-0 flex flex-col min-w-0 pl-3"
              >
                <h4
                  class="text-base font-serif text-dunhuang-blue font-bold mb-3 border-b border-dunhuang-yellow/10 pb-2 shrink-0"
                >
                  操作记录
                </h4>
                <div
                  class="flex-1 min-h-0 overflow-y-auto custom-scrollbar pr-1 space-y-3"
                >
                  <div
                    v-for="log in filteredLogs"
                    :key="log.id"
                    class="border-b border-dunhuang-yellow/15 pb-3 last:border-0 last:pb-0"
                  >
                    <div class="flex justify-between items-center mb-2">
                      <span
                        :class="[
                          'px-2 py-0.5 rounded text-xs font-medium',
                          log.action === 'CREATE'
                            ? 'bg-dunhuang-green/10 text-dunhuang-green'
                            : log.action === 'UPDATE'
                              ? 'bg-dunhuang-blue/10 text-dunhuang-blue'
                              : 'bg-dunhuang-red/10 text-dunhuang-red',
                        ]"
                        >{{ formatAction(log.action) }}</span
                      >
                      <span class="text-dunhuang-text/40 text-xs">{{
                        dateTimeStr(log.created_at)
                      }}</span>
                    </div>
                    <div
                      v-if="log.action === 'UPDATE'"
                      class="text-dunhuang-text/70 text-xs space-y-1.5"
                    >
                      <div
                        v-for="item in formatUpdateDiff(
                          log.old_data,
                          log.new_data,
                        )"
                        :key="item.label"
                        class="flex items-center gap-2 px-2.5 py-1.5 rounded-md bg-dunhuang-red/[0.06] border-l-[3px] border-dunhuang-red/40"
                      >
                        <span
                          class="shrink-0 text-dunhuang-red font-semibold text-[11px] min-w-[3.5rem]"
                          >{{ item.label }}</span
                        >
                        <span class="text-dunhuang-red/40 line-through">{{
                          item.old
                        }}</span>
                        <span class="text-dunhuang-blue mx-0.5">→</span>
                        <span class="text-dunhuang-green font-semibold">{{
                          item.new
                        }}</span>
                      </div>
                    </div>
                    <div
                      v-else-if="log.action === 'CREATE'"
                      class="text-dunhuang-text/50 text-xs"
                    >
                      创建了该品种
                    </div>
                  </div>
                </div>
              </div>
              <div
                v-else
                class="flex-1 flex items-center justify-center text-dunhuang-text/30 text-sm"
              >
                暂无操作记录
              </div>
            </template>
          </div>
          <div v-if="isEditing" class="flex justify-end gap-3 mt-6 shrink-0">
            <button
              @click="saveEdit"
              :disabled="saving"
              class="px-5 py-2 rounded-lg text-sm font-medium transition-colors bg-dunhuang-red text-white hover:bg-dunhuang-red/90 shadow-md disabled:opacity-50"
            >
              {{ saving ? "保存中..." : "保存" }}
            </button>
            <button
              @click="cancelEdit"
              class="px-5 py-2 rounded-lg text-sm transition-colors text-dunhuang-text/70 hover:bg-dunhuang-yellow/20 border border-dunhuang-yellow/50"
            >
              取消
            </button>
          </div>
        </div>
      </div>
    </Transition>
    <!-- 图片放大预览 -->
    <Teleport to="body">
      <div
        v-if="showImagePreview"
        class="fixed inset-0 z-[999] flex items-center justify-center p-8"
        @click="closeImagePreview"
      >
        <img
          :src="species?.image_url ?? ''"
          :alt="species?.name_zh"
          class="max-w-[90vw] max-h-[90vh] object-contain rounded-xl shadow-2xl"
          @click.stop
        />
        <button
          class="absolute top-4 right-4 w-10 h-10 rounded-full bg-dunhuang-text/10 hover:bg-dunhuang-text/20 text-dunhuang-text/60 flex items-center justify-center transition-colors"
          @click="closeImagePreview"
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
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import api from "../api";
import { apiErrorMessage, isAuthError } from "../lib/error";
import { dateTimeStr, diffFields, formatMoney } from "../lib/utils";
import SpeciesImageUpload from "../components/SpeciesImageUpload.vue";

interface SpeciesItem {
  id: number;
  name_zh: string;
  default_price: number;
  default_unit?: string;
  image_url?: string | null;
  supplier_name?: string;
  supplier_note?: string;
}

const route = useRoute();
const router = useRouter();

const loading = ref(true);
const errorMsg = ref("");
const species = ref<SpeciesItem | null>(null);
const showImagePreview = ref(false);
const logs = ref<any[]>([]);

const hasDiff = (log: any) => {
  return formatUpdateDiff(log.old_data, log.new_data).length > 0;
};

const filteredLogs = computed(() =>
  logs.value.filter((log) => log.action !== "UPDATE" || hasDiff(log)),
);

const speciesId = () => Number(route.params.id);

const isEditing = computed(() => route.query.mode === "edit");

const editForm = reactive({
  name_zh: "",
  default_price: "0.00",
  default_unit: "",
  supplier_name: "",
  supplier_note: "",
});
const saving = ref(false);
const saveSuccess = ref(false);

const selectedFile = ref<File | null>(null);
const imageUploadRef = ref<InstanceType<typeof SpeciesImageUpload> | null>(
  null,
);

const onImageSelect = (file: File | null) => {
  selectedFile.value = file;
};

const initEditForm = () => {
  if (species.value) {
    editForm.name_zh = species.value.name_zh;
    editForm.default_price = (species.value.default_price ?? 0).toFixed(2);
    editForm.default_unit = species.value.default_unit ?? "公斤";
    editForm.supplier_name = species.value.supplier_name ?? "";
    editForm.supplier_note = species.value.supplier_note ?? "";
  }
  imageUploadRef.value?.reset();
  selectedFile.value = null;
  saveSuccess.value = false;
};

const cancelEdit = () => {
  imageUploadRef.value?.reset();
  router.replace("/species");
};

const saveEdit = async () => {
  saving.value = true;
  errorMsg.value = "";
  saveSuccess.value = false;
  try {
    const res = await api.put(`/species/${speciesId()}`, {
      name_zh: editForm.name_zh.trim(),
      default_price: Number(editForm.default_price),
      default_unit: editForm.default_unit,
      image_url: species.value?.image_url ?? null,
      supplier_name: editForm.supplier_name.trim(),
      supplier_note: editForm.supplier_note.trim(),
    });
    if (species.value) {
      species.value.name_zh = res.data.name_zh ?? species.value.name_zh;
      species.value.default_price =
        res.data.default_price ?? species.value.default_price;
      species.value.default_unit =
        res.data.default_unit ?? species.value.default_unit;
      species.value.supplier_name =
        res.data.supplier_name ?? species.value.supplier_name;
      species.value.supplier_note =
        res.data.supplier_note ?? species.value.supplier_note;
    }

    if (selectedFile.value) {
      const formData = new FormData();
      formData.append("image", selectedFile.value);
      await api.post(`/species/${speciesId()}/image`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
    }

    saveSuccess.value = true;
    setTimeout(() => {
      router.replace("/species");
    }, 600);
  } catch (error: any) {
    if (isAuthError(error)) return;
    errorMsg.value = apiErrorMessage(error, "保存品种");
  } finally {
    saving.value = false;
  }
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
    { key: "name_zh", label: "品种" },
    {
      key: "default_price",
      label: "默认单价",
      format: (v) => Number(v).toFixed(2),
    },
    { key: "default_unit", label: "默认单位" },
  ]);
};

const fetchSpeciesDetail = async () => {
  loading.value = true;
  errorMsg.value = "";
  try {
    const res = await api.get(`/species/${speciesId()}`);
    species.value = res.data;

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

const goBack = () => {
  router.push("/species");
};

const openImagePreview = () => {
  if (species.value?.image_url) {
    showImagePreview.value = true;
  }
};

const closeImagePreview = () => {
  showImagePreview.value = false;
};

watch(
  () => route.params.id,
  () => {
    fetchSpeciesDetail();
  },
);

watch(isEditing, (editing) => {
  if (editing && species.value) {
    initEditForm();
  }
});

onMounted(async () => {
  await fetchSpeciesDetail();
  if (isEditing.value && species.value) {
    initEditForm();
  }
});
</script>
