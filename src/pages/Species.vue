<template>
  <div
    class="bg-white rounded-2xl shadow-md border border-dunhuang-yellow/30 p-8 relative"
  >
    <Transition name="fade">
      <div
        v-if="errorMsg"
        class="absolute top-4 left-1/2 -translate-x-1/2 z-50 max-w-md w-auto px-5 py-2.5 bg-dunhuang-red/95 text-white rounded-lg text-sm shadow-lg backdrop-blur"
      >
        {{ errorMsg }}
      </div>
    </Transition>
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-4">
        <SearchInput
          v-model="speciesSearchText"
          placeholder="搜索品种..."
          @search="handleSearch"
          @clear="handleClearSearch"
        />
      </div>
      <div class="flex gap-3">
        <button
          v-if="selectedIds.length > 0"
          @click="confirmBatchRemoveSpecies"
          class="bg-dunhuang-red/90 hover:bg-dunhuang-red text-white px-3 py-1.5 rounded text-xs transition-colors"
        >
          批量删除 ({{ selectedIds.length }})
        </button>
        <button
          v-if="authStore.isAdmin"
          @click="showImportModal = true"
          class="bg-dunhuang-yellow hover:bg-dunhuang-yellow/80 text-dunhuang-blue px-3 py-1.5 rounded text-xs transition-colors"
        >
          导入
        </button>
        <button
          @click="showAddModal = true"
          class="bg-dunhuang-blue hover:bg-dunhuang-green text-white px-3 py-1.5 rounded text-xs transition-colors"
        >
          + 新增品种
        </button>
      </div>
    </div>

    <div
      class="overflow-y-scroll overflow-x-hidden custom-scrollbar border border-dunhuang-yellow/30 rounded-lg bg-white h-[494px]"
    >
      <table class="w-full text-left border-collapse whitespace-nowrap">
        <thead
          class="sticky top-0 bg-white/90 backdrop-blur z-20 flex w-full transform-gpu h-[42px]"
        >
          <tr
            class="bg-dunhuang-yellow/20 text-dunhuang-blue font-serif text-sm flex w-full h-full"
          >
            <th
              class="px-3 py-2 border-b border-dunhuang-yellow/40 w-10 flex items-center justify-center shrink-0 sticky left-0 bg-dunhuang-yellow/20 backdrop-blur z-30 sticky-col-left"
            >
              <input
                type="checkbox"
                :checked="isAllSelected"
                @change="toggleAll"
                class="w-4 h-4 rounded border-2 border-dunhuang-yellow/40 text-dunhuang-red focus:ring-0 focus:ring-offset-0 cursor-pointer transition-all duration-200"
              />
            </th>
            <th
              class="px-4 py-2 border-b border-dunhuang-yellow/40 flex-1 flex items-center"
            >
              序号
            </th>
            <th
              class="px-4 py-2 border-b border-dunhuang-yellow/40 flex-1 flex items-center"
            >
              品种
            </th>
            <th
              class="px-4 py-2 border-b border-dunhuang-yellow/40 flex-1 flex items-center"
            >
              单价（元）
            </th>
            <th
              class="px-4 py-2 border-b border-dunhuang-yellow/40 flex-1 flex items-center"
            >
              放生日期
            </th>
            <th
              class="px-4 py-2 border-b border-dunhuang-yellow/40 flex-1 flex items-center"
            >
              默认单位
            </th>
            <th
              class="px-4 py-2 border-b border-dunhuang-yellow/40 flex-1 flex items-center"
            >
              图片
            </th>
            <th
              class="px-4 py-2 border-b border-dunhuang-yellow/40 flex items-center justify-center w-40 shrink-0 sticky right-0 bg-dunhuang-yellow/20 backdrop-blur z-30 sticky-col-right"
            >
              操作
            </th>
          </tr>
        </thead>
        <tbody class="flex flex-col relative min-h-[450px]">
          <tr
            v-for="(sp, index) in paginatedSpecies"
            :key="sp.id"
            class="border-b border-dunhuang-yellow/20 hover:bg-dunhuang-yellow/10 transition-colors text-sm group flex w-full shrink-0 h-[45px]"
          >
            <td
              class="px-3 py-1.5 flex items-center justify-center w-10 shrink-0 sticky left-0 bg-white/60 backdrop-blur-md group-hover:bg-dunhuang-yellow/10 transition-colors sticky-col-left"
            >
              <input
                type="checkbox"
                v-model="selectedIds"
                :value="sp.id"
                class="w-4 h-4 rounded border-2 border-dunhuang-yellow/40 text-dunhuang-red focus:ring-0 focus:ring-offset-0 cursor-pointer transition-all duration-200"
              />
            </td>
            <td
              class="px-4 py-1.5 text-dunhuang-text/80 flex-1 flex items-center"
            >
              {{ (currentPage - 1) * pageSize + index + 1 }}
            </td>
            <td class="px-4 py-1.5 font-medium flex-1 flex items-center">
              {{ sp.name_zh }}
            </td>
            <td
              class="px-4 py-1.5 tabular-nums text-dunhuang-red flex-1 flex items-center"
            >
              {{ formatMoney(sp.default_price) }}
            </td>
            <td class="px-4 py-1.5 flex-1 flex items-center text-sm">
              {{ dateStr(sp.release_date || sp.created_at) || "-" }}
            </td>
            <td class="px-4 py-1.5 flex-1 flex items-center">
              {{ sp.default_unit }}
            </td>
            <td class="px-4 py-1.5 flex-1 flex items-center">
              <div class="flex items-center">
                <img
                  v-if="sp.image_url"
                  :src="sp.image_url"
                  :alt="sp.name_zh"
                  class="w-10 h-8 rounded-lg object-cover border border-dunhuang-yellow/30 cursor-pointer hover:opacity-80 transition-opacity"
                  @click.stop="openImagePreview(sp.image_url)"
                />
                <div
                  v-else
                  class="flex items-center justify-center w-10 h-8 rounded-lg bg-dunhuang-yellow/10 border border-dunhuang-yellow/30 text-dunhuang-blue"
                  :title="sp.name_zh"
                >
                  <span class="text-[10px] font-bold">{{
                    sp.name_zh ? sp.name_zh.charAt(0) : "?"
                  }}</span>
                </div>
              </div>
            </td>
            <td
              class="px-3 py-1.5 flex items-center justify-center w-40 shrink-0 sticky right-0 bg-white/60 backdrop-blur-md group-hover:bg-dunhuang-yellow/10 transition-colors sticky-col-right"
            >
              <div class="flex items-center justify-center gap-1">
                <button
                  @click="openDetail(sp.id)"
                  class="px-2 py-1 rounded text-xs transition-colors text-dunhuang-blue hover:bg-dunhuang-blue/10 border border-transparent hover:border-dunhuang-blue/30"
                >
                  查看
                </button>
                <button
                  @click="openDetail(sp.id, true)"
                  class="px-2 py-1 rounded text-xs transition-colors text-dunhuang-green hover:bg-dunhuang-green/10 border border-transparent hover:border-dunhuang-green/30"
                >
                  编辑
                </button>
                <button
                  @click="confirmRemoveSpecies(sp.id)"
                  class="px-2 py-1 rounded text-xs transition-colors text-dunhuang-red hover:bg-dunhuang-red/10 border border-transparent hover:border-dunhuang-red/30"
                >
                  删除
                </button>
              </div>
            </td>
          </tr>
          <tr
            v-for="i in Math.max(0, 10 - paginatedSpecies.length)"
            :key="'placeholder-' + i"
            class="border-b border-dunhuang-yellow/10 text-sm flex w-full shrink-0 h-[45px]"
          >
            <td
              class="px-3 py-1.5 w-10 shrink-0 sticky left-0 bg-white/60 sticky-col-left"
            ></td>
            <td class="px-4 py-1.5 flex-1"></td>
            <td class="px-4 py-1.5 flex-1"></td>
            <td class="px-4 py-1.5 flex-1"></td>
            <td class="px-4 py-1.5 flex-1"></td>
            <td class="px-4 py-1.5 flex-1"></td>
            <td class="px-4 py-1.5 flex-1"></td>
            <td
              class="px-3 py-1.5 w-40 shrink-0 sticky right-0 bg-white/60 sticky-col-right"
            ></td>
          </tr>
          <tr
            v-if="species.length === 0 && !errorMsg"
            class="absolute inset-0 flex items-center justify-center pointer-events-none"
          >
            <td
              class="w-auto text-center text-dunhuang-text/50 bg-white/50 px-6 py-2 rounded-full backdrop-blur-sm shadow-sm border border-dunhuang-yellow/30"
            >
              暂未录入品种数据
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="flex justify-between items-center mt-4 shrink-0 relative z-30">
      <div class="text-sm text-dunhuang-text/70">
        共
        <span class="font-bold text-dunhuang-blue">{{ totalItems }}</span>
        个品种
        <span v-if="selectedIds.length > 0">
          (已选择
          <span class="font-bold text-dunhuang-red">{{
            selectedIds.length
          }}</span>
          项)
        </span>
      </div>

      <Pagination
        v-model:currentPage="currentPage"
        v-model:pageSize="pageSize"
        :totalPages="totalPages"
        :showPageSizeSelect="true"
      />
    </div>

    <Transition name="modal-backdrop">
      <div
        v-if="showAddModal"
        class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50"
      >
        <Transition name="modal" appear>
          <div
            v-if="showAddModal"
            class="bg-white rounded-2xl shadow-2xl border border-dunhuang-yellow w-full max-w-lg p-8"
          >
            <div class="mb-6 border-b border-dunhuang-yellow/20 pb-4">
              <h4 class="text-xl font-serif text-dunhuang-blue font-bold">
                新增品种
              </h4>
              <p class="text-xs text-dunhuang-text/50 mt-0.5">
                录入新的物命品种信息
              </p>
            </div>

            <form @submit.prevent="addSpecies" class="space-y-5 relative z-10">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div class="sm:col-span-2">
                  <label
                    class="block text-sm font-medium text-dunhuang-text mb-2"
                    >品种</label
                  >
                  <div class="relative">
                    <div
                      class="absolute left-0 top-0 bottom-0 w-10 flex items-center justify-center text-dunhuang-text/40"
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
                          d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                        />
                      </svg>
                    </div>
                    <input
                      v-model="newSp.name_zh"
                      required
                      placeholder="例如：草鱼、鲤鱼、鲈鱼"
                      class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-3 pl-10 pr-4 focus:ring-0 outline-none text-sm transition-shadow"
                    />
                  </div>
                </div>

                <div>
                  <label
                    class="block text-sm font-medium text-dunhuang-text mb-2"
                    >单价（元）</label
                  >
                  <div class="relative">
                    <input
                      type="text"
                      inputmode="decimal"
                      v-model="newSp.default_price"
                      required
                      @keydown.enter.prevent
                      @blur="
                        newSp.default_price = (
                          +newSp.default_price || 0
                        ).toFixed(2)
                      "
                      class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-3 px-4 text-center focus:ring-0 outline-none font-mono text-sm transition-shadow"
                    />
                  </div>
                </div>

                <div>
                  <label
                    class="block text-sm font-medium text-dunhuang-text mb-2"
                    >默认单位</label
                  >
                  <div class="grid grid-cols-2 gap-2">
                    <button
                      v-for="unit in unitOptions"
                      :key="unit"
                      type="button"
                      @click="newSp.default_unit = unit"
                      :class="[
                        'py-2.5 px-3 rounded-lg border text-sm font-medium transition-colors',
                        newSp.default_unit === unit
                          ? 'border-dunhuang-blue bg-dunhuang-blue/10 text-dunhuang-blue shadow-sm'
                          : 'border-dunhuang-yellow/40 bg-white text-dunhuang-text/70 hover:border-dunhuang-blue/50 hover:text-dunhuang-blue',
                      ]"
                    >
                      {{ unit }}
                    </button>
                  </div>
                </div>
              </div>

              <div>
                <label class="block text-sm font-medium text-dunhuang-text mb-2"
                  >放生日期</label
                >
                <DateInput
                  v-model="newSp.release_date"
                  placeholder="选择放生日期"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-dunhuang-text mb-2"
                  >品种图片</label
                >
                <div class="flex items-start gap-5">
                  <div
                    class="relative group cursor-pointer"
                    @click="triggerFileInput"
                  >
                    <div
                      class="w-24 h-24 rounded-xl border-2 border-dashed flex items-center justify-center overflow-hidden transition-colors"
                      :class="
                        previewUrl
                          ? 'border-dunhuang-blue/50'
                          : 'border-dunhuang-yellow/40 hover:border-dunhuang-blue/50 bg-dunhuang-bg'
                      "
                    >
                      <img
                        v-if="previewUrl"
                        :src="previewUrl"
                        class="w-full h-full object-cover"
                      />
                      <div
                        v-else-if="newSp.name_zh"
                        class="text-2xl font-bold text-dunhuang-blue/60 font-serif"
                      >
                        {{ newSp.name_zh.charAt(0) }}
                      </div>
                      <svg
                        v-else
                        class="w-8 h-8 text-dunhuang-text/30"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="1.5"
                          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                        />
                      </svg>
                    </div>
                    <div
                      class="absolute inset-0 rounded-xl bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <span class="text-white text-xs font-medium">{{
                        previewUrl ? "更换图片" : "选择图片"
                      }}</span>
                    </div>
                    <input
                      ref="fileInputRef"
                      type="file"
                      accept="image/*"
                      @change="handleImageSelect"
                      class="hidden"
                    />
                  </div>
                  <div
                    class="flex-1 text-xs text-dunhuang-text/50 space-y-1 pt-1"
                  >
                    <p>支持 JPG、PNG 格式</p>
                    <p>建议尺寸 200×200 像素</p>
                    <button
                      v-if="previewUrl"
                      type="button"
                      @click="clearImage"
                      class="text-dunhuang-red hover:text-dunhuang-red/80 transition-colors mt-1"
                    >
                      移除图片
                    </button>
                  </div>
                </div>
              </div>

              <div
                class="flex justify-end gap-3 pt-4 border-t border-dunhuang-yellow/20"
              >
                <button
                  type="submit"
                  :disabled="saving"
                  class="px-5 py-2.5 rounded-lg text-sm font-medium transition-colors bg-dunhuang-red text-white hover:bg-dunhuang-red/90 shadow-md disabled:opacity-50"
                >
                  {{ saving ? "保存中..." : "保存品种" }}
                </button>
                <button
                  type="button"
                  @click="closeAddModal"
                  class="px-5 py-2.5 rounded-lg text-sm transition-colors text-dunhuang-text/70 hover:bg-dunhuang-yellow/20 border border-dunhuang-yellow/50"
                >
                  取消
                </button>
              </div>
            </form>
          </div>
        </Transition>
      </div>
    </Transition>
    <ConfirmDialog
      :show="deleteConfirm.show"
      @cancel="deleteConfirm.show = false"
      @confirm="executeDeleteSpecies"
    >
      <template v-if="!deleteConfirm.isBatch">
        删除后将无法恢复，确认要删除该品种吗？
      </template>
      <template v-else>
        确认要删除选中的 {{ selectedIds.length }} 个品种吗？此操作无法恢复！
      </template>
    </ConfirmDialog>

    <!-- 图片放大预览弹窗 -->
    <Transition name="modal-backdrop">
      <div
        v-if="previewImageModal.show"
        class="fixed inset-0 bg-transparent flex items-center justify-center z-[80]"
        @click="previewImageModal.show = false"
      >
        <Transition name="preview-image" appear>
          <div
            v-if="previewImageModal.show"
            class="relative max-w-4xl max-h-[90vh] p-4 flex items-center justify-center"
          >
            <img
              :src="previewImageModal.url"
              class="max-w-full max-h-[85vh] rounded-lg shadow-2xl object-contain"
              @click.stop
            />
          </div>
        </Transition>
      </div>
    </Transition>

    <!-- 导入品种弹窗 -->
    <Transition name="modal-backdrop">
      <div
        v-if="showImportModal"
        class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50"
      >
        <Transition name="modal" appear>
          <div
            v-if="showImportModal"
            class="bg-white rounded-2xl shadow-2xl border border-dunhuang-yellow w-full max-w-2xl p-8 max-h-[90vh] flex flex-col"
          >
            <div
              class="flex items-center gap-3 mb-6 border-b border-dunhuang-yellow/20 pb-4 shrink-0"
            >
              <button
                @click="
                  showImportModal = false;
                  importPreview = [];
                "
                class="w-8 h-8 flex items-center justify-center rounded-full text-dunhuang-text/50 hover:text-dunhuang-blue hover:bg-dunhuang-yellow/20 transition-colors shrink-0"
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
                    d="M10 19l-7-7m0 0l7-7m-7 7h18"
                  />
                </svg>
              </button>
              <div>
                <h4 class="text-xl font-serif text-dunhuang-blue font-bold">
                  批量导入品种
                </h4>
                <p class="text-xs text-dunhuang-text/50 mt-0.5">
                  下载模板 → 填写数据 → 上传文件 → 一键导入
                </p>
              </div>
            </div>

            <!-- 未上传文件时显示指引 -->
            <div
              v-if="!importPreview.length"
              class="flex-1 flex flex-col items-center justify-center space-y-6"
            >
              <div class="flex gap-3">
                <button
                  @click="downloadSpeciesTemplate"
                  class="px-4 py-2 rounded-lg text-sm font-medium transition-colors bg-dunhuang-yellow/20 text-dunhuang-blue hover:bg-dunhuang-yellow/30 border border-dunhuang-yellow/40"
                >
                  下载导入模板
                </button>
                <div>
                  <input
                    type="file"
                    ref="speciesFileInput"
                    accept=".xlsx, .xls"
                    class="hidden"
                    @change="handleSpeciesFileUpload"
                  />
                  <button
                    @click="triggerSpeciesFileInput"
                    class="px-4 py-2 rounded-lg text-sm font-medium transition-colors bg-dunhuang-blue text-white hover:bg-dunhuang-green"
                  >
                    选择 Excel 文件
                  </button>
                </div>
              </div>
              <div class="text-center text-dunhuang-text/50 text-sm space-y-1">
                <p>模板包含字段：品种、单价（元）、放生日期</p>
                <p>支持 .xlsx / .xls 格式</p>
              </div>
            </div>

            <!-- 已解析文件时显示预览 -->
            <div v-else class="flex-1 flex flex-col min-h-0">
              <div class="mb-3 flex justify-between items-center shrink-0">
                <span class="text-sm text-dunhuang-text/70">
                  解析到
                  <span class="font-bold text-dunhuang-blue">{{
                    importPreview.length
                  }}</span>
                  个品种
                  <span v-if="overwriteCount > 0" class="ml-1">
                    (覆盖
                    <span class="font-bold text-dunhuang-red">{{
                      overwriteCount
                    }}</span>
                    项)
                  </span>
                </span>
                <button
                  @click="clearImportPreview"
                  class="text-xs text-dunhuang-text/50 hover:text-dunhuang-red transition-colors"
                >
                  重新选择
                </button>
              </div>

              <div
                class="flex-1 overflow-auto custom-scrollbar border border-dunhuang-yellow/30 rounded-lg mb-4 min-h-0"
              >
                <table
                  class="w-full text-left border-collapse whitespace-nowrap text-sm"
                >
                  <thead class="sticky top-0 bg-dunhuang-bg">
                    <tr
                      class="bg-dunhuang-yellow/20 text-dunhuang-blue font-serif"
                    >
                      <th class="px-4 py-2 border-b border-dunhuang-yellow/40">
                        品种
                      </th>
                      <th class="px-4 py-2 border-b border-dunhuang-yellow/40">
                        单价（元）
                      </th>
                      <th class="px-4 py-2 border-b border-dunhuang-yellow/40">
                        放生日期
                      </th>
                      <th class="px-4 py-2 border-b border-dunhuang-yellow/40">
                        状态
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="(row, idx) in importPreview"
                      :key="idx"
                      class="border-b border-dunhuang-yellow/20 hover:bg-dunhuang-yellow/5"
                    >
                      <td class="px-4 py-2">{{ row.name_zh }}</td>
                      <td class="px-4 py-2 tabular-nums">
                        {{ formatMoney(row.default_price) }}
                      </td>
                      <td class="px-4 py-2 text-sm">
                        {{ dateStr(row.release_date) || "-" }}
                      </td>
                      <td class="px-4 py-2">
                        <button
                          v-if="row.exists"
                          @click="row.overwrite = !row.overwrite"
                          :class="[
                            'text-xs px-2 py-0.5 rounded cursor-pointer transition-colors',
                            row.overwrite
                              ? 'bg-dunhuang-red/10 text-dunhuang-red hover:bg-dunhuang-red/20'
                              : 'bg-dunhuang-yellow/20 text-dunhuang-blue hover:bg-dunhuang-yellow/30',
                          ]"
                        >
                          {{ row.overwrite ? "覆盖" : "跳过" }}
                        </button>
                        <span
                          v-else
                          class="text-xs bg-dunhuang-green/10 text-dunhuang-green px-2 py-0.5 rounded"
                          >待新建</span
                        >
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div class="flex justify-end gap-3 shrink-0">
                <button
                  @click="clearImportPreview"
                  class="px-5 py-2 rounded-lg text-sm transition-colors text-dunhuang-text/70 hover:bg-dunhuang-yellow/20 border border-dunhuang-yellow/50"
                >
                  取消
                </button>
                <button
                  @click="confirmImportSpecies"
                  :disabled="importing"
                  class="px-5 py-2 rounded-lg text-sm font-medium transition-colors bg-dunhuang-red text-white hover:bg-dunhuang-red/90 disabled:opacity-50"
                >
                  {{
                    importing
                      ? "导入中..."
                      : `确认导入 ${importPreview.length} 项`
                  }}
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, shallowRef, computed } from "vue";
import { useRouter } from "vue-router";
import * as XLSX from "xlsx";
import api from "../api";
import { apiErrorMessage, isAuthError } from "../lib/error";
import {
  formatMoney,
  dateStr,
  compressImage,
  isPackagingItem,
} from "../lib/utils";
import { useToast } from "../composables/useToast";
import { useSpecies } from "../composables/useSpecies";
import ConfirmDialog from "../components/ConfirmDialog.vue";
import DateInput from "../components/DateInput.vue";
import Pagination from "../components/Pagination.vue";
import SearchInput from "../components/SearchInput.vue";
import { useAuthStore } from "../stores/auth";

// ============================================================
//  品种管理：列表 + 新增 + 批量删除 + 分页
// ============================================================

interface SpeciesItem {
  id: number;
  name_zh: string;
  default_unit: string;
  default_price: number;
  image_url?: string | null;
  release_date?: string | null;
  created_at?: string | null;
}

const router = useRouter();
const authStore = useAuthStore();
const toast = useToast();
const { invalidateCache } = useSpecies();

const species = shallowRef<SpeciesItem[]>([]);
const selectedIds = ref<number[]>([]);
const showAddModal = ref(false);
const errorMsg = ref("");
const speciesSearch = ref("");
const speciesSearchText = ref("");

const currentPage = ref(1);
const pageSize = ref(10);

const displaySpecies = computed(() => {
  return species.value.filter((sp) => !isPackagingItem(sp.name_zh));
});

const totalItems = computed(() => displaySpecies.value.length);
const totalPages = computed(() => Math.ceil(totalItems.value / pageSize.value));

const paginatedSpecies = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  const end = start + pageSize.value;
  return displaySpecies.value.slice(start, end);
});

const deleteConfirm = ref({
  show: false,
  id: null as number | null,
  isBatch: false,
});

const previewImageModal = ref({
  show: false,
  url: "",
});

const openImagePreview = (url: string) => {
  previewImageModal.value = {
    show: true,
    url,
  };
};

const isAllSelected = computed(() => {
  return (
    displaySpecies.value.length > 0 &&
    selectedIds.value.length === displaySpecies.value.length
  );
});

const toggleAll = (e: Event) => {
  const checked = (e.target as HTMLInputElement).checked;
  if (checked) {
    selectedIds.value = displaySpecies.value.map((sp) => sp.id);
  } else {
    selectedIds.value = [];
  }
};
const saving = ref(false);

const newSp = ref({
  name_zh: "",
  default_unit: "公斤",
  default_price: "0.00",
  image_url: null as string | null,
  release_date: "",
});

const selectedFile = ref<File | null>(null);
const previewUrl = ref<string | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);

const unitOptions = ["公斤", "只"];

const triggerFileInput = () => {
  fileInputRef.value?.click();
};

const clearImage = () => {
  selectedFile.value = null;
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
  }
  previewUrl.value = null;
  if (fileInputRef.value) {
    fileInputRef.value.value = "";
  }
};

const handleImageSelect = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) {
    selectedFile.value = null;
    previewUrl.value = null;
    return;
  }

  // 如果文件大于 1MB，进行压缩
  if (file.size > 1024 * 1024) {
    try {
      const compressedBlob = await compressImage(file, 1024, 1024, 0.7);
      const compressedFile = new File([compressedBlob], file.name, {
        type: "image/jpeg",
      });
      selectedFile.value = compressedFile;
      previewUrl.value = URL.createObjectURL(compressedFile);
    } catch (err) {
      console.error("Image compression failed", err);
      selectedFile.value = file;
      previewUrl.value = URL.createObjectURL(file);
    }
  } else {
    selectedFile.value = file;
    previewUrl.value = URL.createObjectURL(file);
  }
};

const closeAddModal = () => {
  showAddModal.value = false;
  newSp.value = {
    name_zh: "",
    default_unit: "公斤",
    default_price: "0.00",
    image_url: null,
    release_date: "",
  };
  selectedFile.value = null;
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value);
  }
  previewUrl.value = null;
  if (fileInputRef.value) {
    fileInputRef.value.value = "";
  }
};

const fetchSpecies = async () => {
  errorMsg.value = "";
  try {
    const params = new URLSearchParams();
    const q = speciesSearch.value.trim();
    if (q) params.set("q", q);
    const url = params.toString()
      ? `/species?${params.toString()}`
      : "/species";
    const res = await api.get(url);
    species.value = Array.isArray(res.data) ? res.data : [];
  } catch (error: any) {
    if (isAuthError(error)) return;
    console.error("Failed to fetch species", error);
    errorMsg.value = apiErrorMessage(error, "加载品种列表");
  }
};

const handleSearch = () => {
  currentPage.value = 1;
  speciesSearch.value = speciesSearchText.value.trim();
  fetchSpecies();
};

const handleClearSearch = () => {
  speciesSearch.value = "";
  speciesSearchText.value = "";
  currentPage.value = 1;
  fetchSpecies();
};

const addSpecies = async () => {
  const name = newSp.value.name_zh.trim();
  if (!name) {
    errorMsg.value = "请输入品种名称";
    return;
  }
  if (+newSp.value.default_price <= 0) {
    errorMsg.value = "单价必须大于0";
    return;
  }
  if (!newSp.value.release_date) {
    errorMsg.value = "请选择放生日期";
    return;
  }
  if (species.value.some((s) => s.name_zh === name)) {
    errorMsg.value = `品种「${name}」已存在，请勿重复添加`;
    return;
  }
  saving.value = true;
  try {
    // 1. Create species first
    const res = await api.post("/species", {
      ...newSp.value,
      default_price: Number(newSp.value.default_price),
    });
    const createdSpecies = res.data;

    // 2. Upload image if selected
    if (selectedFile.value) {
      const formData = new FormData();
      formData.append("image", selectedFile.value);
      await api.post(`/species/${createdSpecies.id}/image`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
    }

    closeAddModal();
    await invalidateCache();
  } catch (error: any) {
    if (isAuthError(error)) return;
    errorMsg.value = apiErrorMessage(error, "保存品种");
  } finally {
    saving.value = false;
  }
};

const openDetail = (id: number, edit = false) => {
  router.push({
    name: "SpeciesDetail",
    params: { id },
    query: edit ? { mode: "edit" } : undefined,
  });
};

const confirmRemoveSpecies = (id: number) => {
  deleteConfirm.value = { show: true, id, isBatch: false };
};

const confirmBatchRemoveSpecies = () => {
  if (selectedIds.value.length === 0) return;
  deleteConfirm.value = { show: true, id: null, isBatch: true };
};

const executeDeleteSpecies = async () => {
  if (deleteConfirm.value.isBatch) {
    try {
      for (const id of selectedIds.value) {
        await api.delete(`/species/${id}`);
      }
      selectedIds.value = [];
      deleteConfirm.value.show = false;
      await invalidateCache();
    } catch (error: any) {
      if (isAuthError(error)) return;
      errorMsg.value = apiErrorMessage(error, "批量删除");
      deleteConfirm.value.show = false;
      await invalidateCache();
    }
  } else {
    const id = deleteConfirm.value.id;
    if (!id) return;
    try {
      await api.delete(`/species/${id}`);
      selectedIds.value = selectedIds.value.filter(
        (selectedId) => selectedId !== id,
      );
      deleteConfirm.value.show = false;
      await invalidateCache();
    } catch (error: any) {
      if (isAuthError(error)) return;
      errorMsg.value = apiErrorMessage(error, "删除品种");
      deleteConfirm.value.show = false;
    }
  }
};

// ============================================================
//  批量导入品种
// ============================================================

interface ImportRow {
  name_zh: string;
  default_price: number;
  default_unit: string;
  exists: boolean;
  species_id: number | null;
  overwrite: boolean;
  release_date?: string | null;
}

const showImportModal = ref(false);
const speciesFileInput = ref<HTMLInputElement | null>(null);
const importPreview = ref<ImportRow[]>([]);
const importing = ref(false);

const overwriteCount = computed(
  () => importPreview.value.filter((r) => r.exists && r.overwrite).length,
);

const triggerSpeciesFileInput = () => {
  if (speciesFileInput.value) {
    speciesFileInput.value.value = "";
    speciesFileInput.value.click();
  }
};

const downloadSpeciesTemplate = () => {
  const templateData = [
    { 品种: "草鱼", "单价（元）": 12.5, 放生日期: "2025-01-15" },
    { 品种: "鲈鱼", "单价（元）": 25.0, 放生日期: "2025-01-15" },
  ];
  const worksheet = XLSX.utils.json_to_sheet(templateData);
  worksheet["!cols"] = [{ wch: 15 }, { wch: 12 }, { wch: 14 }];
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "品种导入模板");
  XLSX.writeFile(workbook, "品种导入模板.xlsx");
};

const handleSpeciesFileUpload = (event: Event) => {
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
      const jsonData = XLSX.utils.sheet_to_json(worksheet) as any[];

      const seen = new Set<string>();

      importPreview.value = jsonData
        .map((row: any) => {
          const nameZh = String(row["品种"] || row["名称"] || "").trim();
          const rawPrice =
            row["单价（元）"] ??
            row["单价"] ??
            row["单价 (¥)"] ??
            row["单价(¥)"] ??
            row["默认单价"] ??
            0;
          const price =
            parseFloat(String(rawPrice).replace(/[^\d.]/g, "")) || 0;

          const release_date = row["放生日期"] || row["日期"] || "";

          if (seen.has(nameZh)) return null;
          seen.add(nameZh);

          const existsInDb = species.value.some((s) => s.name_zh === nameZh);
          const existing = existsInDb
            ? (species.value.find((s) => s.name_zh === nameZh) ?? null)
            : null;

          return {
            name_zh: nameZh,
            default_price: Number(price.toFixed(2)),
            default_unit: "公斤",
            exists: existsInDb,
            species_id: existing ? existing.id : null,
            overwrite: false,
            release_date: release_date ? String(release_date).trim() : "",
          };
        })
        .filter((r) => r && r.name_zh && r.default_price > 0);

      if (importPreview.value.length === 0) {
        toast.warning("未能解析到有效数据，请确认文件格式与模板一致。");
      }
    } catch (err) {
      console.error("Parse species Excel failed", err);
      toast.error("解析 Excel 失败，请检查文件格式是否正确。");
    }
  };
  reader.readAsArrayBuffer(file);
};

const clearImportPreview = () => {
  importPreview.value = [];
};

const confirmImportSpecies = async () => {
  if (importPreview.value.length === 0) return;
  importing.value = true;
  try {
    let created = 0;
    let updated = 0;
    let skipped = 0;

    for (const row of importPreview.value) {
      if (row.exists && row.overwrite && row.species_id) {
        await api.put(`/species/${row.species_id}`, {
          name_zh: row.name_zh,
          default_price: row.default_price,
          default_unit: row.default_unit,
          release_date: row.release_date || null,
        });
        updated++;
      } else if (row.exists) {
        skipped++;
      } else {
        await api.post("/species", {
          name_zh: row.name_zh,
          default_price: row.default_price,
          default_unit: row.default_unit,
          release_date: row.release_date || null,
        });
        created++;
      }
    }

    const parts = [`成功导入 ${created + updated} 个品种`];
    if (created > 0) parts.push(`新建 ${created} 个`);
    if (updated > 0) parts.push(`覆盖 ${updated} 个`);
    if (skipped > 0) parts.push(`跳过 ${skipped} 个`);
    toast.success(parts.join("，"));

    importPreview.value = [];
    showImportModal.value = false;
    await invalidateCache();
  } catch (error: any) {
    if (isAuthError(error)) return;
    errorMsg.value = apiErrorMessage(error, "导入品种");
  } finally {
    importing.value = false;
  }
};

onMounted(fetchSpecies);
</script>
