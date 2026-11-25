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
          <div class="flex flex-wrap items-center gap-2 sm:gap-4">
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
              {{ bill.id ? "编辑单据" : "新增物命" }}
              <span
                v-if="bill.id && editingSpecies"
                class="text-sm font-sans font-medium text-dunhuang-text/50"
              >
                · {{ editingSpecies.name_zh }}
              </span>
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
                      >{{ formatMoney(toJinPrice(editingSpecies.default_price)) }}</span
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
                    >{{ t("billing.unit_price") }}（元/斤）</label
                  >
                  <input
                    type="text"
                    inputmode="decimal"
                    v-model="bill.unit_price"
                    @blur="bill.unit_price = (+bill.unit_price || 0).toFixed(2)"
                    required
                    class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2.5 px-3 text-sm focus:ring-0 outline-none font-mono text-dunhuang-red focus:bg-white focus:border-dunhuang-blue/50 transition-colors"
                  />
                </div>
                <div>
                  <label
                    class="block text-sm font-medium text-dunhuang-text mb-2"
                    >重量 ({{ editingSpecies?.default_unit ?? "斤" }})</label
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
                    >随喜类型</label
                  >
                  <div class="flex items-end gap-3 flex-wrap">
                    <PaymentPicker v-model="bill.payment_method" />
                    <div class="w-32">
                      <span class="mb-1 block text-xs text-dunhuang-text/50"
                        >支付宝（元）</span
                      >
                      <input
                        type="text"
                        inputmode="decimal"
                        v-model="bill.alipay_amount"
                        @blur="
                          bill.alipay_amount =
                            bill.alipay_amount.trim() === ''
                              ? ''
                              : (+bill.alipay_amount).toFixed(2)
                        "
                        placeholder="必填"
                        class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2.5 px-3 text-sm focus:ring-0 outline-none font-mono"
                      />
                    </div>
                    <div class="w-32">
                      <span class="mb-1 block text-xs text-dunhuang-text/50"
                        >微信（元）</span
                      >
                      <input
                        type="text"
                        inputmode="decimal"
                        v-model="bill.wechat_amount"
                        @blur="
                          bill.wechat_amount =
                            bill.wechat_amount.trim() === ''
                              ? ''
                              : (+bill.wechat_amount).toFixed(2)
                        "
                        placeholder="必填"
                        class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2.5 px-3 text-sm focus:ring-0 outline-none font-mono"
                      />
                    </div>
                    <div class="w-32">
                      <span class="mb-1 block text-xs text-dunhuang-text/50"
                        >随喜放生（元）</span
                      >
                      <input
                        type="text"
                        inputmode="decimal"
                        v-model="bill.suixi_amount"
                        @blur="
                          bill.suixi_amount =
                            bill.suixi_amount.trim() === ''
                              ? ''
                              : (+bill.suixi_amount).toFixed(2)
                        "
                        placeholder="必填"
                        class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2.5 px-3 text-sm focus:ring-0 outline-none font-mono"
                      />
                    </div>
                  </div>
                </div>
                <div>
                  <label
                    class="block text-sm font-medium text-dunhuang-text mb-2"
                    >本周现场随喜（元）</label
                  >
                  <input
                    type="text"
                    inputmode="decimal"
                    v-model="bill.weekly_donation"
                    @blur="
                      bill.weekly_donation =
                        bill.weekly_donation.trim() === ''
                          ? ''
                          : (+bill.weekly_donation).toFixed(2)
                    "
                    placeholder="选填"
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
                    <div class="flex items-end justify-between gap-3 mb-2">
                      <label
                        class="block text-sm font-medium text-dunhuang-text"
                        >{{ t("billing.species_name") }}</label
                      >
                      <div
                        class="flex items-center bg-dunhuang-bg/50 border border-dunhuang-yellow/30 rounded-full px-3 h-8 w-52 focus-within:border-dunhuang-blue focus-within:bg-white transition-all duration-200"
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
                          v-model="speciesSearchText"
                          placeholder="搜索品种..."
                          class="flex-1 w-full bg-transparent border-none text-sm text-dunhuang-blue font-medium focus:outline-none focus:ring-0 px-2 placeholder:text-dunhuang-text/30"
                        />
                      </div>
                    </div>
                    <div
                      class="relative rounded-xl bg-dunhuang-bg/30 border border-dunhuang-yellow/20"
                    >
                      <div
                        v-if="filteredSpeciesList.length > 0"
                        class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2.5 overflow-y-auto thin-scrollbar max-h-[236px] p-2"
                      >
                        <div
                          v-for="sp in filteredSpeciesList"
                          :key="sp.id"
                          @click="toggleEntry(sp)"
                          :class="[
                            'cursor-pointer relative overflow-hidden rounded-xl border-2 p-2.5 h-[104px] transition-all duration-200 flex flex-col items-center justify-center gap-1 group',
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
                          <div class="text-center w-full">
                            <h4 class="font-medium text-dunhuang-blue text-sm truncate">
                              {{ sp.name_zh }}
                            </h4>
                            <div class="text-xs text-dunhuang-text/50 mt-0.5">
                              {{ formatMoney(toJinPrice(sp.default_price)) }}（元/斤）
                            </div>
                          </div>
                        </div>
                      </div>
                      <div
                        v-else
                        class="h-[236px] flex items-center justify-center text-sm text-dunhuang-text/40"
                      >
                        未找到匹配的品种
                      </div>
                      <div
                        class="pointer-events-none absolute left-0 right-0 bottom-0 h-6 bg-gradient-to-t from-dunhuang-bg/30 to-transparent rounded-b-xl"
                      ></div>
                    </div>
                  </div>
                  <div class="w-[220px] shrink-0 flex flex-col gap-4">
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
                    <div>
                      <label
                        class="block text-sm font-medium text-dunhuang-text mb-2"
                        >本周现场随喜（元）</label
                      >
                      <input
                        type="text"
                        inputmode="decimal"
                        v-model="bill.weekly_donation"
                        @blur="
                          bill.weekly_donation =
                            bill.weekly_donation.trim() === ''
                              ? ''
                              : (+bill.weekly_donation).toFixed(2)
                        "
                        placeholder="选填"
                        class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2.5 px-3 text-sm focus:ring-0 outline-none font-mono focus:bg-white focus:border-dunhuang-blue/50 transition-colors"
                      />
                    </div>
                  </div>
                </div>

                <!-- 随喜类型 -->
                <div class="shrink-0">
                  <label
                    class="block text-sm font-medium text-dunhuang-text mb-2"
                    >随喜类型</label
                  >
                  <div class="flex items-end gap-3 flex-wrap">
                    <PaymentPicker v-model="bill.payment_method" />
                    <div class="w-32">
                      <span class="mb-1 block text-xs text-dunhuang-text/50"
                        >支付宝（元）</span
                      >
                      <input
                        type="text"
                        inputmode="decimal"
                        v-model="bill.alipay_amount"
                        @blur="
                          bill.alipay_amount =
                            bill.alipay_amount.trim() === ''
                              ? ''
                              : (+bill.alipay_amount).toFixed(2)
                        "
                        placeholder="必填"
                        class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2.5 px-3 text-sm focus:ring-0 outline-none font-mono focus:bg-white focus:border-dunhuang-blue/50 transition-colors"
                      />
                    </div>
                    <div class="w-32">
                      <span class="mb-1 block text-xs text-dunhuang-text/50"
                        >微信（元）</span
                      >
                      <input
                        type="text"
                        inputmode="decimal"
                        v-model="bill.wechat_amount"
                        @blur="
                          bill.wechat_amount =
                            bill.wechat_amount.trim() === ''
                              ? ''
                              : (+bill.wechat_amount).toFixed(2)
                        "
                        placeholder="必填"
                        class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2.5 px-3 text-sm focus:ring-0 outline-none font-mono focus:bg-white focus:border-dunhuang-blue/50 transition-colors"
                      />
                    </div>
                    <div class="w-32">
                      <span class="mb-1 block text-xs text-dunhuang-text/50"
                        >随喜放生（元）</span
                      >
                      <input
                        type="text"
                        inputmode="decimal"
                        v-model="bill.suixi_amount"
                        @blur="
                          bill.suixi_amount =
                            bill.suixi_amount.trim() === ''
                              ? ''
                              : (+bill.suixi_amount).toFixed(2)
                        "
                        placeholder="必填"
                        class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2.5 px-3 text-sm focus:ring-0 outline-none font-mono focus:bg-white focus:border-dunhuang-blue/50 transition-colors"
                      />
                    </div>
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
                    class="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-2 overflow-y-auto pr-2 custom-scrollbar content-start"
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
                            class="text-xs text-dunhuang-text/50 font-medium mt-0.5"
                          >
                            <span class="text-dunhuang-red font-mono">{{
                              (+entry.unit_price || 0).toFixed(2)
                            }}</span>
                            元/斤
                          </span>
                        </div>
                        <button
                          type="button"
                          @click="removeEntry(idx)"
                          class="absolute top-1.5 right-1.5 text-dunhuang-text/40 hover:text-dunhuang-red transition-all duration-200 w-6 h-6 flex items-center justify-center rounded-full hover:bg-dunhuang-red/10 shrink-0"
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
                      <div class="grid grid-cols-3 gap-1.5 mt-0">
                        <div>
                          <label
                            class="block text-xs font-medium text-dunhuang-text/60 mb-1 truncate"
                            >单价（元）</label
                          >
                          <div class="relative">
                            <input
                              type="text"
                              inputmode="decimal"
                              v-model="entry.unit_price"
                              @blur="
                                entry.unit_price = (
                                  +entry.unit_price || 0
                                ).toFixed(2)
                              "
                              class="w-full bg-dunhuang-bg/50 border border-dunhuang-yellow/40 rounded-md px-1.5 py-1 text-sm focus:ring-0 outline-none font-mono text-dunhuang-red font-medium transition-colors focus:bg-white focus:border-dunhuang-blue/50 hover:border-dunhuang-yellow/60"
                            />
                          </div>
                        </div>
                        <div>
                          <label
                            class="block text-xs font-medium text-dunhuang-text/60 mb-1 truncate"
                            >总重 ({{
                              getEntryUnit(entry.species_id) || "斤"
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
                              class="w-full bg-dunhuang-bg/50 border border-dunhuang-yellow/40 rounded-md px-1.5 py-1 text-sm focus:ring-0 outline-none font-mono text-dunhuang-blue font-medium transition-colors focus:bg-white focus:border-dunhuang-blue/50 hover:border-dunhuang-yellow/60"
                            />
                          </div>
                        </div>
                        <div>
                          <label
                            class="block text-xs font-medium text-dunhuang-text/60 mb-1 truncate"
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
                              class="w-full bg-dunhuang-bg/50 border border-dunhuang-yellow/40 rounded-md px-1.5 py-1 text-sm focus:ring-0 outline-none font-mono text-dunhuang-blue font-medium transition-colors focus:bg-white focus:border-dunhuang-blue/50 hover:border-dunhuang-yellow/60"
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

            <div class="flex justify-end gap-3 shrink-0">
              <button
                type="button"
                @click="goBackToList"
                class="h-10 px-4 rounded-lg text-sm text-dunhuang-text/50 hover:text-dunhuang-text/70 hover:bg-dunhuang-yellow/20 transition-colors font-medium"
              >
                取消
              </button>
              <button
                type="submit"
                :disabled="saving"
                class="h-10 px-6 rounded-lg text-sm font-medium transition-colors bg-dunhuang-red text-white hover:bg-dunhuang-red/90 shadow-md disabled:opacity-50"
              >
                {{ saving ? "保存中..." : t("billing.save") }}
              </button>
            </div>
          </div>
        </form>
      </div>
    </Transition>

    <!-- 单据列表 -->
    <Transition name="switch-fade" mode="out-in">
      <div
        v-if="!showForm"
        class="bg-white rounded-2xl shadow-md border border-dunhuang-yellow/30 p-4 sm:p-6 lg:p-8"
      >
        <div class="flex flex-wrap items-center justify-between gap-3 mb-6">
          <div class="flex flex-wrap items-center gap-2 sm:gap-4">
            <!-- 品种搜索（常驻工具栏，不藏在筛选面板里） -->
            <SearchInput
              v-model="billingSearch"
              placeholder="搜索品种..."
              class="self-center"
              @search="refetchFromFirstPage"
              @clear="clearBillingSearch"
            />

            <!-- 放生日期筛选（直接放工具栏，选完立即生效） -->
            <DateRangeInput
              v-model:from="filterDateFrom"
              v-model:to="filterDateTo"
              align="left"
              class="w-[264px] self-center"
              @change="onDateRangeChange"
            />
          </div>

          <div class="flex gap-2 items-center">
            <!-- 批量删除 -->
            <button
              v-if="selectedBillIds.length > 0 && authStore.isAdmin"
              @click="confirmBatchDeleteBills"
              class="h-10 px-5 rounded-lg text-sm font-medium transition-all duration-200 text-dunhuang-red hover:bg-dunhuang-red/8 border border-dunhuang-red/25 hover:border-dunhuang-red/40"
            >
              批量删除 ({{ selectedBillIds.length }})
            </button>

            <!-- 批量导出（只导勾选的单据） -->
            <button
              v-if="selectedBillIds.length > 0"
              @click="exportBills"
              type="button"
              class="h-10 px-5 rounded-lg text-sm font-semibold transition-all duration-200 text-dunhuang-blue bg-dunhuang-blue/8 border border-dunhuang-blue/30 hover:bg-dunhuang-blue/15 hover:border-dunhuang-blue/50"
            >
              批量导出 ({{ selectedBillIds.length }})
            </button>

            <!-- 导入 -->
            <button
              v-if="authStore.isAdmin"
              @click="goToImport"
              type="button"
              class="h-10 px-5 rounded-lg text-sm font-medium transition-all duration-200 text-dunhuang-blue/80 hover:text-dunhuang-blue hover:bg-dunhuang-blue/6 border border-dunhuang-blue/15 hover:border-dunhuang-blue/35"
            >
              导入
            </button>

            <!-- 导出（无勾选时导全量） -->
            <button
              @click="exportBills"
              type="button"
              class="h-10 px-5 rounded-lg text-sm font-medium transition-all duration-200 text-dunhuang-blue/80 hover:text-dunhuang-blue hover:bg-dunhuang-blue/6 border border-dunhuang-blue/15 hover:border-dunhuang-blue/35"
            >
              导出
            </button>

            <!-- 新增（仅管理员可写，其他账号只读） -->
            <template v-if="authStore.isAdmin">
              <button
                @click="
                  initNewBill();
                  showForm = true;
                "
                class="h-10 px-6 rounded-lg text-sm font-semibold transition-all duration-200 bg-dunhuang-blue text-white hover:bg-dunhuang-blue/90 shadow-sm hover:shadow-md"
              >
                新增单据
              </button>
            </template>
          </div>
        </div>

        <div
          class="border border-dunhuang-yellow/30 rounded-lg bg-white overflow-hidden flex flex-col h-[556px]"
        >
          <!-- Header (Synced Scroll) -->
          <div
            ref="tableHeaderRef"
            class="overflow-hidden shrink-0 bg-[#f9f3e7] z-40 transform-gpu shadow-sm"
          >
            <div
              class="flex h-[42px] pr-[12px]"
              :style="{ minWidth: tableHeaderMinWidth + 'px' }"
            >
              <div
                class="bg-dunhuang-yellow/10 text-dunhuang-blue font-sans font-bold text-sm flex w-full h-full"
              >
                <div
                  class="px-3 py-2 border-b border-dunhuang-yellow/40 flex items-center justify-center w-12 shrink-0 sticky left-0 bg-[#f9f3e7] z-50"
                >
                  <input
                    type="checkbox"
                    class="custom-checkbox text-dunhuang-blue focus-visible:ring-2 focus-visible:ring-dunhuang-blue/30 focus-visible:ring-offset-1 outline-none"
                    :checked="isAllSelected"
                    @change="toggleSelectAll"
                  />
                </div>
                <div
                  class="col-th w-16 shrink-0 flex items-center z-50 bg-[#f9f3e7] sticky left-12"
                >
                  序号
                </div>
                <div
                  class="col-th flex-1 min-w-[100px] flex items-center z-50 bg-[#f9f3e7] shadow-[2px_0_5px_-2px_rgba(0,0,0,0.05)] sticky left-[112px]"
                >
                  品种
                </div>
                <div
                  class="col-th flex-1 min-w-[104px] flex items-center"
                >
                  重量（斤）
                </div>
                <div
                  class="col-th flex-1 min-w-[88px] flex items-center"
                >
                  单价（元/斤）
                </div>
                <div
                  class="col-th flex-1 min-w-[96px] flex items-center"
                >
                  总计（元）
                </div>
                <div
                  class="col-th flex-1 min-w-[104px] flex items-center"
                >
                  服务费（元）
                </div>
                <div
                  class="col-th flex-1 min-w-[104px] flex items-center"
                >
                  实付（元）
                </div>
                <div
                  class="col-th flex-1 min-w-[96px] flex items-center"
                >
                  放生日期
                </div>
                <div
                  class="col-th flex-1 min-w-[140px] hidden lg:flex items-center"
                >
                  添加时间
                </div>
                <div
                  class="col-th flex items-center justify-center w-[112px] sm:w-[168px] shrink-0 sticky right-0 bg-[#f9f3e7] z-50 shadow-[-2px_0_5px_-2px_rgba(0,0,0,0.05)]"
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
            class="overflow-y-auto overflow-x-auto panel-scrollbar [scrollbar-gutter:stable] flex-1 w-full"
          >
            <div
              class="flex flex-col pr-[6px] relative min-h-[450px]"
              :style="{ minWidth: tableMinWidth + 'px' }"
            >
              <div
                v-for="(b, index) in paginatedBills"
                :key="b.id ?? b.release_date ?? index"
                class="border-b border-dunhuang-yellow/20 hover:bg-[#fbf6ec] transition-colors text-sm group flex w-full shrink-0 h-[45px]"
              >
                <div
                  class="px-3 py-2 flex items-center justify-center w-12 shrink-0 sticky left-0 bg-white group-hover:bg-[#fbf6ec] transition-colors z-30"
                >
                  <input
                    type="checkbox"
                    class="custom-checkbox text-dunhuang-blue focus-visible:ring-2 focus-visible:ring-dunhuang-blue/30 focus-visible:ring-offset-1 outline-none"
                    :value="b.id"
                    v-model="selectedBillIds"
                  />
                </div>
                <div
                  class="col-td-muted w-16 shrink-0 flex items-center bg-white group-hover:bg-[#fbf6ec] transition-colors z-30 sticky left-12"
                >
                  {{ (currentPage - 1) * pageSize + index + 1 }}
                </div>
                <div
                  class="col-td font-medium flex-1 min-w-[100px] flex items-center truncate pr-2 bg-white group-hover:bg-[#fbf6ec] transition-colors z-30 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.05)] sticky left-[112px]"
                >
                  {{ getSpeciesName(b.species_id, b.species?.name_zh) }}
                </div>
                <div
                  class="col-td tabular-nums flex-1 min-w-[104px] flex items-center"
                >
                  {{ formatMoney(inJin(b.weight)) }}
                </div>
                <div
                  class="col-td-mono-red flex-1 min-w-[88px] flex items-center"
                >
                  {{ formatMoney(pricePerJin(b.unit_price)) }}
                </div>
                <div
                  class="col-td-green flex-1 min-w-[96px] flex items-center"
                >
                  {{ formatMoney(b.subtotal) }}
                </div>
                <div
                  class="col-td tabular-nums flex-1 min-w-[104px] flex items-center"
                >
                  {{ formatFee(b) }}
                </div>
                <div
                  class="col-td-mono-red flex-1 min-w-[104px] flex items-center"
                >
                  {{ b.paid_amount != null ? formatMoney(b.paid_amount) : "—" }}
                </div>
                <div
                  class="col-td flex-1 min-w-[96px] flex items-center"
                >
                  {{ dateStr(b.release_date || b.species?.release_date) }}
                </div>
                <div
                  class="col-td-time flex-1 min-w-[140px] hidden lg:flex items-center"
                >
                  {{ dateTimeStr(b.created_at) }}
                </div>
                <div
                  class="px-3 py-2 flex items-center justify-center w-[112px] sm:w-[168px] shrink-0 sticky right-0 bg-white group-hover:bg-[#fbf6ec] transition-colors z-30 shadow-[-2px_0_5px_-2px_rgba(0,0,0,0.05)]"
                >
                  <div class="flex items-center justify-center gap-1">
                    <button
                      @click="viewBill(b)"
                      class="px-1.5 sm:px-2 py-1.5 rounded text-xs sm:text-sm whitespace-nowrap shrink-0 transition-colors text-dunhuang-blue hover:bg-dunhuang-blue/10 border border-transparent hover:border-dunhuang-blue/30"
                    >
                      查看
                    </button>
                    <button
                      v-if="authStore.isAdmin"
                      @click="editBill(b)"
                      class="px-1.5 sm:px-2 py-1.5 rounded text-xs sm:text-sm whitespace-nowrap shrink-0 transition-colors text-dunhuang-green hover:bg-dunhuang-green/10 border border-transparent hover:border-dunhuang-green/30"
                    >
                      编辑
                    </button>
                    <button
                      v-if="authStore.isAdmin"
                      @click="confirmDeleteBill(b.id)"
                      class="px-1.5 sm:px-2 py-1.5 rounded text-xs sm:text-sm whitespace-nowrap shrink-0 transition-colors text-dunhuang-red hover:bg-dunhuang-red/10 border border-transparent hover:border-dunhuang-red/30"
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
                    class="px-3 py-2 flex items-center justify-center w-12 shrink-0 sticky left-0 bg-white z-30"
                  ></div>
                  <div
                    class="col-td-muted w-16 shrink-0 flex items-center bg-white z-30 sticky left-12"
                  ></div>
                  <div
                    class="col-td font-medium flex-1 min-w-[100px] flex items-center bg-white z-30 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.05)] sticky left-[112px]"
                  ></div>
                  <div
                    class="col-td tabular-nums flex-1 min-w-[104px] flex items-center"
                  ></div>
                  <div
                    class="col-td-mono-red flex-1 min-w-[88px] flex items-center"
                  ></div>
                  <div
                    class="col-td-green flex-1 min-w-[96px] flex items-center"
                  ></div>
                  <div
                    class="col-td tabular-nums flex-1 min-w-[104px] flex items-center"
                  ></div>
                  <div
                    class="col-td-mono-red flex-1 min-w-[104px] flex items-center"
                  ></div>
                  <div
                    class="col-td flex-1 min-w-[96px] flex items-center"
                  ></div>
                  <div
                    class="col-td-time flex-1 min-w-[140px] hidden lg:flex items-center"
                  ></div>
                  <div
                    class="px-3 py-2 flex items-center justify-center w-[168px] shrink-0 sticky right-0 bg-white z-30 shadow-[-2px_0_5px_-2px_rgba(0,0,0,0.05)]"
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
            <div
              class="flex h-[42px] pr-[12px]"
              :style="{ minWidth: tableHeaderMinWidth + 'px' }"
            >
              <div
                class="w-12 shrink-0 sticky left-0 bg-white z-50"
              ></div>
              <div
                class="w-16 shrink-0 bg-white z-50 sticky left-12"
              ></div>
              <div
                class="flex-1 min-w-[100px] flex items-center justify-end pr-4 text-xs text-dunhuang-text/60 bg-white z-50 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.05)] sticky left-[112px]"
              >
                总计
              </div>
              <div
                class="px-4 py-2 flex-1 min-w-[104px] flex items-center"
              >
                <span class="tabular-nums text-xs text-dunhuang-text/60">{{
                  formatMoney(inJin(tableSumWeight))
                }}</span>
              </div>
              <div
                class="px-4 py-2 flex-1 min-w-[88px] flex items-center"
              ></div>
              <div
                class="px-4 py-2 flex-1 min-w-[96px] flex items-center"
              >
                <span class="tabular-nums text-xs text-dunhuang-green">{{
                  formatMoney(tableSumSubtotal)
                }}</span>
              </div>
              <div
                class="px-4 py-2 flex-1 min-w-[104px] flex items-center"
              >
                <span class="tabular-nums text-xs text-dunhuang-text/60">{{
                  formatMoney(tableSumFee)
                }}</span>
              </div>
              <div
                class="px-4 py-2 flex-1 min-w-[104px] flex items-center"
                :title="`实付合计 = 单据实付 ${formatMoney(tableSumPaid)} + 车费/船费 ${formatMoney(tableSumExpense)}`"
              >
                <span class="tabular-nums text-xs text-dunhuang-red">{{
                  formatMoney(tableSumPaid + tableSumExpense)
                }}</span>
              </div>
              <div
                class="px-4 py-2 flex-1 min-w-[96px] flex items-center"
              ></div>
              <div
                class="px-4 py-2 flex-1 min-w-[140px] flex items-center"
              ></div>
              <div
                class="px-3 py-2 w-[168px] shrink-0 sticky right-0 bg-white z-50 shadow-[-2px_0_5px_-2px_rgba(0,0,0,0.05)]"
              ></div>
            </div>
          </div>
        </div>

        <div
          class="flex justify-between items-center mt-4 shrink-0 relative z-50 flex-wrap gap-3"
        >
          <div class="flex items-center gap-3 flex-wrap text-sm text-dunhuang-text/70">
            <span>
              共
              <span class="font-bold text-dunhuang-blue">{{ totalItems }}</span>
              条
            </span>
            <!-- 车费/船费：模板表尾的支出，已并入上方「实付」合计 -->
            <template v-if="tableSumExpense > 0">
              <span class="text-dunhuang-text/30">·</span>
              <span class="text-xs text-dunhuang-text/55">
                车费
                <span class="tabular-nums text-dunhuang-text/75">{{
                  formatMoney(tableSumExpenseCar)
                }}</span>
                <span class="text-dunhuang-text/30 mx-1">/</span>
                船费
                <span class="tabular-nums text-dunhuang-text/75">{{
                  formatMoney(tableSumExpenseShip)
                }}</span>
                元（已含在实付合计）
              </span>
            </template>
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
        class="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 bg-white rounded-2xl shadow-2xl border border-dunhuang-yellow/30 w-[calc(100vw-1.5rem)] max-w-xl max-h-[85vh] flex flex-col overflow-hidden"
      >
        <!-- 标题栏 -->
        <div
          class="flex items-center justify-between px-6 pt-5 pb-4 border-b border-dunhuang-yellow/20 shrink-0"
        >
          <div class="flex items-center gap-3">
            <div class="w-1 h-5 bg-dunhuang-red rounded-full"></div>
            <h3 class="text-lg font-serif text-dunhuang-blue font-bold">
              单据详情
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

        <!-- 内容区：单据信息 -->
        <div class="px-6 py-5 overflow-y-auto">
          <!-- 品种 + 放生日期 -->
          <div
            class="flex items-start justify-between gap-6 pb-5 border-b border-dunhuang-yellow/15"
          >
            <div class="min-w-0">
              <div class="text-xs text-dunhuang-text/45 mb-1.5">品种</div>
              <div
                class="text-lg font-serif font-bold text-dunhuang-blue truncate"
              >
                {{
                  getSpeciesName(
                    viewingBill?.species_id,
                    viewingBill?.species?.name_zh,
                  )
                }}
              </div>
            </div>
            <div class="text-right shrink-0">
              <div class="text-xs text-dunhuang-text/45 mb-1.5">放生日期</div>
              <div class="text-sm font-medium text-dunhuang-blue tabular-nums">
                {{ dateStr(viewingBill?.release_date || viewingBill?.created_at) || "-" }}
              </div>
            </div>
          </div>

          <!-- 数量与金额 -->
          <div class="grid grid-cols-2 gap-x-6 gap-y-5 py-5">
            <div>
              <div class="text-xs text-dunhuang-text/45 mb-1.5">重量（斤）</div>
              <div class="tabular-nums text-sm text-dunhuang-text/80">
                {{ formatMoney(inJin(viewingBill?.weight)) }}
              </div>
            </div>
            <div>
              <div class="text-xs text-dunhuang-text/45 mb-1.5">
                单价（元/斤）
              </div>
              <div class="tabular-nums text-sm text-dunhuang-red">
                {{ formatMoney(pricePerJin(viewingBill?.unit_price)) }}
              </div>
            </div>
            <div>
              <div class="text-xs text-dunhuang-text/45 mb-1.5">总计（元）</div>
              <div
                class="tabular-nums text-sm text-dunhuang-green font-medium"
              >
                {{ formatMoney(viewingBill?.subtotal) }}
              </div>
            </div>
            <div>
              <div class="text-xs text-dunhuang-text/45 mb-1.5">服务费（元）</div>
              <div class="tabular-nums text-sm text-dunhuang-text/70">
                {{ viewingBill ? formatFee(viewingBill) : "" }}
              </div>
            </div>
            <div v-if="viewingBill?.alipay_amount != null">
              <div class="text-xs text-dunhuang-text/45 mb-1.5">支付宝（元）</div>
              <div class="tabular-nums text-sm text-dunhuang-text/70">
                {{ formatMoney(viewingBill.alipay_amount) }}
              </div>
            </div>
            <div v-if="viewingBill?.wechat_amount != null">
              <div class="text-xs text-dunhuang-text/45 mb-1.5">微信（元）</div>
              <div class="tabular-nums text-sm text-dunhuang-text/70">
                {{ formatMoney(viewingBill.wechat_amount) }}
              </div>
            </div>
            <div v-if="viewingBill?.suixi_amount != null">
              <div class="text-xs text-dunhuang-text/45 mb-1.5">
                随喜放生（元）
              </div>
              <div class="tabular-nums text-sm text-dunhuang-text/70">
                {{ formatMoney(viewingBill.suixi_amount) }}
              </div>
            </div>
          </div>

          <!-- 实付：本行分摊 + 本批总额 -->
          <div
            class="rounded-xl border border-dunhuang-red/15 bg-dunhuang-red/[0.04] px-4 py-3.5 flex items-end justify-between"
          >
            <div>
              <div class="text-xs text-dunhuang-text/55">实付（元）</div>
              <div
                v-if="viewingBill?.batch_paid != null"
                class="text-[11px] text-dunhuang-text/45 mt-1 tabular-nums"
              >
                本批实付 {{ formatMoney(viewingBill.batch_paid) }}
              </div>
            </div>
            <div
              class="tabular-nums font-bold text-dunhuang-red text-2xl leading-none"
            >
              {{
                viewingBill?.paid_amount != null
                  ? formatMoney(viewingBill.paid_amount)
                  : "—"
              }}
            </div>
          </div>

          <!-- 记录时间 -->
          <div
            class="flex items-center justify-between pt-4 mt-5 border-t border-dunhuang-yellow/15 text-[11px] text-dunhuang-text/40"
          >
            <span>记录添加时间</span>
            <span class="tabular-nums">{{
              dateTimeStr(viewingBill?.created_at)
            }}</span>
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
import { onMounted, ref, computed } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { dateStr, dateTimeStr, formatMoney, toJin, toJinPrice } from "../lib/utils";
import ConfirmDialog from "../components/ConfirmDialog.vue";
import DateInput from "../components/DateInput.vue";
import DateRangeInput from "../components/DateRangeInput.vue";
import Pagination from "../components/Pagination.vue";
import PaymentPicker from "../components/PaymentPicker.vue";
import SearchInput from "../components/SearchInput.vue";
import { useSpecies } from "../composables/useSpecies";
import { useBillForm } from "../composables/useBillForm";
import { useBillTable } from "../composables/useBillTable";
import { useBillAudit } from "../composables/useBillAudit";

const { t } = useI18n();
const router = useRouter();
const authStore = useAuthStore();

const tableHeaderRef = ref<HTMLElement | null>(null);
const tableBodyRef = ref<HTMLElement | null>(null);
const tableFooterRef = ref<HTMLElement | null>(null);

// 系统内部单位：重量=公斤、单价=元/公斤（导入按斤换算、导出再换算回去）。
// 界面统一按模板的「斤 / 元每斤」展示：重量 ×2、单价 ÷2，总计/实付金额不变。
const inJin = toJin;
const pricePerJin = toJinPrice;

const handleTableScroll = (e: Event) => {
  const target = e.target as HTMLElement;
  if (tableHeaderRef.value) {
    tableHeaderRef.value.scrollLeft = target.scrollLeft;
  }
  if (tableFooterRef.value) {
    tableFooterRef.value.scrollLeft = target.scrollLeft;
  }
};

// 搜索框 ✕ 清空：SearchInput 只发 clear 事件，需要手动清词后再拉取
const clearBillingSearch = async () => {
  billingSearch.value = "";
  await refetchFromFirstPage();
};

// 工具栏上的日期范围：选完/清空立即按新范围重新查询
const onDateRangeChange = async () => {
  await refetchFromFirstPage();
};

const { speciesList, fetchSpecies } = useSpecies();

// 新增表单：品种选择区本地搜索（数据已在内存，纯前端过滤）
const speciesSearchText = ref("");
const filteredSpeciesList = computed(() => {
  const q = speciesSearchText.value.trim();
  if (!q) return speciesList.value;
  return speciesList.value.filter((sp) => sp.name_zh.includes(q));
});

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
  tableSumPaid,
  tableSumExpense,
  tableSumExpenseCar,
  tableSumExpenseShip,
  isAllSelected,
  toggleSelectAll,
  getSpeciesName,
  formatFee,
  fetchBills,
  refetchFromFirstPage,
  clearDateFilter,
  exportBills,
  confirmDeleteBill,
  confirmBatchDeleteBills,
  executeDeleteBill,
  upsertBill,
} = useBillTable(speciesList);

/**
 * 表格最小宽度：序号/品种/重量/单价/小计/服务费/总金额/放生日期/添加时间/操作。
 * 表头/表脚比表体多 6px，补偿竖向滚动条占位。
 */
const tableMinWidth = 1112;
const tableHeaderMinWidth = tableMinWidth + 6;

const { showViewModal, viewingBill, viewBill } = useBillAudit();

const goToImport = () => {
  router.push("/import");
};

const handleSaveBill = async () => {
  if (bill.value.id) {
    await saveSingleBill(upsertBill);
  } else {
    await saveBatchBills(upsertBill);
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
