<template>
  <div class="h-full flex flex-col space-y-6">
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

      <form @submit.prevent="saveBill" class="space-y-6 relative z-10">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- 品种 -->
          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-dunhuang-text mb-3">{{
              t("billing.species_name")
            }}</label>
            <template v-if="bill.id">
              <div
                v-if="editingSpecies"
                class="rounded-xl border-2 border-dunhuang-red bg-dunhuang-red/5 p-4 flex items-center gap-4"
              >
                <img
                  v-if="editingSpecies.image_url"
                  :src="editingSpecies.image_url"
                  :alt="editingSpecies.name_zh"
                  class="w-16 h-16 rounded-full object-cover border-2 border-dunhuang-yellow/30 shadow-sm"
                />
                <div
                  v-else
                  class="w-16 h-16 rounded-full bg-dunhuang-yellow/10 border-2 border-dunhuang-yellow/30 flex items-center justify-center text-dunhuang-blue shadow-sm"
                >
                  <span class="text-xl font-bold">{{
                    editingSpecies.name_zh
                      ? editingSpecies.name_zh.charAt(0)
                      : "?"
                  }}</span>
                </div>
                <div>
                  <h4 class="font-medium text-dunhuang-blue text-lg">
                    {{ editingSpecies.name_zh }}
                  </h4>
                  <div class="text-xs text-dunhuang-text/60 mt-1 font-mono">
                    默认: ¥{{
                      (editingSpecies.default_price || 0).toFixed(2)
                    }}/{{ editingSpecies.default_unit }}
                  </div>
                </div>
              </div>
              <div v-else class="text-sm text-dunhuang-text/50">未找到品种</div>
            </template>
            <template v-else>
              <div
                class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4"
              >
                <div
                  v-for="sp in speciesList"
                  :key="sp.id"
                  @click="
                    bill.species_id = sp.id;
                    handleSpeciesChange();
                  "
                  :class="[
                    'cursor-pointer relative overflow-hidden rounded-xl border-2 p-4 transition-all duration-300 flex flex-col items-center justify-center gap-2 group',
                    bill.species_id === sp.id
                      ? 'border-dunhuang-red bg-dunhuang-red/5 shadow-[0_4px_20px_rgb(187,49,52,0.15)] scale-[1.02]'
                      : 'border-dunhuang-yellow/40 bg-white hover:border-dunhuang-orange hover:shadow-md',
                  ]"
                >
                  <!-- Active Indicator -->
                  <div
                    v-if="bill.species_id === sp.id"
                    class="absolute top-0 right-0 w-8 h-8 bg-dunhuang-red flex items-start justify-end p-1 rounded-bl-xl"
                  >
                    <svg
                      class="w-4 h-4 text-white"
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
                    class="w-16 h-16 rounded-full object-cover border-2 border-dunhuang-yellow/30 shadow-sm"
                  />
                  <div
                    v-else
                    class="w-16 h-16 rounded-full bg-dunhuang-yellow/10 border-2 border-dunhuang-yellow/30 flex items-center justify-center text-dunhuang-blue shadow-sm"
                  >
                    <span class="text-xl font-bold">{{
                      sp.name_zh ? sp.name_zh.charAt(0) : "?"
                    }}</span>
                  </div>

                  <div class="text-center">
                    <h4 class="font-medium text-dunhuang-blue">
                      {{ sp.name_zh }}
                    </h4>
                    <div class="text-xs text-dunhuang-text/60 mt-1 font-mono">
                      默认: ¥{{ (sp.default_price || 0).toFixed(2) }}/{{
                        sp.default_unit
                      }}
                    </div>
                  </div>
                </div>
              </div>
              <!-- Hidden required select for form validation -->
              <select v-model="bill.species_id" required class="hidden">
                <option
                  v-for="sp in speciesList"
                  :key="sp.id"
                  :value="sp.id"
                ></option>
              </select>
            </template>
          </div>

          <!-- 单价 -->
          <div>
            <label class="block text-sm font-medium text-dunhuang-text mb-2"
              >{{ t("billing.unit_price") }} (¥)</label
            >
            <div class="relative">
              <button
                type="button"
                @click="adjustPrice(-0.01)"
                class="absolute left-0 top-0 bottom-0 px-4 bg-dunhuang-yellow/20 hover:bg-dunhuang-yellow/40 rounded-l-lg border-r border-dunhuang-yellow/50 text-dunhuang-blue transition-colors flex items-center justify-center"
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
                    d="M20 12H4"
                  />
                </svg>
              </button>
              <input
                type="number"
                step="0.01"
                min="0"
                v-model.number="bill.unit_price"
                @blur="formatPriceInput"
                required
                class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-3 px-12 text-center focus:ring-2 focus:ring-dunhuang-red outline-none font-mono text-lg [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
              />
              <button
                type="button"
                @click="adjustPrice(0.01)"
                class="absolute right-0 top-0 bottom-0 px-4 bg-dunhuang-yellow/20 hover:bg-dunhuang-yellow/40 rounded-r-lg border-l border-dunhuang-yellow/50 text-dunhuang-blue transition-colors flex items-center justify-center"
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
                    d="M12 4v16m8-8H4"
                  />
                </svg>
              </button>
            </div>
          </div>

          <!-- 重量 -->
          <div>
            <label class="block text-sm font-medium text-dunhuang-text mb-2"
              >{{ t("billing.weight") }} ({{ currentUnit }})</label
            >
            <input
              type="number"
              step="0.01"
              min="0"
              v-model.number="bill.weight"
              @blur="formatWeightInput"
              required
              class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg p-3 focus:ring-2 focus:ring-dunhuang-red outline-none [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
            />
          </div>

          <!-- 服务费类型 -->
          <div class="hidden">
            <label class="block text-sm font-medium text-dunhuang-text mb-2">{{
              t("billing.fee_type")
            }}</label>
            <select
              v-model="bill.fee_type"
              required
              class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg p-3 focus:ring-2 focus:ring-dunhuang-red outline-none"
            >
              <option value="PERCENTAGE">{{ t("billing.percentage") }}</option>
              <option value="FIXED">{{ t("billing.fixed") }}</option>
            </select>
          </div>

          <!-- 服务费数值 -->
          <div>
            <label class="block text-sm font-medium text-dunhuang-text mb-2"
              >服务费 (¥)</label
            >
            <input
              type="number"
              step="0.01"
              min="0"
              v-model.number="bill.fee_value"
              @blur="formatFeeInput"
              required
              class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg p-3 focus:ring-2 focus:ring-dunhuang-red outline-none [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
            />
          </div>
        </div>

        <!-- 汇总区域 -->
        <div
          class="mt-8 flex flex-col md:flex-row items-end justify-between gap-6"
        >
          <div class="space-y-2 text-dunhuang-text">
            <p class="flex justify-between w-48">
              <span>{{ t("billing.subtotal") }}:</span>
              <span class="font-mono">¥ {{ subtotal.toFixed(2) }}</span>
            </p>
            <p
              class="flex justify-between w-48 text-sm text-dunhuang-text/70 border-b border-dunhuang-yellow/30 pb-2"
            >
              <span>服务费:</span>
              <span class="font-mono">+ ¥ {{ fee.toFixed(2) }}</span>
            </p>
            <p
              class="flex justify-between w-48 text-lg font-bold text-dunhuang-red pt-2"
            >
              <span>实付金额:</span>
              <span class="font-mono">¥ {{ total.toFixed(2) }}</span>
            </p>
          </div>

          <button
            type="submit"
            :disabled="saving"
            class="px-6 py-2 rounded text-sm font-medium transition-colors bg-dunhuang-red text-white hover:bg-dunhuang-red/90 shadow-md disabled:opacity-50"
          >
            {{ saving ? "保存中..." : t("billing.save") }}
          </button>
        </div>
      </form>
    </div>

    <!-- 历史单据列表 -->
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

        <div class="flex gap-3 items-center">
          <!-- 日期筛选 -->
          <div
            class="flex items-center bg-white border border-dunhuang-blue/30 rounded px-2 shadow-sm transition-colors hover:border-dunhuang-blue/50 focus-within:border-dunhuang-blue focus-within:ring-2 focus-within:ring-dunhuang-blue/20 h-[28px]"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              class="text-dunhuang-blue shrink-0"
            >
              <rect width="18" height="18" x="3" y="4" rx="2" ry="2" />
              <line x1="16" x2="16" y1="2" y2="6" />
              <line x1="8" x2="8" y1="2" y2="6" />
              <line x1="3" x2="21" y1="10" y2="10" />
            </svg>
            <input
              type="date"
              v-model="filterDate"
              @change="fetchBills"
              class="bg-transparent border-none text-xs text-dunhuang-blue font-medium focus:outline-none focus:ring-0 p-0 w-28 ml-1.5 cursor-pointer [&::-webkit-calendar-picker-indicator]:cursor-pointer [&::-webkit-calendar-picker-indicator]:opacity-60 hover:[&::-webkit-calendar-picker-indicator]:opacity-100 transition-opacity"
            />
            <div
              class="h-4 w-px bg-dunhuang-yellow/30 mx-1"
              v-if="filterDate !== getTodayDateString()"
            ></div>
            <button
              v-if="filterDate !== getTodayDateString()"
              @click="resetToToday"
              class="text-dunhuang-text/50 hover:text-dunhuang-red text-xs px-2 py-1 rounded transition-colors hover:bg-dunhuang-red/10 font-medium whitespace-nowrap"
              title="重置为今日"
            >
              今日
            </button>
          </div>

          <!-- 搜索 -->
          <div
            class="flex items-center bg-white border border-dunhuang-blue/30 rounded px-2 shadow-sm transition-colors hover:border-dunhuang-blue/50 focus-within:border-dunhuang-blue focus-within:ring-2 focus-within:ring-dunhuang-blue/20 h-[28px]"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
              class="text-dunhuang-blue shrink-0"
            >
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" x2="16.65" y1="21" y2="16.65"></line>
            </svg>
            <input
              type="text"
              v-model="billingSearch"
              placeholder="搜索品种..."
              class="bg-transparent border-none text-xs text-dunhuang-blue font-medium focus:outline-none focus:ring-0 p-0 w-28 ml-1.5"
            />
            <button
              v-if="billingSearch"
              @click="billingSearch = ''"
              class="text-dunhuang-text/40 hover:text-dunhuang-red text-xs leading-none px-1"
            >
              ✕
            </button>
          </div>

          <!-- 批量删除 -->
          <button
            v-if="selectedBillIds.length > 0"
            @click="confirmBatchDeleteBills"
            class="px-3 py-1.5 rounded text-xs transition-colors text-dunhuang-red hover:bg-dunhuang-red/10 border border-dunhuang-red/30"
          >
            批量删除 ({{ selectedBillIds.length }})
          </button>

          <!-- 导出 -->
          <button
            @click="exportBills"
            type="button"
            class="px-3 py-1.5 rounded text-xs transition-colors text-dunhuang-blue hover:bg-dunhuang-blue/10 border border-dunhuang-blue/30"
          >
            {{ activeTab === "current" ? "导出单据" : "导出历史" }}
          </button>

          <!-- current tab 专有按钮 -->
          <template v-if="activeTab === 'current'">
            <button
              @click="goToImport"
              type="button"
              class="px-3 py-1.5 rounded text-xs transition-colors text-dunhuang-blue hover:bg-dunhuang-blue/10 border border-dunhuang-blue/30"
            >
              导入
            </button>
            <button
              @click="
                initNewBill();
                showForm = true;
              "
              class="px-3 py-1.5 rounded text-xs transition-colors bg-dunhuang-blue text-white hover:bg-dunhuang-blue/90 shadow-sm"
            >
              + 新增单据
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
                    class="w-4 h-4 rounded border-2 border-dunhuang-yellow/40 text-dunhuang-blue focus:ring-2 focus:ring-dunhuang-blue/30 focus:ring-offset-0 cursor-pointer transition-all duration-200"
                    :checked="isAllSelected"
                    @change="toggleSelectAll"
                  />
                </div>
                <div class="col-th flex-[0.25] flex items-center">序号</div>
                <div class="col-th flex-[0.55] flex items-center">品种名称</div>
                <div class="col-th flex-[0.5] flex items-center">重量</div>
                <div class="col-th flex-[0.6] flex items-center">单价</div>
                <div class="col-th flex-[0.6] flex items-center">小计</div>
                <div class="col-th flex-[0.5] flex items-center">服务费</div>
                <div class="col-th flex-[0.6] flex items-center">总金额</div>
                <div class="col-th flex-[0.9] flex items-center">添加时间</div>
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
                    class="w-4 h-4 rounded border-2 border-dunhuang-yellow/40 text-dunhuang-blue focus:ring-2 focus:ring-dunhuang-blue/30 focus:ring-offset-0 cursor-pointer transition-all duration-200"
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
                <div class="col-td flex-[0.5] flex items-center">
                  {{ b.weight.toFixed(2) }}
                </div>
                <div class="col-td-mono-red flex-[0.6] flex items-center">
                  ¥ {{ b.unit_price.toFixed(2) }}
                </div>
                <div class="col-td-green flex-[0.6] flex items-center">
                  ¥ {{ b.subtotal.toFixed(2) }}
                </div>
                <div class="col-td flex-[0.5] flex items-center">
                  {{ formatFee(b) }}
                </div>
                <div class="col-td-bold-red flex-[0.6] flex items-center">
                  ¥ {{ b.total_amount.toFixed(2) }}
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
              <div
                v-if="bills.length > 0"
                class="flex w-full shrink-0 h-[42px] bg-dunhuang-yellow/5 border-t-2 border-dunhuang-yellow/30"
              >
                <div
                  class="w-10 shrink-0 sticky left-0 bg-dunhuang-yellow/5 sticky-col-left"
                ></div>
                <div class="px-4 py-2 flex-[0.25] flex items-center"></div>
                <div class="px-4 py-2 flex-[0.55] flex items-center"></div>
                <div class="px-4 py-2 flex-[0.5] flex items-center">
                  <span class="text-xs text-dunhuang-text/60">{{
                    tableSumWeight.toFixed(2)
                  }}</span>
                </div>
                <div class="px-4 py-2 flex-[0.6] flex items-center"></div>
                <div class="px-4 py-2 flex-[0.6] flex items-center">
                  <span class="text-xs font-bold text-dunhuang-green"
                    >¥ {{ tableSumSubtotal.toFixed(2) }}</span
                  >
                </div>
                <div class="px-4 py-2 flex-[0.5] flex items-center">
                  <span class="text-xs text-dunhuang-text/60"
                    >¥ {{ tableSumFee.toFixed(2) }}</span
                  >
                </div>
                <div class="px-4 py-2 flex-[0.6] flex items-center">
                  <span class="text-xs font-bold text-dunhuang-red"
                    >¥ {{ tableSumTotal.toFixed(2) }}</span
                  >
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
          条数据
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

    <!-- 查看详情弹窗 -->
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
      <div class="grid grid-cols-1 md:grid-cols-2 gap-0 overflow-hidden flex-1">
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
            <!-- 单号 & 品种 -->
            <div
              class="flex justify-between items-center py-2.5 border-b border-dunhuang-yellow/10"
            >
              <span class="text-dunhuang-text/50 text-sm">单号</span>
              <span
                class="font-mono bg-dunhuang-yellow/10 px-2.5 py-1 rounded-full text-dunhuang-blue text-xs font-bold tracking-wider"
              >
                #{{ String(viewingBill?.id).padStart(5, "0") }}
              </span>
            </div>
            <div
              class="flex justify-between items-center py-2.5 border-b border-dunhuang-yellow/10"
            >
              <span class="text-dunhuang-text/50 text-sm">品种名称</span>
              <span class="font-medium text-dunhuang-blue text-sm">{{
                getSpeciesName(viewingBill?.species_id)
              }}</span>
            </div>
            <div
              class="flex justify-between items-center py-2.5 border-b border-dunhuang-yellow/10"
            >
              <span class="text-dunhuang-text/50 text-sm">重量</span>
              <span class="font-medium text-sm"
                >{{ viewingBill?.weight?.toFixed(2) }} 斤</span
              >
            </div>
            <div
              class="flex justify-between items-center py-2.5 border-b border-dunhuang-yellow/10"
            >
              <span class="text-dunhuang-text/50 text-sm">单价</span>
              <span class="font-mono text-dunhuang-red text-sm"
                >¥ {{ viewingBill?.unit_price?.toFixed(2) }}</span
              >
            </div>

            <!-- 小计——加背景强调 -->
            <div
              class="flex justify-between items-center py-2.5 border-b border-dunhuang-yellow/10 bg-dunhuang-yellow/5 -mx-2 px-2 rounded"
            >
              <span class="text-dunhuang-text/50 text-sm">小计</span>
              <span class="font-mono text-dunhuang-green text-sm"
                >¥ {{ viewingBill?.subtotal?.toFixed(2) }}</span
              >
            </div>
            <div
              class="flex justify-between items-center py-2.5 border-b border-dunhuang-yellow/10"
            >
              <span class="text-dunhuang-text/50 text-sm">服务费</span>
              <span class="font-mono text-dunhuang-text/70 text-sm">{{
                viewingBill ? formatFee(viewingBill) : ""
              }}</span>
            </div>

            <!-- 实付金额——加背景强调 -->
            <div
              class="flex justify-between items-center py-3 bg-dunhuang-red/5 -mx-2 px-2 rounded-lg border border-dunhuang-red/10"
            >
              <span class="text-dunhuang-text/70 text-sm font-medium"
                >实付金额</span
              >
              <span class="font-mono font-bold text-dunhuang-red text-base"
                >¥ {{ viewingBill?.total_amount?.toFixed(2) }}</span
              >
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
          <div class="overflow-y-auto thin-scrollbar pr-2 max-h-[340px]">
            <div v-if="viewingBillLogs.length > 0" class="space-y-3">
              <div
                v-for="log in viewingBillLogs"
                :key="log.id"
                class="bg-dunhuang-bg/50 rounded-lg px-4 py-3 text-sm border border-dunhuang-yellow/10 hover:border-dunhuang-yellow/30 transition-colors"
              >
                <div class="flex justify-between items-center mb-2">
                  <span
                    :class="[
                      'px-2.5 py-0.5 rounded-full text-xs font-medium',
                      log.action === 'CREATE'
                        ? 'bg-dunhuang-green/10 text-dunhuang-green'
                        : log.action === 'UPDATE' || log.action === 'COMPLETED'
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
                    class="text-dunhuang-text/40 mb-1 border-b border-dunhuang-yellow/10 pb-1"
                  >
                    数据变更明细：
                  </div>
                  <div
                    v-for="item in formatUpdateDiff(log.old_data, log.new_data)"
                    :key="item.label"
                    class="flex gap-2"
                  >
                    <span class="w-14 shrink-0 text-dunhuang-text/50"
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
            <div v-else class="text-dunhuang-text/40 text-center py-12 text-sm">
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

      <!-- 底部按钮 -->
      <div
        class="flex justify-end gap-3 px-8 py-4 border-t border-dunhuang-yellow/20 shrink-0 bg-dunhuang-bg/50"
      >
        <button
          @click="showViewModal = false"
          class="px-5 py-2 rounded-full text-sm transition-colors text-dunhuang-text/60 hover:text-dunhuang-text hover:bg-dunhuang-yellow/20 border border-dunhuang-yellow/30"
        >
          关闭
        </button>
        <button
          v-if="activeTab === 'current'"
          @click="
            () => {
              showViewModal = false;
              editBill(viewingBill);
            }
          "
          class="px-5 py-2 rounded-full text-sm transition-colors bg-dunhuang-blue text-white hover:bg-dunhuang-blue/90 shadow-sm"
        >
          编辑单据
        </button>
      </div>
    </div>
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
        条单据。<br />此操作不可撤销，确定要批量删除吗？
      </template>
    </ConfirmDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import * as XLSX from "xlsx";
import api from "../api";
import { apiErrorMessage, isAuthError } from "../lib/error";
import { dateTimeStr, diffFields } from "../lib/utils";
import ConfirmDialog from "../components/ConfirmDialog.vue";

const { t } = useI18n();
const router = useRouter();

const activeTab = ref("current");

const tabs = [
  { key: "current", label: "最新单据" },
  { key: "history", label: "历史单据" },
];

const getTodayDateString = () => {
  const tzOffset = new Date().getTimezoneOffset() * 60000; // offset in milliseconds
  return new Date(Date.now() - tzOffset).toISOString().slice(0, 10);
};

const filterDate = ref(getTodayDateString());
const billingSearch = ref("");

watch(
  () => activeTab.value,
  (newTab) => {
    billingSearch.value = "";
    if (newTab === "history") {
      filterDate.value = "";
    } else {
      filterDate.value = getTodayDateString();
    }
  },
);

watch(billingSearch, () => {
  currentPage.value = 1;
});

const bills = ref<any[]>([]);
const speciesList = ref<any[]>([]);
const saving = ref(false);
const showForm = ref(false);
const showViewModal = ref(false);
const viewingBill = ref<any>(null);
const viewingBillLogs = ref<any[]>([]);

const editingSpecies = computed(
  () => speciesList.value.find((s) => s.id == bill.value.species_id) || null,
);
const deleteConfirm = ref({
  show: false,
  id: null as number | null,
  isBatch: false,
});
const selectedBillIds = ref<number[]>([]);

const isAllSelected = computed({
  get: () => {
    return (
      paginatedBills.value.length > 0 &&
      paginatedBills.value.every((b) => selectedBillIds.value.includes(b.id))
    );
  },
  set: (val) => {
    if (val) {
      const idsToAdd = paginatedBills.value
        .filter((b) => !selectedBillIds.value.includes(b.id))
        .map((b) => b.id);
      selectedBillIds.value.push(...idsToAdd);
    } else {
      const paginatedIds = paginatedBills.value.map((b) => b.id);
      selectedBillIds.value = selectedBillIds.value.filter(
        (id) => !paginatedIds.includes(id),
      );
    }
  },
});

const toggleSelectAll = (e: Event) => {
  isAllSelected.value = (e.target as HTMLInputElement).checked;
};

// Pagination states
const currentPage = ref(1);
const pageSize = 10;

const totalItems = computed(() => filteredBills.value.length);
const totalPages = computed(() => Math.ceil(totalItems.value / pageSize));

const filteredBills = computed(() => {
  const q = billingSearch.value.trim().toLowerCase();
  if (!q) return bills.value;
  return bills.value.filter((b: any) => {
    const sp = speciesList.value.find((s: any) => s.id === b.species_id);
    return sp && sp.name_zh.toLowerCase().includes(q);
  });
});

const paginatedBills = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  const end = start + pageSize;
  return filteredBills.value.slice(start, end);
});

const tableSumWeight = computed(() =>
  Number(
    paginatedBills.value.reduce((s, b) => s + (b.weight || 0), 0).toFixed(2),
  ),
);

const tableSumSubtotal = computed(() =>
  Number(
    paginatedBills.value.reduce((s, b) => s + (b.subtotal || 0), 0).toFixed(2),
  ),
);

const tableSumFee = computed(() =>
  Number(
    paginatedBills.value
      .reduce((s, b) => {
        const v =
          b.fee_type === "PERCENTAGE"
            ? (b.subtotal || 0) * ((b.fee_value || 0) / 100)
            : b.fee_value || 0;
        return s + v;
      }, 0)
      .toFixed(2),
  ),
);

const tableSumTotal = computed(() =>
  Number(
    paginatedBills.value
      .reduce((s, b) => s + (b.total_amount || 0), 0)
      .toFixed(2),
  ),
);

const displayedPages = computed(() => {
  const pages = [];
  let start = Math.max(1, currentPage.value - 2);
  let end = Math.min(totalPages.value, start + 4);

  if (end - start < 4) {
    start = Math.max(1, end - 4);
  }

  for (let i = start; i <= end; i++) {
    pages.push(i);
  }
  return pages;
});

const formatAction = (action: string) => {
  const map: Record<string, string> = {
    CREATE: "新增单据",
    UPDATE: "修改单据",
    DELETE: "删除单据",
    COMPLETED: "单据归档",
  };
  return map[action] || action;
};

const formatUpdateDiff = (
  oldDataStr: string | null,
  newDataStr: string | null,
) => {
  if (!oldDataStr || !newDataStr) return [];
  try {
    const oldD = JSON.parse(oldDataStr);
    const newD = JSON.parse(newDataStr);
    const result = diffFields(oldDataStr, newDataStr, [
      {
        key: "species_id",
        label: "品种",
        format: (v) => getSpeciesName(v as number),
      },
      { key: "weight", label: "重量", format: (v) => `${v} kg` },
      { key: "unit_price", label: "单价", format: (v) => `¥${v}` },
    ]);

    if (oldD.fee_type !== newD.fee_type || oldD.fee_value !== newD.fee_value) {
      const fmt = (type: string, val: number) =>
        type === "PERCENTAGE" ? `${val}%` : `¥${val}`;
      const oldFee = fmt(oldD.fee_type, oldD.fee_value);
      const newFee = fmt(newD.fee_type, newD.fee_value);
      if (oldFee !== newFee)
        result.push({ label: "服务费", old: oldFee, new: newFee });
    }
    return result;
  } catch {
    return [];
  }
};

const newBillDefaults = () => ({
  id: null as number | null,
  species_id: "",
  weight: 0,
  unit_price: 0,
  currency: "CNY",
  fee_type: "FIXED",
  fee_value: 0,
  status: "DRAFT",
});

const bill = ref(newBillDefaults());

const initNewBill = () => {
  bill.value = newBillDefaults();
  if (speciesList.value.length > 0) {
    bill.value.species_id = speciesList.value[0].id;
    handleSpeciesChange();
  }
};

const currentUnit = computed(() => {
  const sp = speciesList.value.find((s) => s.id === bill.value.species_id);
  return sp ? sp.default_unit : "kg";
});

const handleSpeciesChange = () => {
  const sp = speciesList.value.find((s) => s.id === bill.value.species_id);
  if (sp && sp.default_price !== undefined) {
    bill.value.unit_price = sp.default_price;
  }
};

const subtotal = computed(() => {
  return Number(
    ((bill.value.weight || 0) * (bill.value.unit_price || 0)).toFixed(2),
  );
});

const fee = computed(() => {
  if (bill.value.fee_type === "PERCENTAGE") {
    return Number(
      (subtotal.value * ((bill.value.fee_value || 0) / 100)).toFixed(2),
    );
  }
  return Number((bill.value.fee_value || 0).toFixed(2));
});

const total = computed(() => Number((subtotal.value + fee.value).toFixed(2)));

const goToImport = () => {
  router.push("/import");
};

const goBackToList = () => {
  showForm.value = false;
  bill.value.id = null;
  bill.value.weight = 0;
};

const adjustPrice = (delta: number) => {
  bill.value.unit_price = Number((bill.value.unit_price + delta).toFixed(2));
};

const formatPriceInput = () => {
  bill.value.unit_price = Number((bill.value.unit_price || 0).toFixed(2));
};

const formatWeightInput = () => {
  bill.value.weight = Number((bill.value.weight || 0).toFixed(2));
};

const formatFeeInput = () => {
  bill.value.fee_value = Number((bill.value.fee_value || 0).toFixed(2));
};

const fetchSpecies = async () => {
  try {
    const res = await api.get("/species");
    speciesList.value = res.data || [];
    if (res.data && res.data.length > 0 && !bill.value.species_id) {
      bill.value.species_id = res.data[0].id;
      handleSpeciesChange();
    }
  } catch (error: any) {
    if (isAuthError(error)) return;
    console.error("Failed to fetch species", error);
  }
};

const fetchBills = async () => {
  try {
    let url = `/bills?limit=0`;

    const res = await api.get(url);
    let data = res.data || [];

    if (filterDate.value) {
      const datePrefix = filterDate.value; // "YYYY-MM-DD"
      bills.value = data.filter((b: any) =>
        b.created_at.startsWith(datePrefix),
      );
    } else {
      bills.value = data;
    }
    currentPage.value = 1; // Reset to first page when data changes
  } catch (error: any) {
    if (isAuthError(error)) return;
    console.error("Failed to fetch bills", error);
  }
};

const switchTab = (tab: string) => {
  activeTab.value = tab;
  showForm.value = false;
  selectedBillIds.value = [];
  currentPage.value = 1;
  fetchBills();
};

const resetToToday = () => {
  filterDate.value = getTodayDateString();
  fetchBills();
};

const exportBills = () => {
  if (bills.value.length === 0) {
    alert("没有可导出的单据数据");
    return;
  }

  const exportData = bills.value.map((b) => ({
    单号: `#${String(b.id).padStart(5, "0")}`,
    品种名称: getSpeciesName(b.species_id),
    重量: b.weight.toFixed(2),
    单价: `¥ ${b.unit_price.toFixed(2)}`,
    小计: `¥ ${b.subtotal.toFixed(2)}`,
    服务费: formatFee(b),
    总金额: `¥ ${b.total_amount.toFixed(2)}`,
    添加时间: dateTimeStr(b.created_at),
  }));

  const worksheet = XLSX.utils.json_to_sheet(exportData);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "历史单据");

  const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, "");
  XLSX.writeFile(workbook, `历史单据_${dateStr}.xlsx`);
};

const getSpeciesName = (id: number) => {
  const sp = speciesList.value.find((s) => s.id === id);
  return sp ? sp.name_zh : `未知品种(${id})`;
};

const formatFee = (b: any) => {
  if (b.fee_type === "PERCENTAGE") {
    return `${b.fee_value}%`;
  }
  return `+ ¥ ${b.fee_value.toFixed(2)}`;
};

const saveBill = async () => {
  if (!bill.value.species_id) {
    alert("请选择品种");
    return;
  }
  if (!Number.isFinite(bill.value.weight) || bill.value.weight <= 0) {
    alert("重量必须大于0");
    return;
  }
  if (!Number.isFinite(bill.value.unit_price) || bill.value.unit_price <= 0) {
    alert("单价必须大于0");
    return;
  }
  saving.value = true;
  const isNew = !bill.value.id;
  try {
    const payload = {
      ...bill.value,
      species_id: Number(bill.value.species_id),
      status: "COMPLETED",
    };
    if (bill.value.id) {
      const response = await api.put(`/bills/${bill.value.id}`, payload);
      const index = bills.value.findIndex((b) => b.id === bill.value.id);
      if (index !== -1) bills.value[index] = response.data;
      alert("单据更新成功！");
    } else {
      const response = await api.post("/bills", payload);
      bills.value.unshift(response.data);
      currentPage.value = 1;
      alert("单据保存成功！");
    }

    bill.value.weight = 0;
    bill.value.id = null;
    showForm.value = false;

    if (isNew && activeTab.value !== "current") {
      activeTab.value = "current";
      fetchBills();
    }
  } catch (error: any) {
    if (isAuthError(error)) return;
    alert(apiErrorMessage(error, "保存单据"));
  } finally {
    saving.value = false;
  }
};

const viewBill = async (b: any) => {
  viewingBill.value = b;
  viewingBillLogs.value = [];
  showViewModal.value = true;
  try {
    const res = await api.get(`/logs/bill/${b.id}`);
    viewingBillLogs.value = res.data || [];
  } catch (error: any) {
    if (isAuthError(error)) return;
    console.error("Failed to fetch bill logs", error);
  }
};

const editBill = (b: any) => {
  bill.value = {
    id: b.id,
    species_id: String(b.species_id),
    weight: b.weight,
    unit_price: b.unit_price,
    currency: b.currency,
    fee_type: "FIXED", // Force FIXED since we removed PERCENTAGE option
    fee_value:
      b.fee_type === "PERCENTAGE"
        ? Number((b.weight * b.unit_price * (b.fee_value / 100)).toFixed(2))
        : b.fee_value,
    status: b.status,
  };
  showForm.value = true;
  window.scrollTo({ top: 0, behavior: "smooth" });
};

const confirmDeleteBill = (id: number) => {
  deleteConfirm.value = { show: true, id, isBatch: false };
};

const confirmBatchDeleteBills = () => {
  if (selectedBillIds.value.length === 0) return;
  deleteConfirm.value = { show: true, id: null, isBatch: true };
};

const executeDeleteBill = async () => {
  if (deleteConfirm.value.isBatch) {
    try {
      for (const id of selectedBillIds.value) {
        await api.delete(`/bills/${id}`);
      }
      bills.value = bills.value.filter(
        (b) => !selectedBillIds.value.includes(b.id),
      );
      selectedBillIds.value = [];
      deleteConfirm.value.show = false;
      alert("批量删除成功！");
    } catch (error: any) {
      if (isAuthError(error)) return;
      alert(apiErrorMessage(error, "批量删除"));
      deleteConfirm.value.show = false;
    }
  } else {
    const id = deleteConfirm.value.id;
    if (!id) return;

    try {
      await api.delete(`/bills/${id}`);
      deleteConfirm.value.show = false;
      bills.value = bills.value.filter((b) => b.id !== id);
    } catch (error: any) {
      if (isAuthError(error)) return;
      alert(apiErrorMessage(error, "删除单据"));
    }
  }
};

onMounted(() => {
  fetchSpecies();
  fetchBills();
});
</script>

<style scoped>
.col-th {
  @apply px-4 py-2 border-b border-dunhuang-yellow/40 whitespace-nowrap;
}
.col-td {
  @apply px-4 py-2 whitespace-nowrap;
}
.col-td-mono-red {
  @apply px-4 py-2 font-mono text-dunhuang-red whitespace-nowrap;
}
.col-td-bold-red {
  @apply px-4 py-2 font-bold text-dunhuang-red whitespace-nowrap;
}
.col-td-green {
  @apply px-4 py-2 text-dunhuang-green whitespace-nowrap;
}
.col-td-muted {
  @apply px-4 py-2 text-dunhuang-text/80 whitespace-nowrap;
}
.col-td-time {
  @apply px-4 py-2 text-xs text-dunhuang-text/70 whitespace-nowrap;
}
</style>

<style>
@import "../assets/table.css";
</style>
