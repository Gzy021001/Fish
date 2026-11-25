<template>
  <div class="h-full flex flex-col min-h-0">
    <div
      class="bg-white rounded-2xl shadow-md border border-dunhuang-yellow/30 p-4 sm:p-6 relative flex-1 flex flex-col min-h-0"
    >
      <Transition name="fade">
        <div
          v-if="errorMsg"
          class="absolute top-4 left-1/2 -translate-x-1/2 z-50 max-w-md w-auto px-5 py-2.5 bg-dunhuang-red/95 text-white rounded-lg text-sm shadow-lg backdrop-blur"
        >
          {{ errorMsg }}
        </div>
      </Transition>

      <!-- 工具栏 -->
      <div class="flex flex-wrap items-center justify-between gap-3 shrink-0 mb-3">
        <SearchInput
          v-model="speciesSearchText"
          placeholder="搜索品种..."
          @search="handleSearch"
          @clear="handleClearSearch"
        />
        <div class="flex flex-wrap items-center gap-2">
          <button
            v-if="selectedIds.length > 0"
            @click="exportSpecies"
            :disabled="exportingSpecies"
            class="h-9 px-4 rounded-lg text-sm font-medium transition-colors bg-dunhuang-blue/8 text-dunhuang-blue border border-dunhuang-blue/25 hover:bg-dunhuang-blue/15 disabled:opacity-50"
          >
            批量导出 ({{ selectedIds.length }})
          </button>
          <button
            v-if="selectedIds.length > 0 && authStore.isAdmin"
            @click="confirmBatchRemoveSpecies"
            class="h-9 px-4 rounded-lg text-sm font-medium transition-colors text-dunhuang-red bg-dunhuang-red/8 border border-dunhuang-red/25 hover:bg-dunhuang-red/15"
          >
            批量删除 ({{ selectedIds.length }})
          </button>
          <button
            @click="exportSpecies"
            :disabled="exportingSpecies"
            class="h-9 px-4 rounded-lg text-sm font-medium transition-colors text-dunhuang-blue/80 bg-white border border-dunhuang-blue/20 hover:text-dunhuang-blue hover:bg-dunhuang-blue/6 disabled:opacity-50"
          >
            导出
          </button>
          <button
            v-if="authStore.isAdmin"
            @click="showAddModal = true"
            class="h-9 px-4 rounded-lg text-sm font-semibold transition-colors bg-dunhuang-blue text-white hover:bg-dunhuang-blue/90 shadow-sm"
          >
            新增品种
          </button>
        </div>
      </div>

      <!-- 品种列表：表头固定，行数多时表格内部滚动，操作列固定在右侧 -->
      <div
        class="flex-1 min-h-0 rounded-lg border border-dunhuang-yellow/30 overflow-hidden flex flex-col"
      >
        <div
          class="shrink-0 grid species-grid h-11 bg-[#f7f0e2] text-dunhuang-blue font-sans font-bold text-sm border-b border-dunhuang-yellow/40"
          :style="{ paddingRight: bodyGutter + 'px' }"
        >
          <div class="px-3 flex items-center justify-center">
            <input
              type="checkbox"
              :checked="isAllSelected"
              @change="toggleAll"
              class="custom-checkbox text-dunhuang-red focus-visible:ring-2 focus-visible:ring-dunhuang-red/30 focus-visible:ring-offset-1 outline-none"
            />
          </div>
          <div class="px-3 flex items-center justify-center whitespace-nowrap">
            序号
          </div>
          <div class="px-3 flex items-center justify-center whitespace-nowrap">
            品种
          </div>
          <div
            class="px-3 flex items-center justify-center whitespace-nowrap"
            title="该品种最近一次有单据的放生日期（最近一周的放生日）"
          >
            放生日期
          </div>
          <div class="px-3 flex items-center justify-center whitespace-nowrap">
            单价（元/斤）
          </div>
          <div class="px-3 flex items-center justify-center whitespace-nowrap">
            单位
          </div>
          <div class="px-3 flex items-center justify-center whitespace-nowrap">
            照片
          </div>
          <div class="px-3 flex items-center justify-center whitespace-nowrap">
            备注
          </div>
          <div
            class="sticky right-0 z-20 px-3 flex items-center justify-center whitespace-nowrap bg-[#f7f0e2] border-l border-dunhuang-yellow/25"
            :class="
              bodyScrollsX
                ? 'shadow-[-8px_0_8px_-8px_rgba(74,52,40,0.22)]'
                : ''
            "
          >
            操作
          </div>
        </div>

        <div
          ref="rowsBodyRef"
          class="species-rows panel-scrollbar flex flex-col flex-1 min-h-0 overflow-auto"
        >
          <div
            v-for="(sp, index) in paginatedSpecies"
            :key="sp.id"
            class="grid species-grid h-11 shrink-0 text-sm border-b border-dunhuang-yellow/15 transition-colors"
            :class="
              index % 2 === 1
                ? 'bg-[#fcfaf3] hover:bg-[#f7f1e2]'
                : 'bg-white hover:bg-[#fdf9f0]'
            "
          >
            <div class="px-3 flex items-center justify-center">
              <input
                type="checkbox"
                v-model="selectedIds"
                :value="sp.id"
                class="custom-checkbox text-dunhuang-red focus-visible:ring-2 focus-visible:ring-dunhuang-red/30 focus-visible:ring-offset-1 outline-none"
              />
            </div>
            <div
              class="px-3 flex items-center justify-center text-dunhuang-text/60 tabular-nums"
            >
              {{ (currentPage - 1) * pageSize + index + 1 }}
            </div>
            <div
              class="px-3 flex items-center justify-center font-medium text-dunhuang-text min-w-0"
              :title="sp.name_zh"
            >
              <span class="truncate">{{ sp.name_zh }}</span>
            </div>
            <div
              class="px-3 flex items-center justify-center text-dunhuang-text/70 whitespace-nowrap tabular-nums"
            >
              {{ dateStr(sp.last_release_date) || "—" }}
            </div>
            <div class="px-3 flex items-center justify-center">
              <input
                v-if="editingPriceId === sp.id"
                v-model="editingPrice"
                type="text"
                inputmode="decimal"
                class="price-edit-input w-24 h-8 px-2 rounded-lg border border-dunhuang-blue/40 bg-white text-center tabular-nums text-sm outline-none focus:ring-2 focus:ring-dunhuang-blue/20"
                :disabled="savingPrice"
                @click.stop
                @keydown.enter.prevent="savePrice(sp)"
                @keydown.esc.prevent="cancelEditPrice"
                @blur="savePrice(sp)"
              />
              <button
                v-else
                type="button"
                class="tabular-nums text-dunhuang-red rounded px-1.5 py-0.5 transition-colors"
                :class="
                  authStore.isAdmin
                    ? 'hover:bg-dunhuang-red/10 cursor-pointer'
                    : 'cursor-default'
                "
                :title="authStore.isAdmin ? '点击修改单价' : ''"
                @click="startEditPrice(sp)"
              >
                {{ formatMoney(toJinPrice(sp.default_price)) }}
              </button>
            </div>
            <div
              class="px-3 flex items-center justify-center text-dunhuang-text/60"
            >
              {{ sp.default_unit }}
            </div>
            <div class="px-3 flex items-center justify-center">
              <button
                type="button"
                class="species-photo-btn relative h-8 w-8 rounded-md overflow-hidden transition-colors group"
                :class="
                  authStore.isAdmin
                    ? 'cursor-pointer hover:ring-2 hover:ring-dunhuang-blue/30'
                    : 'cursor-default'
                "
                :title="
                  authStore.isAdmin
                    ? sp.image_url
                      ? '点击更换照片'
                      : '点击上传照片'
                    : sp.image_url
                      ? sp.name_zh
                      : '暂无照片'
                "
                :disabled="uploadingPhotoId === sp.id"
                @click.stop="pickPhoto(sp)"
              >
                <img
                  v-if="sp.image_url"
                  :src="sp.image_url"
                  alt=""
                  class="h-8 w-8 rounded-md object-cover border border-dunhuang-yellow/30"
                />
                <span
                  v-else
                  class="h-8 w-8 rounded-md border border-dashed border-dunhuang-yellow/40 bg-[#faf6ec] flex items-center justify-center text-dunhuang-text/20"
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
                  >
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                    <circle cx="8.5" cy="8.5" r="1.5" />
                    <polyline points="21 15 16 10 5 21" />
                  </svg>
                </span>
                <span
                  v-if="uploadingPhotoId === sp.id"
                  class="absolute inset-0 bg-white/70 flex items-center justify-center"
                >
                  <span
                    class="h-3 w-3 rounded-full border-2 border-dunhuang-blue/70 border-t-transparent animate-spin"
                  ></span>
                </span>
              </button>
            </div>
            <div
              class="px-3 flex items-center justify-center text-dunhuang-text/60 min-w-0"
              :title="sp.supplier_note || ''"
            >
              <span class="truncate">{{ sp.supplier_note || "—" }}</span>
            </div>
            <div
              class="sticky right-0 bg-inherit px-3 flex items-center justify-center border-l border-dunhuang-yellow/20"
              :class="
                bodyScrollsX
                  ? 'shadow-[-8px_0_8px_-8px_rgba(74,52,40,0.16)]'
                  : ''
              "
            >
              <button
                v-if="authStore.isAdmin"
                @click="openEditModal(sp)"
                class="px-2 py-1 rounded text-xs whitespace-nowrap transition-colors text-dunhuang-blue hover:bg-dunhuang-blue/10 border border-transparent hover:border-dunhuang-blue/30"
              >
                编辑
              </button>
              <button
                v-if="authStore.isAdmin"
                @click="confirmRemoveSpecies(sp.id)"
                class="px-2 py-1 rounded text-xs whitespace-nowrap transition-colors text-dunhuang-red hover:bg-dunhuang-red/10 border border-transparent hover:border-dunhuang-red/30"
              >
                删除
              </button>
              <span v-else class="text-dunhuang-text/25">—</span>
            </div>
          </div>

          <div
            v-if="species.length === 0 && !errorMsg"
            class="py-12 text-center text-sm text-dunhuang-text/40"
          >
            暂未录入品种数据
          </div>

          <!-- 表格剩余空间的装饰：点阵底纹 + 水波纹，避免大片留白 -->
          <div
            v-else
            class="species-tail flex-1 min-h-0 flex flex-col items-center justify-center gap-2 select-none overflow-hidden bg-[radial-gradient(circle,rgba(191,160,95,0.13)_1px,transparent_1px)] [background-size:18px_18px]"
          >
            <svg
              class="w-20 h-4 shrink-0 text-dunhuang-yellow/45"
              viewBox="0 0 80 16"
              fill="none"
              stroke="currentColor"
              stroke-width="1.3"
              stroke-linecap="round"
            >
              <path d="M2 8q9-8 18 0t18 0 18 0 18 0" />
            </svg>
            <p
              class="text-[11px] tracking-[0.28em] text-dunhuang-text/30 shrink-0 whitespace-nowrap"
            >
              本页 {{ paginatedSpecies.length }} 个品种
            </p>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div
        class="shrink-0 flex justify-between items-center flex-wrap gap-3 mt-3"
      >
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

      <!-- 列表内点击照片上传用的隐藏文件框 -->
      <input
        ref="photoInputRef"
        type="file"
        accept="image/*"
        class="hidden"
        @change="handlePhotoPicked"
      />
    </div>

    <!-- 新增品种弹窗 -->
    <Transition name="modal-backdrop">
      <div
        v-if="showAddModal"
        class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50"
      >
        <Transition name="modal" appear>
          <div
            v-if="showAddModal"
            class="bg-white rounded-2xl shadow-2xl border border-dunhuang-yellow w-full max-w-lg p-4 sm:p-8 max-h-[90vh] overflow-y-auto panel-scrollbar"
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
                    >单价（元/斤）</label
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
                    >单位</label
                  >
                  <div class="grid grid-cols-3 gap-2">
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
                  class="h-10 px-5 rounded-lg text-sm font-medium transition-colors bg-dunhuang-red text-white hover:bg-dunhuang-red/90 shadow-md disabled:opacity-50"
                >
                  {{ saving ? "保存中..." : "保存品种" }}
                </button>
                <button
                  type="button"
                  @click="closeAddModal"
                  class="h-10 px-5 rounded-lg text-sm transition-colors text-dunhuang-text/70 hover:bg-dunhuang-yellow/20 border border-dunhuang-yellow/50"
                >
                  取消
                </button>
              </div>
            </form>
          </div>
        </Transition>
      </div>
    </Transition>

    <!-- 编辑品种弹窗 -->
    <Transition name="modal-backdrop">
      <div
        v-if="showEditModal"
        class="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50 px-4"
        @click.self="closeEditModal"
      >
        <Transition name="modal" appear>
          <form
            v-if="showEditModal"
            @submit.prevent="saveEditSpecies"
            class="bg-white rounded-2xl shadow-2xl border border-dunhuang-yellow w-full max-w-lg p-5 sm:p-6 max-h-[90vh] overflow-y-auto panel-scrollbar"
          >
            <div
              class="flex items-center justify-between gap-3 mb-4 pb-3 border-b border-dunhuang-yellow/20"
            >
              <div class="min-w-0">
                <h4 class="text-lg font-serif text-dunhuang-blue font-bold">
                  编辑品种
                </h4>
                <p class="text-xs text-dunhuang-text/45 mt-0.5 truncate">
                  {{ editTarget?.name_zh }}
                </p>
              </div>
              <button
                type="button"
                @click="closeEditModal"
                class="w-8 h-8 shrink-0 rounded-lg flex items-center justify-center text-dunhuang-text/35 hover:text-dunhuang-red hover:bg-dunhuang-red/10 transition-colors"
                title="关闭"
              >
                <svg
                  class="w-4 h-4"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>

            <div class="flex items-start gap-5">
              <!-- 照片 -->
              <div class="shrink-0">
                <div
                  class="relative w-24 h-24 rounded-xl border-2 border-dashed cursor-pointer group overflow-hidden transition-colors"
                  :class="
                    editPreviewUrl || editTarget?.image_url
                      ? 'border-dunhuang-blue/40'
                      : 'border-dunhuang-yellow/40 hover:border-dunhuang-blue/50 bg-dunhuang-bg'
                  "
                  @click="triggerEditFileInput"
                >
                  <img
                    v-if="editPreviewUrl || editTarget?.image_url"
                    :src="editPreviewUrl || editTarget?.image_url || ''"
                    alt=""
                    class="w-full h-full object-cover"
                  />
                  <div
                    v-else
                    class="w-full h-full flex items-center justify-center text-2xl font-bold text-dunhuang-blue/40 font-serif"
                  >
                    {{ editForm.name_zh.charAt(0) || "?" }}
                  </div>
                  <div
                    class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <span class="text-white text-xs font-medium">{{
                      editPreviewUrl || editTarget?.image_url
                        ? "更换照片"
                        : "上传照片"
                    }}</span>
                  </div>
                </div>
                <input
                  ref="editFileInputRef"
                  type="file"
                  accept="image/*"
                  class="hidden"
                  @change="handleEditImageSelect"
                />
              </div>

              <!-- 名称 / 单价 / 单位 -->
              <div class="flex-1 min-w-0 space-y-3">
                <div>
                  <label
                    class="block text-xs font-medium text-dunhuang-text/60 mb-1.5"
                    >品种名称</label
                  >
                  <input
                    v-model="editForm.name_zh"
                    type="text"
                    placeholder="品种名称"
                    class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2 px-3 text-sm outline-none focus:ring-0 focus:border-dunhuang-blue/50"
                  />
                </div>
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label
                      class="block text-xs font-medium text-dunhuang-text/60 mb-1.5"
                      >单价（元/斤）</label
                    >
                    <input
                      v-model="editForm.default_price"
                      type="text"
                      inputmode="decimal"
                      @blur="
                        editForm.default_price = (
                          Number(editForm.default_price) || 0
                        ).toFixed(2)
                      "
                      class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2 px-3 text-sm outline-none focus:ring-0 focus:border-dunhuang-blue/50 tabular-nums"
                    />
                  </div>
                  <div>
                    <label
                      class="block text-xs font-medium text-dunhuang-text/60 mb-1.5"
                      >单位</label
                    >
                    <input
                      v-model="editForm.default_unit"
                      type="text"
                      placeholder="斤 / 只"
                      class="w-full bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2 px-3 text-sm outline-none focus:ring-0 focus:border-dunhuang-blue/50"
                    />
                  </div>
                </div>
                <div class="flex items-center gap-1.5">
                  <button
                    v-for="unit in unitOptions"
                    :key="unit"
                    type="button"
                    @click="editForm.default_unit = unit"
                    :class="[
                      'px-2.5 py-1 rounded-md text-xs font-medium border transition-colors',
                      editForm.default_unit === unit
                        ? 'border-dunhuang-blue bg-dunhuang-blue/10 text-dunhuang-blue'
                        : 'border-dunhuang-yellow/40 text-dunhuang-text/50 hover:border-dunhuang-blue/40 hover:text-dunhuang-blue',
                    ]"
                  >
                    {{ unit }}
                  </button>
                </div>
              </div>
            </div>

            <div class="mt-4">
              <label class="block text-xs font-medium text-dunhuang-text/60 mb-1.5"
                >备注</label
              >
              <textarea
                v-model="editForm.supplier_note"
                rows="2"
                placeholder="例如：常驻供应商 / 暂不售卖 / 规格说明"
                class="w-full resize-none bg-dunhuang-bg border border-dunhuang-yellow/50 rounded-lg py-2 px-3 text-sm outline-none focus:ring-0 focus:border-dunhuang-blue/50"
              ></textarea>
            </div>

            <p class="text-[11px] text-dunhuang-text/40 mt-3">
              最近放生
              {{ dateStr(editTarget?.last_release_date) || "—" }}
            </p>

            <p v-if="editFormError" class="text-xs text-dunhuang-red mt-2">
              {{ editFormError }}
            </p>

            <div
              class="flex justify-end gap-3 mt-4 pt-4 border-t border-dunhuang-yellow/20"
            >
              <button
                type="button"
                @click="closeEditModal"
                class="h-10 px-5 rounded-lg text-sm transition-colors text-dunhuang-text/70 hover:bg-dunhuang-yellow/20 border border-dunhuang-yellow/50"
              >
                取消
              </button>
              <button
                type="submit"
                :disabled="editSaving"
                class="h-10 px-5 rounded-lg text-sm font-medium transition-colors bg-dunhuang-blue text-white hover:bg-dunhuang-blue/90 shadow-md disabled:opacity-50"
              >
                {{ editSaving ? "保存中..." : "保存" }}
              </button>
            </div>
          </form>
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
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, shallowRef, computed, watch, nextTick } from "vue";
import api from "../api";
import { apiErrorMessage, isAuthError } from "../lib/error";
import {
  formatMoney,
  compressImage,
  dateStr,
  toJinPrice,
  toPerKgPrice,
} from "../lib/utils";
import { useToast } from "../composables/useToast";
import { useSpecies } from "../composables/useSpecies";
import ConfirmDialog from "../components/ConfirmDialog.vue";
import DateInput from "../components/DateInput.vue";
import Pagination from "../components/Pagination.vue";
import SearchInput from "../components/SearchInput.vue";
import { useAuthStore } from "../stores/auth";

// ============================================================
//  品种库：列表 + 新增 + 批量删除 + 分页（品种由开单/导入自动入库，这里只做维护）
// ============================================================

interface SpeciesItem {
  id: number;
  name_zh: string;
  default_unit: string;
  default_price: number;
  image_url?: string | null;
  supplier_name?: string | null;
  supplier_note?: string | null;
  release_date?: string | null;
  created_at?: string | null;
  /** 列表接口附带：最近一次有单据的放生日期（没有单据时回退品种自身放生日期） */
  last_release_date?: string | null;
}

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

// 服务端分页：总数以后端 X-Total-Count 为准，翻页/改条数触发重新拉取
const totalItems = ref(0);
const totalPages = computed(() => Math.ceil(totalItems.value / pageSize.value));

watch(currentPage, () => {
  fetchSpecies();
});

watch(pageSize, () => {
  if (currentPage.value !== 1) {
    currentPage.value = 1; // watch(currentPage) 统一拉取
  } else {
    fetchSpecies();
  }
});

// 删除后当前页可能越界：自动回退到最后一页（watch(currentPage) 会重新拉取）
watch(totalPages, (t) => {
  if (t > 0 && currentPage.value > t) {
    currentPage.value = t;
  }
});

const paginatedSpecies = computed(() => species.value);

// 表格是否横向溢出：只有真溢出时才给固定列加阴影，否则那道阴影会变成一条多余的竖线
const rowsBodyRef = ref<HTMLElement | null>(null);
const bodyScrollsX = ref(false);
// 表体预留的滚动条宽度：表头要补同样的右侧留白，列才能和数据行对齐
const bodyGutter = ref(0);
let rowsObserver: ResizeObserver | null = null;

// ===== 行内改单价：点价格进入编辑，回车/失焦保存，Esc 取消 =====
const editingPriceId = ref<number | null>(null);
const editingPrice = ref("");
const savingPrice = ref(false);

const startEditPrice = (sp: SpeciesItem) => {
  if (!authStore.isAdmin) return;
  editingPriceId.value = sp.id;
  editingPrice.value = toJinPrice(sp.default_price ?? 0).toFixed(2);
  nextTick(() => {
    const el = document.querySelector<HTMLInputElement>(".price-edit-input");
    el?.focus();
    el?.select();
  });
};

const cancelEditPrice = () => {
  editingPriceId.value = null;
  editingPrice.value = "";
};

// ===== 编辑弹窗：名称 / 单价 / 单位 / 备注 / 照片 =====
const showEditModal = ref(false);
const editSaving = ref(false);
const editFormError = ref("");
const editTarget = ref<SpeciesItem | null>(null);
const editForm = ref({
  name_zh: "",
  default_unit: "斤",
  default_price: "0.00",
  supplier_note: "",
});
const editPhotoFile = ref<Blob | null>(null);
const editPreviewUrl = ref<string | null>(null);
const editFileInputRef = ref<HTMLInputElement | null>(null);

const todayIso = () => {
  const t = new Date();
  return `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, "0")}-${String(t.getDate()).padStart(2, "0")}`;
};

const openEditModal = (sp: SpeciesItem) => {
  if (!authStore.isAdmin) return;
  editTarget.value = sp;
  editForm.value = {
    name_zh: sp.name_zh,
    default_unit: sp.default_unit || "斤",
    default_price: toJinPrice(sp.default_price ?? 0).toFixed(2),
    supplier_note: sp.supplier_note || "",
  };
  editPhotoFile.value = null;
  if (editPreviewUrl.value) URL.revokeObjectURL(editPreviewUrl.value);
  editPreviewUrl.value = null;
  editFormError.value = "";
  showEditModal.value = true;
};

const closeEditModal = () => {
  showEditModal.value = false;
  editTarget.value = null;
  if (editPreviewUrl.value) {
    URL.revokeObjectURL(editPreviewUrl.value);
    editPreviewUrl.value = null;
  }
  editPhotoFile.value = null;
};

const triggerEditFileInput = () => editFileInputRef.value?.click();

const handleEditImageSelect = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  let picked: Blob = file;
  if (file.size > 1024 * 1024) {
    try {
      picked = await compressImage(file, 1024, 1024, 0.7);
    } catch (compressError) {
      console.error("Image compression failed", compressError);
    }
  }
  editPhotoFile.value = picked;
  if (editPreviewUrl.value) URL.revokeObjectURL(editPreviewUrl.value);
  editPreviewUrl.value = URL.createObjectURL(picked);
};

const saveEditSpecies = async () => {
  const sp = editTarget.value;
  if (!sp || editSaving.value) return;
  const name = editForm.value.name_zh.trim();
  const unit = editForm.value.default_unit.trim();
  const price = Number(editForm.value.default_price);
  if (!name) {
    editFormError.value = "请填写品种名称";
    return;
  }
  if (!Number.isFinite(price) || price <= 0) {
    editFormError.value = "单价必须大于0";
    return;
  }
  if (!unit) {
    editFormError.value = "请填写单位";
    return;
  }

  editSaving.value = true;
  editFormError.value = "";
  try {
    // 后端 PUT 是整行覆盖：未在弹窗里出现的字段原样带回，避免被清空
    await api.put(`/species/${sp.id}`, {
      name_zh: name,
      default_unit: unit,
      default_price: toPerKgPrice(price),
      release_date: sp.release_date || sp.last_release_date || todayIso(),
      supplier_name: sp.supplier_name ?? null,
      supplier_note: editForm.value.supplier_note.trim() || null,
    });

    if (editPhotoFile.value) {
      const formData = new FormData();
      formData.append("image", editPhotoFile.value, "species.jpg");
      await api.post(`/species/${sp.id}/image`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
    }

    closeEditModal();
    await fetchSpecies();
    toast.success("品种已更新");
  } catch (error: any) {
    if (isAuthError(error)) return;
    console.error("Failed to update species", error);
    editFormError.value = apiErrorMessage(error, "保存品种");
  } finally {
    editSaving.value = false;
  }
};

// ===== 列表内点击照片上传：点缩略图/占位框选图，压缩后走 /species/{id}/image =====
const photoInputRef = ref<HTMLInputElement | null>(null);
const photoTargetId = ref<number | null>(null);
const uploadingPhotoId = ref<number | null>(null);

const pickPhoto = (sp: SpeciesItem) => {
  if (!authStore.isAdmin || uploadingPhotoId.value === sp.id) return;
  photoTargetId.value = sp.id;
  photoInputRef.value?.click();
};

const handlePhotoPicked = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = "";
  const targetId = photoTargetId.value;
  if (!file || !targetId) return;

  uploadingPhotoId.value = targetId;
  try {
    let payload: Blob = file;
    if (file.size > 1024 * 1024) {
      try {
        payload = await compressImage(file, 1024, 1024, 0.7);
      } catch (compressError) {
        console.error("Image compression failed", compressError);
      }
    }
    const formData = new FormData();
    formData.append("image", payload, file.name || "species.jpg");
    await api.post(`/species/${targetId}/image`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    await fetchSpecies();
    toast.success("照片已更新");
  } catch (error: any) {
    if (isAuthError(error)) return;
    console.error("Failed to upload species image", error);
    errorMsg.value = apiErrorMessage(error, "上传照片");
  } finally {
    uploadingPhotoId.value = null;
    photoTargetId.value = null;
  }
};

const savePrice = async (sp: SpeciesItem) => {
  if (editingPriceId.value !== sp.id || savingPrice.value) return;
  const value = Number(editingPrice.value);
  if (!Number.isFinite(value) || value <= 0) {
    errorMsg.value = "单价必须大于0";
    return;
  }
  if (Math.abs(value - toJinPrice(sp.default_price ?? 0)) < 0.005) {
    cancelEditPrice();
    return;
  }
  savingPrice.value = true;
  try {
    // 后端 PUT 是整行覆盖：其它字段原样带回，避免把供应商/日期清空
    await api.put(`/species/${sp.id}`, {
      name_zh: sp.name_zh,
      default_unit: sp.default_unit,
      default_price: toPerKgPrice(value),
      release_date: sp.release_date ?? null,
      supplier_name: sp.supplier_name ?? null,
      supplier_note: sp.supplier_note ?? null,
    });
    cancelEditPrice();
    toast.success(`「${sp.name_zh}」单价已更新`);
    await invalidateCache();
    await fetchSpecies();
  } catch (error: any) {
    if (isAuthError(error)) return;
    errorMsg.value = apiErrorMessage(error, "保存单价");
  } finally {
    savingPrice.value = false;
  }
};

const deleteConfirm = ref({
  show: false,
  id: null as number | null,
  isBatch: false,
});

const isAllSelected = computed(() => {
  // 只对当前页的判断负责，避免勾一页变成全选所有页
  return (
    paginatedSpecies.value.length > 0 &&
    paginatedSpecies.value.every((sp) => selectedIds.value.includes(sp.id))
  );
});

const toggleAll = (e: Event) => {
  const checked = (e.target as HTMLInputElement).checked;
  const pageIds = paginatedSpecies.value.map((sp) => sp.id);
  if (checked) {
    // 只勾选当前页的行，不影响其它页已选中的数据
    const extra = pageIds.filter((id) => !selectedIds.value.includes(id));
    selectedIds.value = [...selectedIds.value, ...extra];
  } else {
    selectedIds.value = selectedIds.value.filter((id) => !pageIds.includes(id));
  }
};

const exportingSpecies = ref(false);

const exportSpecies = async () => {
  // 有勾选 -> 只导勾选的品种；没勾选 -> 全量导出
  const params: Record<string, string> = {};
  if (selectedIds.value.length > 0) {
    params.species_ids = selectedIds.value.join(",");
  }
  exportingSpecies.value = true;
  try {
    const res = await api.get("/species/export", {
      params,
      responseType: "blob",
      timeout: 60000,
    });
    const blob = res.data as Blob;
    if (!blob || blob.size === 0) {
      toast.error("导出失败：文件为空");
      return;
    }
    let filename = "慈悲组品种库.xlsx";
    const disposition = res.headers?.["content-disposition"] as string | undefined;
    if (disposition) {
      const match = disposition.match(/filename\*=UTF-8''([^;]+)/i);
      if (match) filename = decodeURIComponent(match[1]);
    }
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
    toast.success("导出完成");
  } catch (error) {
    toast.error(apiErrorMessage(error, "导出品种库"));
  } finally {
    exportingSpecies.value = false;
  }
};

const saving = ref(false);

const newSp = ref({
  name_zh: "",
  default_unit: "斤",
  default_price: "0.00",
  image_url: null as string | null,
  release_date: "",
});

const selectedFile = ref<File | null>(null);
const previewUrl = ref<string | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);

const unitOptions = ["斤", "只", "个"];

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
    default_unit: "斤",
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
    params.set("page", String(currentPage.value));
    params.set("page_size", String(pageSize.value));
    // 列表要显示照片缩略图，让接口带上 image_url（base64 图片仍不会进列表，只在文件存储模式下有值）
    params.set("include_images", "true");
    const url = params.toString()
      ? `/species?${params.toString()}`
      : "/species";
    const res = await api.get(url);
    species.value = Array.isArray(res.data) ? res.data : [];
    const headerTotal = Number(res.headers?.["x-total-count"]);
    totalItems.value =
      Number.isFinite(headerTotal) && headerTotal > 0
        ? headerTotal
        : species.value.length;
  } catch (error: any) {
    if (isAuthError(error)) return;
    console.error("Failed to fetch species", error);
    errorMsg.value = apiErrorMessage(error, "加载品种列表");
  }
};

const handleSearch = () => {
  speciesSearch.value = speciesSearchText.value.trim();
  if (currentPage.value !== 1) {
    currentPage.value = 1; // watch(currentPage) 统一拉取
  } else {
    fetchSpecies();
  }
};

const handleClearSearch = () => {
  speciesSearch.value = "";
  speciesSearchText.value = "";
  if (currentPage.value !== 1) {
    currentPage.value = 1; // watch(currentPage) 统一拉取
  } else {
    fetchSpecies();
  }
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
      default_price: toPerKgPrice(newSp.value.default_price),
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
    await fetchSpecies();
  } catch (error: any) {
    if (isAuthError(error)) return;
    errorMsg.value = apiErrorMessage(error, "保存品种");
  } finally {
    saving.value = false;
  }
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
      await fetchSpecies();
    } catch (error: any) {
      if (isAuthError(error)) return;
      errorMsg.value = apiErrorMessage(error, "批量删除");
      deleteConfirm.value.show = false;
      await invalidateCache();
      await fetchSpecies();
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
      await fetchSpecies();
    } catch (error: any) {
      if (isAuthError(error)) return;
      errorMsg.value = apiErrorMessage(error, "删除品种");
      deleteConfirm.value.show = false;
    }
  }
};

onMounted(() => {
  fetchSpecies();
  const el = rowsBodyRef.value;
  if (el) {
    const syncScrollState = () => {
      bodyScrollsX.value = el.scrollWidth > el.clientWidth + 1;
      bodyGutter.value = Math.max(0, el.offsetWidth - el.clientWidth);
    };
    rowsObserver = new ResizeObserver(syncScrollState);
    rowsObserver.observe(el);
    syncScrollState();
  }
});

onBeforeUnmount(() => {
  rowsObserver?.disconnect();
  rowsObserver = null;
});
</script>

<style scoped>
/* 表头 / 数据行共用同一套列宽：品种 + 放生日期 + 单价 + 单位 + 照片 + 备注 + 操作 */
.species-grid {
  grid-template-columns:
    44px 56px minmax(100px, 1.6fr) minmax(88px, 0.9fr) minmax(84px, 0.9fr)
    minmax(70px, 0.7fr) 64px minmax(90px, 1.2fr) minmax(96px, 0.7fr);
}
</style>
