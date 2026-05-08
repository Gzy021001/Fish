<template>
  <div class="h-full flex flex-col space-y-6">
    <div
      v-if="errorMsg"
      class="mb-4 p-3 bg-dunhuang-red/10 text-dunhuang-red rounded border border-dunhuang-red/20 text-sm shrink-0"
    >
      {{ errorMsg }}
    </div>

    <Transition name="switch-fade" mode="out-in">
      <div
        v-if="loading"
        class="bg-white/80 backdrop-blur rounded-2xl shadow-sm border border-dunhuang-yellow/30 p-10 text-center text-dunhuang-text/60 flex-1"
      >
        正在加载品种详情...
      </div>

      <div
        v-else-if="species"
        class="bg-white rounded-2xl shadow-md border border-dunhuang-yellow/30 p-8 flex-1 min-h-0 flex flex-col"
      >
        <div
          class="flex items-center justify-between mb-8 border-b-2 border-dunhuang-yellow/30 pb-4 shrink-0"
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
          <div v-if="isEditing" class="flex gap-3">
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

        <div class="relative z-10 flex-1 min-h-0 overflow-hidden flex flex-col">
          <div
            v-if="saveSuccess"
            class="mb-4 p-3 bg-dunhuang-green/10 text-dunhuang-green rounded border border-dunhuang-green/20 text-sm shrink-0"
          >
            品种信息已保存
          </div>
          <div class="flex-1 flex gap-6 min-h-0">
            <!-- 左侧：品种信息 -->
            <div class="flex-1 min-w-0 space-y-5">
              <div
                class="w-full max-w-md sm:max-w-lg lg:max-w-xl aspect-[4/3] rounded-xl overflow-hidden border-2 border-dunhuang-yellow/30 bg-white flex items-center justify-center shadow-sm relative group"
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

              <div class="space-y-3">
                <div>
                  <span class="block text-xs text-dunhuang-text/50 mb-1"
                    >品种</span
                  >
                  <p
                    v-if="!isEditing"
                    class="text-base font-medium text-dunhuang-blue"
                  >
                    {{ species.name_zh }}
                  </p>
                  <input
                    v-else
                    v-model="editForm.name_zh"
                    required
                    class="w-28 bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2 px-3 focus:ring-2 focus:ring-dunhuang-blue outline-none text-sm transition-shadow"
                  />
                </div>
                <div>
                  <span class="block text-xs text-dunhuang-text/50 mb-1"
                    >单价（元）</span
                  >
                  <p
                    v-if="!isEditing"
                    class="text-base font-mono text-dunhuang-red"
                  >
                    {{ formatMoney(species.default_price) }}
                  </p>
                  <input
                    v-else
                    type="number"
                    step="0.01"
                    min="0"
                    v-model.number="editForm.default_price"
                    @blur="
                      editForm.default_price = Number(
                        (editForm.default_price || 0).toFixed(2),
                      )
                    "
                    class="w-28 bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2 px-3 text-center focus:ring-2 focus:ring-dunhuang-blue outline-none font-mono text-sm transition-shadow [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
                  />
                </div>
              </div>
            </div>

            <!-- 右侧：操作记录 -->
            <div
              v-if="filteredLogs.length > 0"
              class="flex-1 min-h-0 flex flex-col min-w-0"
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
                    <div class="text-dunhuang-text/40 mb-1">数据变更明细：</div>
                    <div
                      v-for="item in formatUpdateDiff(
                        log.old_data,
                        log.new_data,
                      )"
                      :key="item.label"
                      class="flex gap-2 items-center whitespace-nowrap"
                    >
                      <span
                        class="w-16 shrink-0 text-dunhuang-text/50 text-[11px]"
                        >{{ item.label }}:</span
                      >
                      <span class="line-through text-dunhuang-red/50">{{
                        item.old
                      }}</span>
                      <span class="text-dunhuang-blue/60">→</span>
                      <span class="text-dunhuang-green">{{ item.new }}</span>
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

interface SpeciesItem {
  id: number;
  name_zh: string;
  default_price: number;
  image_url?: string | null;
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

const editForm = reactive({ name_zh: "", default_price: 0 });
const saving = ref(false);
const saveSuccess = ref(false);

const initEditForm = () => {
  if (species.value) {
    editForm.name_zh = species.value.name_zh;
    editForm.default_price = species.value.default_price;
  }
  saveSuccess.value = false;
};

const cancelEdit = () => {
  router.replace({ name: "SpeciesDetail", params: { id: speciesId() } });
};

const saveEdit = async () => {
  saving.value = true;
  errorMsg.value = "";
  saveSuccess.value = false;
  try {
    const res = await api.put(`/species/${speciesId()}`, {
      name_zh: editForm.name_zh.trim(),
      default_price: editForm.default_price,
    });
    species.value = res.data;
    saveSuccess.value = true;
    setTimeout(() => {
      router.replace({ name: "SpeciesDetail", params: { id: speciesId() } });
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
    { key: "default_price", label: "默认单价", format: (v) => String(v) },
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
