<template>
  <div class="h-full flex flex-col space-y-6">
    <Transition name="switch-fade" mode="out-in">
      <div
        v-if="showForm"
        class="bg-white rounded-2xl shadow-md border border-dunhuang-yellow/30 p-8 flex-1"
      >
        <div
          class="flex items-center justify-between mb-8 border-b-2 border-dunhuang-yellow/30 pb-4"
        >
          <div class="flex items-center gap-4">
            <button
              @click="goBackToList"
              class="text-dunhuang-text/60 hover:text-dunhuang-blue transition-colors flex items-center justify-center w-8 h-8 rounded-full hover:bg-dunhuang-yellow/20"
              title="返回列表"
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
              {{ t("common.billing") }}
            </h2>
          </div>
        </div>

        <form @submit.prevent="handleSaveBill" class="space-y-6 relative z-10">
          <!-- 编辑模式 -->
          <template v-if="bill.id">
            <div
              v-if="editingSpecies"
              class="rounded-2xl bg-gradient-to-br from-dunhuang-red/[0.06] to-dunhuang-bg p-6 flex items-stretch gap-6 shadow-md ring-1 ring-dunhuang-red/10"
            >
              <div
                class="shrink-0 w-32 h-32 rounded-2xl overflow-hidden shadow-md ring-1 ring-dunhuang-yellow/20"
              >
                <img
                  v-if="editingSpecies.image_url"
                  :src="editingSpecies.image_url"
                  :alt="editingSpecies.name_zh"
                  class="w-full h-full object-cover"
                />
                <div
                  v-else
                  class="w-full h-full bg-dunhuang-yellow/[0.08] flex items-center justify-center text-dunhuang-blue"
                >
                  <span class="text-4xl font-bold font-serif opacity-40">{{
                    editingSpecies.name_zh
                      ? editingSpecies.name_zh.charAt(0)
                      : "?"
                  }}</span>
                </div>
              </div>
              <div class="flex flex-col justify-center min-w-0">
                <h4 class="font-bold text-dunhuang-blue text-xl mb-2">
                  {{ editingSpecies.name_zh }}
                </h4>
                <div class="text-sm text-dunhuang-text/60 tabular-nums">
                  参考价
                  <span
                    class="text-dunhuang-red font-mono font-bold text-base"
                    >{{ formatMoney(editingSpecies.default_price) }}</span
                  >
                  元/{{ editingSpecies.default_unit }}
                </div>
              </div>
            </div>
            <div v-else class="text-sm text-dunhuang-text/50">未找到品种</div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label class="block text-sm font-medium text-dunhuang-text mb-2"
                  >{{ t("billing.unit_price") }}（元）</label
                >
                <input
                  type="text"
                  :value="(+bill.unit_price || 0).toFixed(2)"
                  disabled
                  class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-3 px-4 text-sm focus:ring-0 outline-none font-mono text-dunhuang-red disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-dunhuang-text mb-2"
                  >重量 ({{ editingSpecies?.default_unit ?? "公斤" }})</label
                >
                <input
                  type="text"
                  inputmode="decimal"
                  v-model="bill.weight"
                  @blur="bill.weight = (+bill.weight || 0).toFixed(2)"
                  required
                  class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-3 px-4 text-sm focus:ring-0 outline-none font-mono"
                />
              </div>
              <div class="hidden">
                <select v-model="bill.fee_type" class="hidden">
                  <option value="FIXED">固定金额</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-dunhuang-text mb-2"
                  >服务费（元）</label
                >
                <input
                  type="text"
                  inputmode="decimal"
                  v-model="bill.fee_value"
                  @blur="bill.fee_value = (+bill.fee_value || 0).toFixed(2)"
                  required
                  class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-3 px-4 text-sm focus:ring-0 outline-none font-mono"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-dunhuang-text mb-2"
                  >放生日期</label
                >
                <DateInput
                  v-model="bill.release_date"
                  placeholder="选择放生日期"
                />
              </div>
            </div>
          </template>

          <!-- 新增模式 -->
          <template v-else>
            <div class="space-y-6">
              <!-- 品种选择 -->
              <div>
                <label
                  class="block text-sm font-medium text-dunhuang-text mb-3"
                  >{{ t("billing.species_name") }}</label
                >
                <div
                  class="relative rounded-xl bg-dunhuang-bg/30 border border-dunhuang-yellow/20"
                >
                  <div
                    class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3 overflow-y-auto custom-scrollbar max-h-[200px] p-3"
                  >
                    <div
                      v-for="sp in speciesList"
                      :key="sp.id"
                      @click="toggleEntry(sp)"
                      :class="[
                        'cursor-pointer relative overflow-hidden rounded-xl border-2 p-3 transition-all duration-200 flex flex-col items-center justify-center gap-1.5 group',
                        isEntrySelected(sp.id)
                          ? 'border-dunhuang-red bg-dunhuang-red/5 shadow-[0_2px_12px_rgb(187,49,52,0.12)]'
                          : 'border-dunhuang-yellow/40 bg-white hover:border-dunhuang-orange hover:shadow-md',
                      ]"
                    >
                      <div
                        v-if="isEntrySelected(sp.id)"
                        class="absolute top-0 right-0 w-7 h-7 bg-dunhuang-red flex items-start justify-end p-0.5 rounded-bl-xl"
                      >
                        <svg
                          class="w-3.5 h-3.5 text-white"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="3"
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      </div>
                      <img
                        v-if="sp.image_url"
                        :src="sp.image_url"
                        :alt="sp.name_zh"
                        class="w-12 h-12 rounded-full object-cover border-2 border-dunhuang-yellow/30 shadow-sm"
                      />
                      <div
                        v-else
                        class="w-12 h-12 rounded-full bg-dunhuang-yellow/10 border-2 border-dunhuang-yellow/30 flex items-center justify-center text-dunhuang-blue shadow-sm"
                      >
                        <span class="text-lg font-bold">{{
                          sp.name_zh ? sp.name_zh.charAt(0) : "?"
                        }}</span>
                      </div>
                      <div class="text-center">
                        <h4 class="font-medium text-dunhuang-blue text-sm">
                          {{ sp.name_zh }}
                        </h4>
                        <div class="text-xs text-dunhuang-text/50 mt-0.5">
                          {{ formatMoney(sp.default_price) }}
                        </div>
                      </div>
                    </div>
                  </div>
                  <div
                    class="pointer-events-none absolute left-0 right-0 bottom-0 h-6 bg-gradient-to-t from-dunhuang-bg/30 to-transparent rounded-b-xl"
                  ></div>
                </div>
              </div>

              <!-- 已选品种编辑区 -->
              <div v-if="billEntries.length > 0" class="space-y-3">
                <div class="flex items-center justify-between">
                  <span class="text-sm font-medium text-dunhuang-text"
                    >已选
                    <span class="text-dunhuang-blue font-bold">{{
                      billEntries.length
                    }}</span>
                    个品种</span
                  >
                </div>
                <div
                  class="grid grid-cols-1 md:grid-cols-2 gap-3 overflow-y-auto custom-scrollbar max-h-[316px] pr-2"
                >
                  <div
                    v-for="(entry, idx) in billEntries"
                    :key="entry.species_id"
                    class="rounded-xl border border-dunhuang-yellow/20 bg-white p-4 transition-shadow hover:shadow-sm"
                  >
                    <div
                      class="flex items-center gap-3 mb-3 pb-2 border-b border-dunhuang-yellow/15"
                    >
                      <img
                        v-if="getEntrySpecies(entry.species_id)?.image_url"
                        :src="getEntrySpecies(entry.species_id)!.image_url!"
                        :alt="getEntryName(entry.species_id)"
                        class="w-10 h-10 rounded-full object-cover border border-dunhuang-yellow/30"
                      />
                      <div
                        v-else
                        class="w-10 h-10 rounded-full bg-dunhuang-yellow/10 border border-dunhuang-yellow/30 flex items-center justify-center text-dunhuang-blue"
                      >
                        <span class="text-sm font-bold">{{
                          getEntryName(entry.species_id).charAt(0)
                        }}</span>
                      </div>
                      <div class="flex-1">
                        <span class="font-medium text-dunhuang-blue text-sm">{{
                          getEntryName(entry.species_id)
                        }}</span>
                        <span class="text-xs text-dunhuang-text/40 ml-2">{{
                          getEntryUnit(entry.species_id)
                        }}</span>
                      </div>
                      <button
                        type="button"
                        @click="removeEntry(idx)"
                        class="text-dunhuang-text/30 hover:text-dunhuang-red transition-colors w-6 h-6 flex items-center justify-center rounded-full hover:bg-dunhuang-red/8"
                        title="移除此品种"
                      >
                        <svg
                          class="w-3.5 h-3.5"
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
                    <div class="grid grid-cols-3 gap-2">
                      <div>
                        <label class="block text-xs text-dunhuang-text/50 mb-1"
                          >单价（元）</label
                        >
                        <input
                          type="text"
                          :value="
                            (
                              getEntrySpecies(entry.species_id)
                                ?.default_price ??
                              entry.unit_price ??
                              0
                            ).toFixed(2)
                          "
                          disabled
                          class="w-full bg-dunhuang-bg border border-dunhuang-yellow/40 rounded-lg px-2.5 py-1.5 text-sm focus:ring-0 outline-none font-mono text-dunhuang-red disabled:opacity-50 disabled:cursor-not-allowed"
                        />
                      </div>
                      <div>
                        <label class="block text-xs text-dunhuang-text/50 mb-1"
                          >总重 ({{
                            editingSpecies?.default_unit ?? "公斤"
                          }})</label
                        >
                        <input
                          type="text"
                          inputmode="decimal"
                          v-model="entry.weight"
                          @blur="entry.weight = (+entry.weight || 0).toFixed(2)"
                          class="w-full bg-dunhuang-bg border border-dunhuang-yellow/40 rounded-lg px-2.5 py-1.5 text-sm focus:ring-0 outline-none font-mono"
                        />
                      </div>
                      <div>
                        <label class="block text-xs text-dunhuang-text/50 mb-1"
                          >服务费（元）</label
                        >
                        <input
                          type="text"
                          inputmode="decimal"
                          v-model="entry.fee_value"
                          @blur="
                            entry.fee_value = (+entry.fee_value || 0).toFixed(2)
                          "
                          class="w-full bg-dunhuang-bg border border-dunhuang-yellow/40 rounded-lg px-2.5 py-1.5 text-sm focus:ring-0 outline-none font-mono"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div
                v-else
                class="text-center text-sm text-dunhuang-text/40 py-6"
              >
                点击上方品种卡片开始添加
              </div>
            </div>
          </template>

          <!-- 编辑模式汇总 -->
          <template v-if="bill.id">
            <div
              class="space-y-0 rounded-xl border border-dunhuang-yellow/30 bg-dunhuang-bg/50 overflow-hidden w-48"
            >
              <div
                class="flex justify-between items-center px-4 py-2.5 text-sm"
              >
                <span class="text-dunhuang-text/60"
                  >{{ t("billing.subtotal") }}（元）</span
                >
                <span class="tabular-nums text-dunhuang-blue font-medium">{{
                  formatMoney(editSubtotal)
                }}</span>
              </div>
              <div
                class="flex justify-between items-center px-4 py-2.5 text-sm border-t border-dunhuang-yellow/20"
              >
                <span class="text-dunhuang-text/60"
                  >{{ t("billing.fee_value") }}（元）</span
                >
                <span class="tabular-nums text-dunhuang-text/60">{{
                  formatMoney(editFee)
                }}</span>
              </div>
              <div
                class="flex justify-between items-center px-4 py-2.5 text-sm bg-dunhuang-red/5 border-t border-dunhuang-red/10"
              >
                <span class="text-dunhuang-text/80 font-medium"
                  >{{ t("billing.total") }}（元）</span
                >
                <span class="tabular-nums font-bold text-dunhuang-red">{{
                  formatMoney(editTotal)
                }}</span>
              </div>
            </div>
          </template>

          <!-- 汇总区域 -->
          <div
            class="mt-8 flex flex-col md:flex-row items-end justify-between gap-6"
          >
            <div
              v-if="!bill.id"
              class="space-y-0 rounded-xl border border-dunhuang-yellow/30 bg-dunhuang-bg/50 overflow-hidden w-48"
            >
              <div
                class="flex justify-between items-center px-4 py-2.5 text-sm"
              >
                <span class="text-dunhuang-text/60"
                  >{{ t("billing.subtotal") }}（元）</span
                >
                <span class="tabular-nums text-dunhuang-blue font-medium">{{
                  formatMoney(batchSubtotal)
                }}</span>
              </div>
              <div
                class="flex justify-between items-center px-4 py-2.5 text-sm border-t border-dunhuang-yellow/20"
              >
                <span class="text-dunhuang-text/60"
                  >{{ t("billing.fee_value") }}（元）</span
                >
                <span class="tabular-nums text-dunhuang-text/60">{{
                  formatMoney(batchFee)
                }}</span>
              </div>
              <div
                class="flex justify-between items-center px-4 py-2.5 text-sm bg-dunhuang-red/5 border-t border-dunhuang-red/10"
              >
                <span class="text-dunhuang-text/80 font-medium"
                  >{{ t("billing.total") }}（元）</span
                >
                <span class="tabular-nums font-bold text-dunhuang-red">{{
                  formatMoney(batchTotal)
                }}</span>
              </div>
            </div>

            <div class="flex justify-end w-full md:w-auto md:ml-auto">
              <button
                type="submit"
                :disabled="saving"
                class="px-6 py-2 rounded text-sm font-medium transition-colors bg-dunhuang-red text-white hover:bg-dunhuang-red/90 shadow-md disabled:opacity-50"
              >
                {{ saving ? "保存中..." : t("billing.save") }}
              </button>
            </div>
          </div>
        </form>
      </div>
    </Transition>

    <!-- 历史单据列表 -->
    <Transition name="switch-fade" mode="out-in">
      <div
        v-if="!showForm"
        class="bg-white rounded-2xl shadow-md border border-dunhuang-yellow/30 p-8"
      >
        <div class="flex items-center justify-between mb-6">
          <div
            class="flex items-center gap-6 border-b border-dunhuang-yellow/30 pb-2"
          >
            <button
              v-for="tab in tabs"
              :key="tab.key"
              @click="switchTab(tab.key)"
              :class="[
                'text-lg font-serif font-bold transition-colors pb-1 -mb-[5px] border-b-2',
                activeTab === tab.key
                  ? 'text-dunhuang-blue border-dunhuang-blue'
                  : 'text-dunhuang-text/50 border-transparent hover:text-dunhuang-blue/70',
              ]"
            >
              {{ tab.label }}
            </button>
          </div>

          <div class="flex gap-2 items-center">
            <!-- 日期筛选 -->
            <div class="relative">
              <button
                @click="toggleShowDatePicker"
                :class="[
                  'flex items-center gap-1.5 rounded-lg px-3 h-8 text-sm font-medium transition-all duration-200',
                  dateRangeLabel
                    ? 'bg-dunhuang-blue/[0.08] text-dunhuang-blue border border-dunhuang-blue/20 hover:border-dunhuang-blue/40'
                    : 'bg-dunhuang-bg/50 text-dunhuang-text/40 border border-dunhuang-blue/15 hover:text-dunhuang-text/60 hover:border-dunhuang-blue/35',
                ]"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  class="shrink-0"
                >
                  <rect width="18" height="18" x="3" y="4" rx="2" ry="2" />
                  <line x1="16" x2="16" y1="2" y2="6" />
                  <line x1="8" x2="8" y1="2" y2="6" />
                  <line x1="3" x2="21" y1="10" y2="10" />
                </svg>
                <span>{{ dateRangeLabel || "选择筛选日期" }}</span>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  class="shrink-0"
                  :class="showDatePicker ? 'rotate-180' : ''"
                >
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              </button>
              <button
                v-if="filterDateFrom || filterDateTo"
                @click="clearDateFilter"
                class="ml-0.5 text-dunhuang-text/30 hover:text-dunhuang-red text-xs leading-none transition-colors"
                title="清除日期筛选"
              >
                ✕
              </button>

              <Transition name="dropdown">
                <div
                  v-if="showDatePicker"
                  class="absolute top-full mt-1.5 right-0 z-30"
                  @click.stop
                >
                  <div
                    class="bg-white rounded-2xl shadow-xl border border-dunhuang-yellow/20 p-4 w-[312px]"
                  >
                    <div class="flex flex-wrap gap-1.5 mb-3">
                      <button
                        v-for="preset in datePresets"
                        :key="preset.label"
                        @click="applyDatePreset(preset)"
                        :class="[
                          'px-2.5 py-1 text-xs rounded-full border transition-colors',
                          isPresetActive(preset)
                            ? 'bg-dunhuang-blue/10 text-dunhuang-blue border-dunhuang-blue/30'
                            : 'bg-dunhuang-bg/50 text-dunhuang-text/60 border-dunhuang-yellow/15 hover:border-dunhuang-blue/30 hover:text-dunhuang-blue',
                        ]"
                      >
                        {{ preset.label }}
                      </button>
                    </div>

                    <div class="flex items-center gap-2">
                      <div class="flex-1">
                        <label class="block text-xs text-dunhuang-text/40 mb-1"
                          >开始月份</label
                        >
                        <input
                          type="month"
                          v-model="pickerFromMonth"
                          class="w-full bg-dunhuang-bg border border-dunhuang-yellow/25 rounded-lg px-3 py-2 text-sm text-dunhuang-blue focus:ring-0 focus:border-dunhuang-blue/50 outline-none transition-all"
                        />
                      </div>
                      <span class="text-dunhuang-text/30 mt-5">—</span>
                      <div class="flex-1">
                        <label class="block text-xs text-dunhuang-text/40 mb-1"
                          >结束月份</label
                        >
                        <input
                          type="month"
                          v-model="pickerToMonth"
                          class="w-full bg-dunhuang-bg border border-dunhuang-yellow/25 rounded-lg px-3 py-2 text-sm text-dunhuang-blue focus:ring-0 focus:border-dunhuang-blue/50 outline-none transition-all"
                        />
                      </div>
                    </div>

                    <div
                      class="flex justify-end gap-2 mt-3 pt-3 border-t border-dunhuang-yellow/10"
                    >
                      <button
                        @click="cancelDatePicker"
                        class="px-3 py-1.5 rounded-lg text-xs text-dunhuang-text/50 hover:text-dunhuang-text/70 hover:bg-dunhuang-yellow/5 transition-colors"
                      >
                        取消
                      </button>
                      <button
                        @click="dateApply"
                        class="px-4 py-1.5 rounded-lg text-xs font-medium bg-dunhuang-blue text-white hover:bg-dunhuang-blue/90 transition-colors shadow-sm"
                      >
                        确认
                      </button>
                    </div>
                  </div>
                </div>
              </Transition>
            </div>

            <!-- 搜索 -->
            <div
              class="flex items-center bg-dunhuang-bg/50 border border-dunhuang-blue/15 rounded-lg px-2.5 transition-all duration-200 hover:border-dunhuang-blue/35 focus-within:border-dunhuang-blue focus-within:ring-2 focus-within:ring-dunhuang-blue/15 focus-within:bg-white h-8"
            >
              <button
                type="button"
                @click="performSearch"
                class="text-dunhuang-blue/50 hover:text-dunhuang-blue transition-colors shrink-0"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="15"
                  height="15"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" x2="16.65" y1="21" y2="16.65"></line>
                </svg>
              </button>
              <input
                type="text"
                v-model="searchText"
                placeholder="搜索品种..."
                @keydown.enter="performSearch"
                class="bg-transparent border-none text-sm text-dunhuang-blue font-medium focus:outline-none focus:ring-0 p-0 w-28 ml-1.5 placeholder:text-dunhuang-text/30"
              />
              <button
                v-if="searchText"
                @click="clearSearchText"
                class="text-dunhuang-text/30 hover:text-dunhuang-red text-xs leading-none px-1 transition-colors"
              >
                ✕
              </button>
            </div>

            <!-- 批量删除 -->
            <button
              v-if="selectedBillIds.length > 0"
              @click="confirmBatchDeleteBills"
              class="h-8 px-3.5 rounded-lg text-sm font-medium transition-all duration-200 text-dunhuang-red hover:bg-dunhuang-red/8 border border-dunhuang-red/25 hover:border-dunhuang-red/40"
            >
              批量删除 ({{ selectedBillIds.length }})
            </button>

            <!-- 导出 -->
            <button
              @click="exportBills"
              type="button"
              class="h-8 px-3.5 rounded-lg text-sm font-medium transition-all duration-200 text-dunhuang-blue/80 hover:text-dunhuang-blue hover:bg-dunhuang-blue/6 border border-dunhuang-blue/15 hover:border-dunhuang-blue/35"
            >
              {{ activeTab === "current" ? "导出" : "导出" }}
            </button>

            <!-- current tab 专有按钮 -->
            <template v-if="activeTab === 'current'">
              <button
                @click="goToImport"
                type="button"
                class="h-8 px-3.5 rounded-lg text-sm font-medium transition-all duration-200 text-dunhuang-blue/80 hover:text-dunhuang-blue hover:bg-dunhuang-blue/6 border border-dunhuang-blue/15 hover:border-dunhuang-blue/35"
              >
                导入
              </button>
              <button
                @click="
                  initNewBill();
                  showForm = true;
                "
                class="h-8 px-4 rounded-lg text-sm font-semibold transition-all duration-200 bg-dunhuang-blue text-white hover:bg-dunhuang-blue/90 shadow-sm hover:shadow-md"
              >
                新增单据
              </button>
            </template>
          </div>
        </div>

        <div
          class="border border-dunhuang-yellow/30 rounded-lg bg-white overflow-hidden"
        >
          <div class="overflow-y-auto custom-scrollbar">
            <div class="flex flex-col">
              <div
                class="sticky top-0 bg-dunhuang-bg/90 backdrop-blur z-20 flex w-full shrink-0"
              >
                <div
                  class="bg-dunhuang-yellow/20 text-dunhuang-blue font-sans font-bold text-sm flex w-full"
                >
                  <div
                    class="px-3 py-2 border-b border-dunhuang-yellow/40 flex items-center justify-center w-10 shrink-0 sticky left-0 bg-dunhuang-yellow/20 backdrop-blur z-30 sticky-col-left"
                  >
                    <input
                      type="checkbox"
                      class="w-4 h-4 rounded border-2 border-dunhuang-yellow/40 text-dunhuang-blue focus:ring-0 focus:ring-offset-0 cursor-pointer transition-all duration-200"
                      :checked="isAllSelected"
                      @change="toggleSelectAll"
                    />
                  </div>
                  <div class="col-th flex-[0.25] flex items-center">序号</div>
                  <div class="col-th flex-[0.55] flex items-center">品种</div>
                  <div class="col-th flex-[0.5] flex items-center">
                    重量（公斤）
                  </div>
                  <div class="col-th flex-[0.6] flex items-center">
                    单价（元）
                  </div>
                  <div class="col-th flex-[0.6] flex items-center">
                    小计（元）
                  </div>
                  <div class="col-th flex-[0.5] flex items-center">
                    服务费（元）
                  </div>
                  <div class="col-th flex-[0.6] flex items-center">
                    总金额（元）
                  </div>
                  <div class="col-th flex-[0.7] flex items-center">
                    放生日期
                  </div>
                  <div class="col-th flex-[0.9] flex items-center">
                    添加时间
                  </div>
                  <div
                    v-if="activeTab === 'current'"
                    class="col-th flex items-center justify-center w-40 shrink-0 sticky right-0 bg-dunhuang-yellow/20 backdrop-blur z-30 sticky-col-right"
                  >
                    操作
                  </div>
                </div>
              </div>

              <div class="flex flex-col relative">
                <div
                  v-for="(b, index) in paginatedBills"
                  :key="b.id"
                  class="border-b border-dunhuang-yellow/20 hover:bg-dunhuang-yellow/10 transition-colors text-sm group flex w-full shrink-0 h-[45px]"
                >
                  <div
                    class="px-3 py-2 flex items-center justify-center w-10 shrink-0 sticky left-0 bg-white/60 backdrop-blur-md group-hover:bg-dunhuang-yellow/10 transition-colors sticky-col-left"
                  >
                    <input
                      type="checkbox"
                      class="w-4 h-4 rounded border-2 border-dunhuang-yellow/40 text-dunhuang-blue focus:ring-0 focus:ring-offset-0 cursor-pointer transition-all duration-200"
                      :value="b.id"
                      v-model="selectedBillIds"
                    />
                  </div>
                  <div class="col-td-muted flex-[0.25] flex items-center">
                    {{ (currentPage - 1) * pageSize + index + 1 }}
                  </div>
                  <div class="col-td font-medium flex-[0.55] flex items-center">
                    {{ getSpeciesName(b.species_id) }}
                  </div>
                  <div class="col-td tabular-nums flex-[0.5] flex items-center">
                    {{ formatMoney(b.weight) }}
                  </div>
                  <div class="col-td-mono-red flex-[0.6] flex items-center">
                    {{ formatMoney(b.unit_price) }}
                  </div>
                  <div class="col-td-green flex-[0.6] flex items-center">
                    {{ formatMoney(b.subtotal) }}
                  </div>
                  <div class="col-td tabular-nums flex-[0.5] flex items-center">
                    {{ formatFee(b) }}
                  </div>
                  <div class="col-td-mono-red flex-[0.6] flex items-center">
                    {{ formatMoney(b.total_amount) }}
                  </div>
                  <div class="col-td flex-[0.7] flex items-center">
                    {{ dateStr(b.release_date || b.created_at) }}
                  </div>
                  <div class="col-td-time flex-[0.9] flex items-center">
                    {{ dateTimeStr(b.created_at) }}
                  </div>
                  <div
                    v-if="activeTab === 'current'"
                    class="px-3 py-2 flex items-center justify-center w-40 shrink-0 sticky right-0 bg-white/60 backdrop-blur-md group-hover:bg-dunhuang-yellow/10 transition-colors sticky-col-right"
                  >
                    <div class="flex items-center justify-center gap-1">
                      <button
                        @click="viewBill(b)"
                        class="px-2 py-1 rounded text-xs transition-colors text-dunhuang-blue hover:bg-dunhuang-blue/10 border border-transparent hover:border-dunhuang-blue/30"
                      >
                        查看
                      </button>
                      <button
                        @click="editBill(b)"
                        class="px-2 py-1 rounded text-xs transition-colors text-dunhuang-green hover:bg-dunhuang-green/10 border border-transparent hover:border-dunhuang-green/30"
                      >
                        编辑
                      </button>
                      <button
                        @click="confirmDeleteBill(b.id)"
                        class="px-2 py-1 rounded text-xs transition-colors text-dunhuang-red hover:bg-dunhuang-red/10 border border-transparent hover:border-dunhuang-red/30"
                      >
                        删除
                      </button>
                    </div>
                  </div>
                </div>
                <template
                  v-for="i in pageSize - paginatedBills.length"
                  :key="'placeholder-' + i"
                >
                  <div
                    class="border-b border-dunhuang-yellow/10 text-sm flex w-full shrink-0 h-[45px]"
                  >
                    <div
                      class="px-3 py-2 flex items-center justify-center w-10 shrink-0 sticky left-0 bg-white/60 sticky-col-left"
                    ></div>
                    <div
                      class="col-td-muted flex-[0.25] flex items-center"
                    ></div>
                    <div
                      class="col-td font-medium flex-[0.55] flex items-center"
                    ></div>
                    <div
                      class="col-td tabular-nums flex-[0.5] flex items-center"
                    ></div>
                    <div
                      class="col-td-mono-red flex-[0.6] flex items-center"
                    ></div>
                    <div
                      class="col-td-green flex-[0.6] flex items-center"
                    ></div>
                    <div
                      class="col-td tabular-nums flex-[0.5] flex items-center"
                    ></div>
                    <div
                      class="col-td-mono-red flex-[0.6] flex items-center"
                    ></div>
                    <div class="col-td flex-[0.7] flex items-center"></div>
                    <div class="col-td-time flex-[0.9] flex items-center"></div>
                    <div
                      v-if="activeTab === 'current'"
                      class="px-3 py-2 flex items-center justify-center w-40 shrink-0 sticky right-0 bg-white/60 sticky-col-right"
                    ></div>
                  </div>
                </template>
                <div
                  class="flex w-full shrink-0 h-[42px] bg-dunhuang-yellow/5 border-t-2 border-dunhuang-yellow/30"
                >
                  <div
                    class="w-10 shrink-0 sticky left-0 bg-dunhuang-yellow/5 sticky-col-left"
                  ></div>
                  <div class="px-4 py-2 flex-[0.25] flex items-center"></div>
                  <div class="px-4 py-2 flex-[0.55] flex items-center"></div>
                  <div class="px-4 py-2 flex-[0.5] flex items-center">
                    <span class="tabular-nums text-xs text-dunhuang-text/60">{{
                      formatMoney(tableSumWeight)
                    }}</span>
                  </div>
                  <div class="px-4 py-2 flex-[0.6] flex items-center"></div>
                  <div class="px-4 py-2 flex-[0.6] flex items-center">
                    <span class="tabular-nums text-xs text-dunhuang-green">{{
                      formatMoney(tableSumSubtotal)
                    }}</span>
                  </div>
                  <div class="px-4 py-2 flex-[0.5] flex items-center">
                    <span class="tabular-nums text-xs text-dunhuang-text/60">{{
                      formatMoney(tableSumFee)
                    }}</span>
                  </div>
                  <div class="px-4 py-2 flex-[0.6] flex items-center">
                    <span class="tabular-nums text-xs text-dunhuang-red">{{
                      formatMoney(tableSumTotal)
                    }}</span>
                  </div>
                  <div class="px-4 py-2 flex-[0.9] flex items-center"></div>
                  <div
                    v-if="activeTab === 'current'"
                    class="px-3 py-2 w-40 shrink-0 sticky right-0 bg-dunhuang-yellow/5 sticky-col-right"
                  ></div>
                </div>
                <div
                  v-if="bills.length === 0"
                  class="absolute inset-0 flex items-center justify-center pointer-events-none"
                >
                  <div
                    class="text-dunhuang-text/50 bg-white/50 px-6 py-2 rounded-full backdrop-blur-sm shadow-sm border border-dunhuang-yellow/30"
                  >
                    暂无单据
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div
          class="flex justify-between items-center mt-4 shrink-0 relative z-10"
        >
          <div class="text-sm text-dunhuang-text/70">
            共
            <span class="font-bold text-dunhuang-blue">{{ totalItems }}</span>
            条记录
          </div>

          <!-- 分页控件 -->
          <div class="flex items-center gap-2" v-if="totalPages > 1">
            <button
              @click="currentPage--"
              :disabled="currentPage === 1"
              class="w-8 h-8 flex items-center justify-center rounded border border-dunhuang-yellow/50 text-dunhuang-blue hover:bg-dunhuang-yellow/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </button>
            <div class="flex gap-1">
              <button
                v-for="page in displayedPages"
                :key="page"
                @click="currentPage = page"
                :class="[
                  'w-8 h-8 flex items-center justify-center rounded border transition-colors text-sm',
                  currentPage === page
                    ? 'bg-dunhuang-blue border-dunhuang-blue text-white shadow-sm'
                    : 'border-dunhuang-yellow/50 text-dunhuang-text/80 hover:bg-dunhuang-yellow/20',
                ]"
              >
                {{ page }}
              </button>
            </div>
            <button
              @click="currentPage++"
              :disabled="currentPage === totalPages"
              class="w-8 h-8 flex items-center justify-center rounded border border-dunhuang-yellow/50 text-dunhuang-blue hover:bg-dunhuang-yellow/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 查看详情弹窗 -->
    <Transition name="slide-up">
      <div
        v-if="showViewModal"
        class="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 bg-white rounded-2xl shadow-2xl border border-dunhuang-yellow/30 w-full max-w-4xl max-h-[85vh] flex flex-col overflow-hidden"
      >
        <!-- 标题栏 -->
        <div
          class="flex items-center justify-between px-8 pt-6 pb-4 border-b border-dunhuang-yellow/20 shrink-0"
        >
          <div class="flex items-center gap-3">
            <div class="w-1 h-6 bg-dunhuang-red rounded-full"></div>
            <h3 class="text-xl font-serif text-dunhuang-blue font-bold">
              单据详情与记录
            </h3>
          </div>
          <button
            @click="showViewModal = false"
            class="w-8 h-8 flex items-center justify-center rounded-full hover:bg-dunhuang-yellow/20 text-dunhuang-text/40 hover:text-dunhuang-red transition-colors"
          >
            <svg
              class="w-5 h-5"
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

        <!-- 内容区 -->
        <div
          class="grid grid-cols-1 md:grid-cols-2 gap-0 overflow-hidden flex-1"
        >
          <!-- 左侧：单据详情 -->
          <div class="flex flex-col p-8 md:border-r border-dunhuang-yellow/20">
            <h4
              class="text-base font-serif text-dunhuang-blue font-bold mb-5 flex items-center gap-2"
            >
              <svg
                class="w-4 h-4 text-dunhuang-red"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              基本信息
            </h4>

            <div class="flex flex-col flex-1 justify-start space-y-1">
              <div
                class="flex justify-between items-center py-2.5 border-b border-dunhuang-yellow/10"
              >
                <span class="text-dunhuang-text/50 text-sm">品种</span>
                <span class="font-medium text-dunhuang-blue text-sm">{{
                  getSpeciesName(viewingBill?.species_id)
                }}</span>
              </div>
              <div
                class="flex justify-between items-center py-2.5 border-b border-dunhuang-yellow/10"
              >
                <span class="text-dunhuang-text/50 text-sm">重量（公斤）</span>
                <span class="font-medium text-sm">{{
                  formatMoney(viewingBill?.weight)
                }}</span>
              </div>
              <div
                class="flex justify-between items-center py-2.5 border-b border-dunhuang-yellow/10"
              >
                <span class="text-dunhuang-text/50 text-sm">单价（元）</span>
                <span class="tabular-nums text-dunhuang-red text-sm">{{
                  formatMoney(viewingBill?.unit_price)
                }}</span>
              </div>

              <!-- 小计——加背景强调 -->
              <div
                class="flex justify-between items-center py-2.5 border-b border-dunhuang-yellow/10 bg-dunhuang-yellow/5 -mx-2 px-2 rounded"
              >
                <span class="text-dunhuang-text/50 text-sm">小计（元）</span>
                <span class="tabular-nums text-dunhuang-green text-sm">{{
                  formatMoney(viewingBill?.subtotal)
                }}</span>
              </div>
              <div
                class="flex justify-between items-center py-2.5 border-b border-dunhuang-yellow/10"
              >
                <span class="text-dunhuang-text/50 text-sm">服务费（元）</span>
                <span class="tabular-nums text-dunhuang-text/70 text-sm">{{
                  viewingBill ? formatFee(viewingBill) : ""
                }}</span>
              </div>

              <!-- 实付金额——加背景强调 -->
              <div
                class="flex justify-between items-center py-3 bg-dunhuang-red/5 -mx-2 px-2 rounded-lg border border-dunhuang-red/10"
              >
                <span class="text-dunhuang-text/70 text-sm font-medium"
                  >实付金额（元）</span
                >
                <span
                  class="tabular-nums font-bold text-dunhuang-red text-base"
                  >{{ formatMoney(viewingBill?.total_amount) }}</span
                >
              </div>

              <div class="flex justify-between items-center pt-4 mt-auto">
                <span class="text-dunhuang-text/40 text-xs">放生日期</span>
                <span class="text-xs text-dunhuang-blue font-medium">{{
                  dateStr(
                    viewingBill?.release_date || viewingBill?.created_at,
                  ) || "-"
                }}</span>
              </div>

              <div class="flex justify-between items-center pt-4 mt-auto">
                <span class="text-dunhuang-text/40 text-xs">记录添加时间</span>
                <span class="text-xs text-dunhuang-text/50">{{
                  dateTimeStr(viewingBill?.created_at)
                }}</span>
              </div>
            </div>
          </div>

          <!-- 右侧：操作记录 -->
          <div class="flex flex-col p-8 overflow-hidden min-h-0">
            <h4
              class="text-base font-serif text-dunhuang-blue font-bold mb-5 flex items-center gap-2"
            >
              <svg
                class="w-4 h-4 text-dunhuang-blue"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              操作记录
            </h4>
            <div class="overflow-y-auto custom-scrollbar pr-2 max-h-[340px]">
              <div v-if="filteredViewingBillLogs.length > 0" class="space-y-3">
                <div
                  v-for="log in filteredViewingBillLogs"
                  :key="log.id"
                  class="bg-dunhuang-bg/50 rounded-lg px-4 py-3 text-sm border border-dunhuang-yellow/10 hover:border-dunhuang-yellow/30 transition-colors"
                >
                  <div class="flex justify-between items-center mb-2">
                    <span
                      :class="[
                        'px-2.5 py-0.5 rounded-full text-xs font-medium',
                        log.action === 'CREATE'
                          ? 'bg-dunhuang-green/10 text-dunhuang-green'
                          : log.action === 'UPDATE' ||
                              log.action === 'COMPLETED'
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
                    class="text-dunhuang-text/80 text-xs space-y-1.5"
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
                    创建了该单据
                  </div>
                  <div
                    v-else-if="log.action === 'COMPLETED'"
                    class="text-dunhuang-text/50 text-xs"
                  >
                    单据已从最新单据归档至历史单据
                  </div>
                </div>
              </div>
              <div
                v-else
                class="text-dunhuang-text/40 text-center py-12 text-sm"
              >
                <svg
                  class="w-12 h-12 mx-auto mb-3 opacity-30"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="1.5"
                    d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
                  />
                </svg>
                暂无操作记录
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
    <ConfirmDialog
      :show="deleteConfirm.show"
      @cancel="deleteConfirm.show = false"
      @confirm="executeDeleteBill"
    >
      <template v-if="!deleteConfirm.isBatch">
        即将删除单号为 #{{
          String(deleteConfirm.id).padStart(5, "0")
        }}
        的单据。<br />此操作不可撤销，确定要删除吗？
      </template>
      <template v-else>
        即将删除选中的
        {{ selectedBillIds.length }}
        条记录。<br />此操作不可撤销，确定要批量删除吗？
      </template>
    </ConfirmDialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { dateStr, dateTimeStr, formatMoney } from "../lib/utils";
import ConfirmDialog from "../components/ConfirmDialog.vue";
import DateInput from "../components/DateInput.vue";
import { useSpecies } from "../composables/useSpecies";
import { useBillForm } from "../composables/useBillForm";
import { useBillTable } from "../composables/useBillTable";
import { useBillAudit } from "../composables/useBillAudit";

const { t } = useI18n();
const router = useRouter();

const showDatePicker = ref(false);

const now = new Date();
const currentYearMonth = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
const pickerFromMonth = ref(currentYearMonth);
const pickerToMonth = ref(currentYearMonth);

const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
const lastMonthStr = `${lastMonth.getFullYear()}-${String(lastMonth.getMonth() + 1).padStart(2, "0")}`;

const threeMonthsAgo = new Date(now.getFullYear(), now.getMonth() - 2, 1);
const threeMonthsAgoStr = `${threeMonthsAgo.getFullYear()}-${String(threeMonthsAgo.getMonth() + 1).padStart(2, "0")}`;

const datePresets = [
  { label: "本月", from: currentYearMonth, to: currentYearMonth },
  { label: "上月", from: lastMonthStr, to: lastMonthStr },
  { label: "近三个月", from: threeMonthsAgoStr, to: currentYearMonth },
  {
    label: "本年",
    from: `${now.getFullYear()}-01`,
    to: `${now.getFullYear()}-12`,
  },
];

const isPresetActive = (preset: { from: string; to: string }) => {
  return (
    pickerFromMonth.value === preset.from && pickerToMonth.value === preset.to
  );
};

const applyDatePreset = (preset: { from: string; to: string }) => {
  pickerFromMonth.value = preset.from;
  pickerToMonth.value = preset.to;
};

const openDatePicker = () => {
  if (filterDateFrom.value) {
    const parts = filterDateFrom.value.split("-");
    if (parts.length >= 2) pickerFromMonth.value = `${parts[0]}-${parts[1]}`;
  }
  if (filterDateTo.value) {
    const parts = filterDateTo.value.split("-");
    if (parts.length >= 2) pickerToMonth.value = `${parts[0]}-${parts[1]}`;
  }
};

const dateApply = () => {
  showDatePicker.value = false;
  if (pickerFromMonth.value) {
    filterDateFrom.value = `${pickerFromMonth.value}-01`;
  }
  if (pickerToMonth.value) {
    const [y, m] = pickerToMonth.value.split("-").map(Number);
    const lastDay = new Date(y, m, 0).getDate();
    filterDateTo.value = `${pickerToMonth.value}-${String(lastDay).padStart(2, "0")}`;
  }
  fetchBills();
};

const cancelDatePicker = () => {
  showDatePicker.value = false;
};

const toggleShowDatePicker = () => {
  if (showDatePicker.value) {
    showDatePicker.value = false;
  } else {
    openDatePicker();
    showDatePicker.value = true;
  }
};

const tabs = [
  { key: "current", label: "最新单据" },
  { key: "history", label: "历史单据" },
];

const { speciesList, fetchSpecies } = useSpecies();

const {
  showForm,
  saving,
  bill,
  billEntries,
  isEntrySelected,
  toggleEntry,
  removeEntry,
  getEntrySpecies,
  getEntryName,
  getEntryUnit,
  editingSpecies,
  initNewBill,
  batchSubtotal,
  batchFee,
  batchTotal,
  editSubtotal,
  editFee,
  editTotal,
  goBackToList,
  saveBill,
  editBill,
} = useBillForm(speciesList);

const {
  activeTab,
  filterDateFrom,
  filterDateTo,
  dateRangeLabel,
  billingSearch,
  bills,
  selectedBillIds,
  deleteConfirm,
  currentPage,
  pageSize,
  totalItems,
  totalPages,
  paginatedBills,
  tableSumWeight,
  tableSumSubtotal,
  tableSumFee,
  tableSumTotal,
  displayedPages,
  isAllSelected,
  toggleSelectAll,
  getSpeciesName,
  formatFee,
  fetchBills,
  switchTab,
  clearDateFilter,
  exportBills,
  confirmDeleteBill,
  confirmBatchDeleteBills,
  executeDeleteBill,
  upsertBill,
} = useBillTable(speciesList);

const searchText = ref("");

const performSearch = () => {
  billingSearch.value = searchText.value;
};

const clearSearchText = () => {
  searchText.value = "";
  billingSearch.value = "";
};

const {
  showViewModal,
  viewingBill,
  filteredViewingBillLogs,
  viewBill,
  formatAction,
  formatUpdateDiff,
} = useBillAudit(speciesList);

const goToImport = () => {
  router.push("/import");
};

const handleSaveBill = async () => {
  const prevTab = activeTab.value;
  await saveBill(upsertBill);
  if (prevTab !== "current") {
    activeTab.value = "current";
    fetchBills();
  }
};

onMounted(() => {
  fetchSpecies();
  fetchBills();
});
</script>

<style scoped>
.dropdown-enter-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}
.dropdown-leave-active {
  transition:
    opacity 0.15s ease,
    transform 0.15s ease;
}
.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-6px) scale(0.96);
}
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px) scale(0.97);
}
.col-th {
  @apply px-4 py-2 border-b border-dunhuang-yellow/40 whitespace-nowrap;
}
.col-td {
  @apply px-4 py-2 whitespace-nowrap;
}
.col-td-mono-red {
  @apply px-4 py-2 tabular-nums text-dunhuang-red whitespace-nowrap;
}
.col-td-green {
  @apply px-4 py-2 tabular-nums text-dunhuang-green whitespace-nowrap;
}
.col-td-muted {
  @apply px-4 py-2 text-dunhuang-text/80 whitespace-nowrap;
}
.col-td-time {
  @apply px-4 py-2 text-dunhuang-text/70 whitespace-nowrap;
}
</style>
