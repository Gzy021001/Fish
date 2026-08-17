<template>
  <div class="h-full flex flex-col space-y-6">
    <Transition name="switch-fade" mode="out-in">
      <div
        v-if="showForm"
        class="bg-white rounded-2xl shadow-md border border-dunhuang-yellow/30 flex-1 min-h-0 flex flex-col"
      >
        <div
          class="shrink-0 flex items-center justify-between mb-2 border-b-2 border-dunhuang-yellow/30 pb-2 px-6 pt-6"
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

        <form
          @submit.prevent="handleSaveBill"
          class="flex-1 min-h-0 flex flex-col"
        >
          <div
            class="flex-1 min-h-0 px-6 pt-2 pb-4 flex flex-col overflow-hidden"
          >
            <!-- 编辑模式 -->
            <template v-if="bill.id">
              <div
                v-if="editingSpecies"
                class="rounded-2xl bg-gradient-to-br from-dunhuang-red/[0.06] to-dunhuang-bg p-4 flex items-stretch gap-4 shadow-md ring-1 ring-dunhuang-red/10"
              >
                <div
                  class="shrink-0 w-24 h-24 rounded-2xl overflow-hidden shadow-md ring-1 ring-dunhuang-yellow/20"
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

              <div
                class="grid grid-cols-1 md:grid-cols-2 gap-x-5 gap-y-5 my-auto"
              >
                <div>
                  <label
                    class="block text-sm font-medium text-dunhuang-text mb-2"
                    >{{ t("billing.unit_price") }}（元/公斤）</label
                  >
                  <input
                    type="text"
                    :value="(+bill.unit_price || 0).toFixed(2)"
                    disabled
                    class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2.5 px-3 text-sm focus:ring-0 outline-none font-mono text-dunhuang-red disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                </div>
                <div>
                  <label
                    class="block text-sm font-medium text-dunhuang-text mb-2"
                    >重量 ({{ editingSpecies?.default_unit ?? "公斤" }})</label
                  >
                  <input
                    type="text"
                    inputmode="decimal"
                    v-model="bill.weight"
                    @blur="bill.weight = (+bill.weight || 0).toFixed(2)"
                    required
                    class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2.5 px-3 text-sm focus:ring-0 outline-none font-mono"
                  />
                </div>
                <div class="hidden">
                  <select v-model="bill.fee_type" class="hidden">
                    <option value="FIXED">固定金额</option>
                  </select>
                </div>
                <div>
                  <label
                    class="block text-sm font-medium text-dunhuang-text mb-2"
                    >服务费（元）</label
                  >
                  <input
                    type="text"
                    inputmode="decimal"
                    v-model="bill.fee_value"
                    @blur="bill.fee_value = (+bill.fee_value || 0).toFixed(2)"
                    required
                    class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2.5 px-3 text-sm focus:ring-0 outline-none font-mono"
                  />
                </div>
                <div>
                  <label
                    class="block text-sm font-medium text-dunhuang-text mb-2"
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
              <div class="space-y-3 flex-1 min-h-0 flex flex-col">
                <!-- 品种选择 + 放生日期 同行 -->
                <div class="shrink-0 flex items-start gap-5">
                  <div class="flex-1 min-w-0">
                    <label
                      class="block text-sm font-medium text-dunhuang-text mb-2"
                      >{{ t("billing.species_name") }}</label
                    >
                    <div
                      class="relative rounded-xl bg-dunhuang-bg/30 border border-dunhuang-yellow/20"
                    >
                      <div
                        class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2.5 overflow-y-auto custom-scrollbar max-h-[118px] p-2"
                      >
                        <div
                          v-for="sp in speciesList"
                          :key="sp.id"
                          @click="toggleEntry(sp)"
                          :class="[
                            'cursor-pointer relative overflow-hidden rounded-xl border-2 p-2.5 transition-all duration-200 flex flex-col items-center justify-center gap-1 group',
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
                            class="w-14 h-10 rounded-lg object-cover border-2 border-dunhuang-yellow/30 shadow-sm"
                          />
                          <div
                            v-else
                            class="w-14 h-10 rounded-lg bg-dunhuang-yellow/10 border-2 border-dunhuang-yellow/30 flex items-center justify-center text-dunhuang-blue shadow-sm"
                          >
                            <span class="text-base font-bold">{{
                              sp.name_zh ? sp.name_zh.charAt(0) : "?"
                            }}</span>
                          </div>
                          <div class="text-center">
                            <h4 class="font-medium text-dunhuang-blue text-sm">
                              {{ sp.name_zh }}
                            </h4>
                            <div class="text-xs text-dunhuang-text/50 mt-0.5">
                              {{ formatMoney(sp.default_price) }}（元/公斤）
                            </div>
                          </div>
                        </div>
                      </div>
                      <div
                        class="pointer-events-none absolute left-0 right-0 bottom-0 h-6 bg-gradient-to-t from-dunhuang-bg/30 to-transparent rounded-b-xl"
                      ></div>
                    </div>
                  </div>
                  <div class="w-[220px] shrink-0">
                    <label
                      class="block text-sm font-medium text-dunhuang-text mb-2"
                      >放生日期</label
                    >
                    <DateInput
                      v-model="bill.release_date"
                      placeholder="选择放生日期"
                    />
                  </div>
                </div>

                <!-- 已选品种编辑区 -->
                <div
                  v-if="billEntries.length > 0"
                  class="flex-1 min-h-0 flex flex-col space-y-2"
                >
                  <div class="shrink-0 flex items-center justify-between">
                    <span class="text-sm font-medium text-dunhuang-text"
                      >已选
                      <span class="text-dunhuang-blue font-bold">{{
                        billEntries.length
                      }}</span>
                      个品种</span
                    >
                  </div>
                  <div
                    class="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-2 overflow-y-auto pr-2 custom-scrollbar content-start"
                  >
                    <div
                      v-for="(entry, idx) in billEntries"
                      :key="entry.species_id"
                      class="rounded-xl border border-dunhuang-yellow/30 bg-white p-2 transition-shadow hover:shadow-md hover:border-dunhuang-yellow/50 relative group flex flex-col"
                    >
                      <div
                        class="flex items-center gap-2 mb-1.5 border-b border-dunhuang-yellow/10 pb-1.5"
                      >
                        <img
                          v-if="getEntrySpecies(entry.species_id)?.image_url"
                          :src="getEntrySpecies(entry.species_id)!.image_url!"
                          :alt="getEntryName(entry.species_id)"
                          class="w-9 h-9 rounded-lg object-cover border border-dunhuang-yellow/30 shrink-0 shadow-sm"
                        />
                        <div
                          v-else
                          class="w-9 h-9 rounded-lg bg-dunhuang-yellow/10 border border-dunhuang-yellow/30 flex items-center justify-center text-dunhuang-blue shrink-0 shadow-sm"
                        >
                          <span class="text-xs font-bold">{{
                            getEntryName(entry.species_id).charAt(0)
                          }}</span>
                        </div>
                        <div
                          class="flex-1 min-w-0 flex flex-col justify-center"
                        >
                          <span
                            class="font-medium text-dunhuang-blue text-sm truncate leading-tight"
                            >{{ getEntryName(entry.species_id) }}</span
                          >
                          <span
                            class="text-[10px] text-dunhuang-text/50 font-medium mt-0.5"
                          >
                            <span class="text-dunhuang-red font-mono">{{
                              (
                                getEntrySpecies(entry.species_id)
                                  ?.default_price ??
                                entry.unit_price ??
                                0
                              ).toFixed(2)
                            }}</span>
                            元/公斤
                          </span>
                        </div>
                        <button
                          type="button"
                          @click="removeEntry(idx)"
                          class="absolute top-1.5 right-1.5 text-dunhuang-text/20 hover:text-dunhuang-red transition-all duration-200 w-5 h-5 flex items-center justify-center rounded-full hover:bg-dunhuang-red/10 shrink-0 opacity-0 group-hover:opacity-100"
                          title="移除此品种"
                        >
                          <svg
                            class="w-3 h-3"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              stroke-width="2.5"
                              d="M6 18L18 6M6 6l12 12"
                            />
                          </svg>
                        </button>
                      </div>
                      <div class="grid grid-cols-2 gap-2 mt-0">
                        <div>
                          <label
                            class="block text-[10px] font-medium text-dunhuang-text/60 mb-1"
                            >总重 ({{
                              getEntryUnit(entry.species_id) || "公斤"
                            }})</label
                          >
                          <div class="relative">
                            <input
                              type="text"
                              inputmode="decimal"
                              v-model="entry.weight"
                              @blur="
                                entry.weight = (+entry.weight || 0).toFixed(2)
                              "
                              class="w-full bg-dunhuang-bg/50 border border-dunhuang-yellow/40 rounded-md px-2 py-1 text-xs focus:ring-0 outline-none font-mono text-dunhuang-blue font-medium transition-colors focus:bg-white focus:border-dunhuang-blue/50 hover:border-dunhuang-yellow/60"
                            />
                          </div>
                        </div>
                        <div>
                          <label
                            class="block text-[10px] font-medium text-dunhuang-text/60 mb-1"
                            >服务费（元）</label
                          >
                          <div class="relative">
                            <input
                              type="text"
                              inputmode="decimal"
                              v-model="entry.fee_value"
                              @blur="
                                entry.fee_value = (
                                  +entry.fee_value || 0
                                ).toFixed(2)
                              "
                              class="w-full bg-dunhuang-bg/50 border border-dunhuang-yellow/40 rounded-md px-2 py-1 text-xs focus:ring-0 outline-none font-mono text-dunhuang-blue font-medium transition-colors focus:bg-white focus:border-dunhuang-blue/50 hover:border-dunhuang-yellow/60"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div
                  v-else
                  class="flex-1 flex items-center justify-center text-sm text-dunhuang-text/40"
                >
                  点击上方品种卡片开始添加
                </div>
              </div>
            </template>
          </div>

          <!-- 底部汇总 + 保存 -->
          <div
            class="shrink-0 flex items-end justify-between gap-4 px-6 pb-5 pt-3 border-t border-dunhuang-yellow/10"
          >
            <div class="flex items-end gap-4">
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

              <!-- 新增模式汇总 -->
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
            </div>

            <div class="flex justify-end shrink-0">
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
          <div class="flex items-center gap-4">
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

            <!-- 筛选面板 -->
            <div class="relative self-center mb-2" ref="filterWrapperRef">
              <button
                @click="
                  showFilterDropdown
                    ? (showFilterDropdown = false)
                    : openFilterDropdown()
                "
                :class="[
                  'flex items-center justify-center gap-1.5 rounded-lg px-3.5 h-7 text-[13px] font-semibold transition-all duration-200',
                  activeFilterCount > 0
                    ? 'bg-dunhuang-yellow/15 text-dunhuang-blue border border-dunhuang-yellow/40 shadow-sm'
                    : 'bg-dunhuang-bg/50 text-dunhuang-text/40 border border-dunhuang-blue/15 hover:text-dunhuang-text/60 hover:border-dunhuang-blue/35 hover:bg-white',
                ]"
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
                    d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                  />
                </svg>
                <span>筛选</span>
                <span
                  v-if="activeFilterCount > 0"
                  class="ml-1 flex items-center justify-center w-4 h-4 text-[10px] font-bold text-white bg-dunhuang-red rounded-full leading-none pt-[1px]"
                >
                  {{ activeFilterCount }}
                </span>
              </button>

              <Transition name="dropdown">
                <div
                  v-if="showFilterDropdown"
                  class="absolute top-full mt-2 left-0 z-50"
                >
                  <div
                    class="bg-white rounded-2xl shadow-xl border border-dunhuang-yellow/20 w-[320px]"
                    style="
                      box-shadow:
                        0 12px 36px rgba(92, 64, 51, 0.12),
                        0 4px 12px rgba(92, 64, 51, 0.06);
                    "
                  >
                    <div
                      class="flex items-center gap-2.5 px-5 pt-4 pb-3 border-b border-dunhuang-yellow/10"
                    >
                      <div
                        class="w-1 h-5 rounded-full bg-dunhuang-yellow shrink-0"
                      ></div>
                      <h4
                        class="text-sm font-serif font-bold text-dunhuang-blue"
                      >
                        筛选
                      </h4>
                    </div>

                    <div class="px-5 py-4 space-y-4">
                      <!-- 品种搜索 -->
                      <div>
                        <label
                          class="block text-[11px] text-dunhuang-text/40 mb-1.5 tracking-wider font-medium"
                          >搜索品种</label
                        >
                        <div
                          class="flex items-center bg-dunhuang-bg/30 border border-dunhuang-yellow/30 rounded-lg px-2.5 h-9 focus-within:border-dunhuang-blue focus-within:bg-white transition-all duration-200"
                        >
                          <svg
                            class="w-3.5 h-3.5 text-dunhuang-blue/40 shrink-0"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                          </svg>
                          <input
                            type="text"
                            v-model="pickerSearchText"
                            placeholder="输入品种名称..."
                            class="flex-1 w-full bg-transparent border-none text-sm text-dunhuang-blue font-medium focus:outline-none focus:ring-0 px-2 placeholder:text-dunhuang-text/30"
                            @keydown.enter="applyFilters"
                          />
                        </div>
                      </div>

                      <!-- 日期范围 -->
                      <div>
                        <label
                          class="block text-[11px] text-dunhuang-text/40 mb-1.5 tracking-wider font-medium"
                          >放生日期范围</label
                        >
                        <div
                          class="flex items-center gap-1.5 border border-dunhuang-yellow/30 rounded-lg bg-dunhuang-bg/30 px-2 h-9 w-full hover:border-dunhuang-yellow/50 focus-within:border-dunhuang-blue focus-within:bg-white transition-all duration-200"
                        >
                          <DateInput
                            v-model="pickerFromDate"
                            placeholder="开始日期"
                            size="sm"
                            variant="ghost"
                            class="flex-1 min-w-0"
                          />
                          <span
                            class="text-dunhuang-text/30 text-xs font-medium shrink-0 px-0.5"
                            >至</span
                          >
                          <DateInput
                            v-model="pickerToDate"
                            placeholder="结束日期"
                            size="sm"
                            variant="ghost"
                            class="flex-1 min-w-0"
                          />
                        </div>
                      </div>
                      <!-- 归档状态 (仅在最新单据下显示) -->
                      <div v-if="activeTab === 'current'">
                        <label
                          class="block text-[11px] text-dunhuang-text/40 mb-1.5 tracking-wider font-medium"
                          >单据状态</label
                        >
                        <div class="flex gap-2">
                          <button
                            @click="pickerStatus = ''"
                            :class="[
                              'flex-1 h-8 rounded-lg text-xs font-medium transition-all duration-200 border',
                              pickerStatus === ''
                                ? 'bg-dunhuang-blue text-white border-dunhuang-blue'
                                : 'bg-dunhuang-bg/30 text-dunhuang-text/60 border-dunhuang-yellow/30 hover:border-dunhuang-blue/50',
                            ]"
                          >
                            全部
                          </button>
                          <button
                            @click="pickerStatus = 'DRAFT'"
                            :class="[
                              'flex-1 h-8 rounded-lg text-xs font-medium transition-all duration-200 border',
                              pickerStatus === 'DRAFT'
                                ? 'bg-dunhuang-blue text-white border-dunhuang-blue'
                                : 'bg-dunhuang-bg/30 text-dunhuang-text/60 border-dunhuang-yellow/30 hover:border-dunhuang-blue/50',
                            ]"
                          >
                            草稿
                          </button>
                          <button
                            @click="pickerStatus = 'COMPLETED'"
                            :class="[
                              'flex-1 h-8 rounded-lg text-xs font-medium transition-all duration-200 border',
                              pickerStatus === 'COMPLETED'
                                ? 'bg-dunhuang-blue text-white border-dunhuang-blue'
                                : 'bg-dunhuang-bg/30 text-dunhuang-text/60 border-dunhuang-yellow/30 hover:border-dunhuang-blue/50',
                            ]"
                          >
                            已归档
                          </button>
                        </div>
                      </div>
                    </div>

                    <!-- 操作按钮 -->
                    <div
                      class="flex justify-end items-center px-5 py-3 bg-dunhuang-bg/40 border-t border-dunhuang-yellow/10 rounded-b-2xl"
                    >
                      <div class="flex gap-2">
                        <button
                          @click="applyFilters"
                          class="px-5 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 bg-dunhuang-blue text-white hover:bg-dunhuang-blue/90 shadow-sm hover:shadow-md"
                        >
                          搜索
                        </button>
                        <button
                          @click="resetFilters"
                          class="px-4 py-1.5 rounded-lg text-xs text-dunhuang-text/50 hover:text-dunhuang-text/70 hover:bg-dunhuang-yellow/20 transition-colors font-medium"
                        >
                          重置
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </Transition>
            </div>
          </div>

          <div class="flex gap-2 items-center">
            <!-- 批量删除 -->
            <button
              v-if="activeTab === 'current' && selectedBillIds.length > 0"
              @click="confirmBatchDeleteBills"
              class="h-8 px-3.5 rounded-lg text-sm font-medium transition-all duration-200 text-dunhuang-red hover:bg-dunhuang-red/8 border border-dunhuang-red/25 hover:border-dunhuang-red/40"
            >
              批量删除 ({{ selectedBillIds.length }})
            </button>

            <!-- 批量归档 -->
            <button
              v-if="
                activeTab === 'current' &&
                selectedBillIds.length > 0 &&
                authStore.isAdmin
              "
              @click="confirmArchiveBills"
              class="h-8 px-3.5 rounded-lg text-sm font-medium transition-all duration-200 text-dunhuang-green hover:bg-dunhuang-green/8 border border-dunhuang-green/25 hover:border-dunhuang-green/40"
            >
              核对无误并归档 ({{ selectedBillIds.length }})
            </button>

            <!-- current tab 专有按钮：导入 -->
            <button
              v-if="activeTab === 'current' && authStore.isAdmin"
              @click="goToImport"
              type="button"
              class="h-8 px-3.5 rounded-lg text-sm font-medium transition-all duration-200 text-dunhuang-blue/80 hover:text-dunhuang-blue hover:bg-dunhuang-blue/6 border border-dunhuang-blue/15 hover:border-dunhuang-blue/35"
            >
              导入
            </button>

            <!-- 导出 -->
            <button
              @click="exportBills"
              type="button"
              class="h-8 px-3.5 rounded-lg text-sm font-medium transition-all duration-200 text-dunhuang-blue/80 hover:text-dunhuang-blue hover:bg-dunhuang-blue/6 border border-dunhuang-blue/15 hover:border-dunhuang-blue/35"
            >
              导出
            </button>

            <!-- current tab 专有按钮 -->
            <template v-if="activeTab === 'current'">
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
          class="border border-dunhuang-yellow/30 rounded-lg bg-white overflow-hidden flex flex-col h-[534px]"
        >
          <!-- Header (Synced Scroll) -->
          <div
            ref="tableHeaderRef"
            class="overflow-hidden shrink-0 bg-[#fbf6ec] z-40 transform-gpu shadow-sm"
          >
            <div class="flex min-w-[1100px] h-[42px]">
              <div
                class="bg-dunhuang-yellow/10 text-dunhuang-blue font-sans font-bold text-sm flex w-full h-full"
              >
                <div
                  v-if="activeTab === 'current'"
                  class="px-3 py-2 border-b border-dunhuang-yellow/40 flex items-center justify-center w-12 shrink-0 sticky left-0 bg-[#fbf6ec] z-50"
                >
                  <input
                    type="checkbox"
                    class="w-4 h-4 rounded border-2 border-dunhuang-yellow/40 text-dunhuang-blue focus:ring-0 focus:ring-offset-0 cursor-pointer transition-all duration-200"
                    :checked="isAllSelected"
                    @change="toggleSelectAll"
                  />
                </div>
                <div
                  class="col-th w-16 shrink-0 flex items-center z-50 bg-[#fbf6ec]"
                  :class="
                    activeTab === 'current'
                      ? 'sticky left-12'
                      : 'sticky left-0 pl-2'
                  "
                >
                  序号
                </div>
                <div
                  class="col-th w-28 shrink-0 flex items-center z-50 bg-[#fbf6ec] shadow-[2px_0_5px_-2px_rgba(0,0,0,0.05)]"
                  :class="
                    activeTab === 'current'
                      ? 'sticky left-[112px]'
                      : 'sticky left-16'
                  "
                >
                  品种
                </div>
                <div
                  class="col-th flex-[0.35] flex items-center justify-center"
                >
                  归档状态
                </div>
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
                <div class="col-th flex-[0.7] flex items-center">放生日期</div>
                <div class="col-th flex-[0.9] flex items-center">添加时间</div>
                <div
                  v-if="activeTab === 'current'"
                  class="col-th flex items-center justify-center w-40 shrink-0 sticky right-0 bg-[#fbf6ec] z-50 shadow-[-2px_0_5px_-2px_rgba(0,0,0,0.05)]"
                >
                  操作
                </div>
              </div>
            </div>
          </div>

          <!-- Body (Main Scroll Area) -->
          <div
            ref="tableBodyRef"
            @scroll="handleTableScroll"
            class="overflow-auto custom-scrollbar flex-1 w-full"
          >
            <div class="flex flex-col min-w-[1100px] relative min-h-[450px]">
              <div
                v-for="(b, index) in paginatedBills"
                :key="b.id"
                class="border-b border-dunhuang-yellow/20 hover:bg-[#fcf8f0] transition-colors text-sm group flex w-full shrink-0 h-[45px]"
              >
                <div
                  v-if="activeTab === 'current'"
                  class="px-3 py-2 flex items-center justify-center w-12 shrink-0 sticky left-0 bg-white group-hover:bg-[#fcf8f0] transition-colors z-30"
                >
                  <input
                    type="checkbox"
                    class="w-4 h-4 rounded border-2 border-dunhuang-yellow/40 text-dunhuang-blue focus:ring-0 focus:ring-offset-0 cursor-pointer transition-all duration-200"
                    :value="b.id"
                    v-model="selectedBillIds"
                  />
                </div>
                <div
                  class="col-td-muted w-16 shrink-0 flex items-center bg-white group-hover:bg-[#fcf8f0] transition-colors z-30"
                  :class="
                    activeTab === 'current'
                      ? 'sticky left-12'
                      : 'sticky left-0 pl-2'
                  "
                >
                  {{ (currentPage - 1) * pageSize + index + 1 }}
                </div>
                <div
                  class="col-td font-medium w-28 shrink-0 flex items-center truncate pr-2 bg-white group-hover:bg-[#fcf8f0] transition-colors z-30 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.05)]"
                  :class="
                    activeTab === 'current'
                      ? 'sticky left-[112px]'
                      : 'sticky left-16'
                  "
                >
                  {{ getSpeciesName(b.species_id) }}
                </div>
                <div
                  class="col-td flex-[0.35] flex items-center justify-center"
                >
                  <span
                    v-if="b.status === 'COMPLETED'"
                    class="text-[10px] px-1.5 py-0.5 rounded bg-dunhuang-blue/10 text-dunhuang-blue border border-dunhuang-blue/20 shrink-0"
                    >已归档</span
                  >
                  <span
                    v-else-if="b.status === 'DRAFT'"
                    class="text-[10px] px-1.5 py-0.5 rounded bg-dunhuang-yellow/20 text-dunhuang-orange border border-dunhuang-yellow/40 shrink-0"
                    >草稿</span
                  >
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
                  {{ dateStr(b.release_date || b.species?.release_date) }}
                </div>
                <div class="col-td-time flex-[0.9] flex items-center">
                  {{ dateTimeStr(b.created_at) }}
                </div>
                <div
                  v-if="activeTab === 'current'"
                  class="px-3 py-2 flex items-center justify-center w-40 shrink-0 sticky right-0 bg-white group-hover:bg-[#fcf8f0] transition-colors z-30 shadow-[-2px_0_5px_-2px_rgba(0,0,0,0.05)]"
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
                v-for="i in Math.max(0, pageSize - paginatedBills.length)"
                :key="'placeholder-' + i"
              >
                <div
                  class="border-b border-dunhuang-yellow/10 text-sm flex w-full shrink-0 h-[45px]"
                >
                  <div
                    v-if="activeTab === 'current'"
                    class="px-3 py-2 flex items-center justify-center w-12 shrink-0 sticky left-0 bg-white z-30"
                  ></div>
                  <div
                    class="col-td-muted w-16 shrink-0 flex items-center bg-white z-30"
                    :class="
                      activeTab === 'current'
                        ? 'sticky left-12'
                        : 'sticky left-0 pl-2'
                    "
                  ></div>
                  <div
                    class="col-td font-medium w-28 shrink-0 flex items-center bg-white z-30 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.05)]"
                    :class="
                      activeTab === 'current'
                        ? 'sticky left-[112px]'
                        : 'sticky left-16'
                    "
                  ></div>
                  <div
                    class="col-td flex-[0.35] flex items-center justify-center"
                  ></div>
                  <div
                    class="col-td tabular-nums flex-[0.5] flex items-center"
                  ></div>
                  <div
                    class="col-td-mono-red flex-[0.6] flex items-center"
                  ></div>
                  <div class="col-td-green flex-[0.6] flex items-center"></div>
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
                    class="px-3 py-2 flex items-center justify-center w-40 shrink-0 sticky right-0 bg-white z-30 shadow-[-2px_0_5px_-2px_rgba(0,0,0,0.05)]"
                  ></div>
                </div>
              </template>
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

          <!-- Footer (Synced Scroll) -->
          <div
            ref="tableFooterRef"
            class="overflow-hidden shrink-0 bg-white border-t-2 border-dunhuang-yellow/30 shadow-[0_-2px_5px_-2px_rgba(0,0,0,0.05)]"
          >
            <div class="flex min-w-[1100px] h-[42px]">
              <div
                v-if="activeTab === 'current'"
                class="w-12 shrink-0 sticky left-0 bg-white z-50"
              ></div>
              <div
                class="w-16 shrink-0 bg-white z-50"
                :class="
                  activeTab === 'current' ? 'sticky left-12' : 'sticky left-0'
                "
              ></div>
              <div
                class="w-28 shrink-0 flex items-center justify-end pr-4 text-xs text-dunhuang-text/60 bg-white z-50 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.05)]"
                :class="
                  activeTab === 'current'
                    ? 'sticky left-[112px]'
                    : 'sticky left-16'
                "
              >
                总计
              </div>
              <div class="px-4 py-2 flex-[0.35]"></div>
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
              <div class="px-4 py-2 flex-[0.7] flex items-center"></div>
              <div class="px-4 py-2 flex-[0.9] flex items-center"></div>
              <div
                v-if="activeTab === 'current'"
                class="px-3 py-2 w-40 shrink-0 sticky right-0 bg-white z-50 shadow-[-2px_0_5px_-2px_rgba(0,0,0,0.05)]"
              ></div>
            </div>
          </div>
        </div>

        <div
          class="flex justify-between items-center mt-4 shrink-0 relative z-30"
        >
          <div class="text-sm text-dunhuang-text/70">
            共
            <span class="font-bold text-dunhuang-blue">{{ totalItems }}</span>
            条
          </div>

          <Pagination
            v-model:currentPage="currentPage"
            v-model:pageSize="pageSize"
            :totalPages="totalPages"
            :showPageSizeSelect="true"
          />
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
            <div class="overflow-y-auto pr-2 max-h-[340px]">
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
        确定删除此条单据？<br />此操作不可撤销。
      </template>
      <template v-else>
        确定删除选中的
        {{ selectedBillIds.length }} 条单据？<br />此操作不可撤销。
      </template>
    </ConfirmDialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, computed } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { dateStr, dateTimeStr, formatMoney } from "../lib/utils";
import ConfirmDialog from "../components/ConfirmDialog.vue";
import DateInput from "../components/DateInput.vue";
import Pagination from "../components/Pagination.vue";
import { useSpecies } from "../composables/useSpecies";
import { useBillForm } from "../composables/useBillForm";
import { useBillTable } from "../composables/useBillTable";
import { useBillAudit } from "../composables/useBillAudit";

const { t } = useI18n();
const router = useRouter();
const authStore = useAuthStore();

const showFilterDropdown = ref(false);
const filterWrapperRef = ref<HTMLElement | null>(null);
const pickerSearchText = ref("");
const pickerStatus = ref("");

const tableHeaderRef = ref<HTMLElement | null>(null);
const tableBodyRef = ref<HTMLElement | null>(null);
const tableFooterRef = ref<HTMLElement | null>(null);

const handleTableScroll = (e: Event) => {
  const target = e.target as HTMLElement;
  if (tableHeaderRef.value) {
    tableHeaderRef.value.scrollLeft = target.scrollLeft;
  }
  if (tableFooterRef.value) {
    tableFooterRef.value.scrollLeft = target.scrollLeft;
  }
};

const handleFilterClickOutside = (e: MouseEvent) => {
  if (
    showFilterDropdown.value &&
    filterWrapperRef.value &&
    !filterWrapperRef.value.contains(e.target as Node)
  ) {
    showFilterDropdown.value = false;
  }
};

const pickerFromDate = ref("");
const pickerToDate = ref("");

const openFilterDropdown = () => {
  pickerFromDate.value = filterDateFrom.value;
  pickerToDate.value = filterDateTo.value;
  pickerSearchText.value = billingSearch.value;
  pickerStatus.value = filterStatus.value;
  showFilterDropdown.value = true;
};

const applyFilters = async () => {
  let from = pickerFromDate.value || "";
  let to = pickerToDate.value || "";
  if (from && to && from > to) {
    [from, to] = [to, from];
  }
  filterDateFrom.value = from;
  filterDateTo.value = to;

  billingSearch.value = pickerSearchText.value;
  searchText.value = pickerSearchText.value;
  filterStatus.value = pickerStatus.value;

  showFilterDropdown.value = false;
  await fetchBills();
};

const resetFilters = () => {
  pickerFromDate.value = "";
  pickerToDate.value = "";
  pickerSearchText.value = "";
  pickerStatus.value = "";
  filterDateFrom.value = "";
  filterDateTo.value = "";
  billingSearch.value = "";
  searchText.value = "";
  filterStatus.value = "";
  showFilterDropdown.value = false;
  fetchBills();
};

const activeFilterCount = computed(() => {
  let count = 0;
  if (filterDateFrom.value || filterDateTo.value) count++;
  if (billingSearch.value) count++;
  if (filterStatus.value) count++;
  return count;
});

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
  saveSingleBill,
  saveBatchBills,
  editBill,
} = useBillForm(speciesList);

const {
  activeTab,
  filterDateFrom,
  filterDateTo,
  filterStatus,
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
  isAllSelected,
  toggleSelectAll,
  getSpeciesName,
  formatFee,
  fetchBills,
  switchTab,
  clearDateFilter,
  exportBills,
  confirmArchiveBills,
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
  if (bill.value.id) {
    await saveSingleBill(upsertBill);
  } else {
    await saveBatchBills(upsertBill);
  }
  if (prevTab !== "current") {
    activeTab.value = "current";
    fetchBills();
  }
};

onMounted(() => {
  document.addEventListener("mousedown", handleFilterClickOutside);
  fetchSpecies();
  fetchBills();
});

onBeforeUnmount(() => {
  document.removeEventListener("mousedown", handleFilterClickOutside);
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
