# 移动端单据录入 (Billing Form) 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `src-mobile` 目录下构建独立的账单录入表单页面（BillingForm.vue），实现移动端的快捷“记一笔”以及详情页的“编辑”功能。

**Architecture:**
- 使用 Vue Router 注册 `/billing/new` 和 `/billing/edit/:id` 路由，复用同一个组件 `BillingForm.vue`。
- 新增模式下，保存成功后表单重置但保留日期，并弹出 Toast 继续留在本页录入；编辑模式下，保存成功返回详情页。
- 依赖现有的 `/api/species` 拉取可用下拉品种。选中品种时，提取并默认带入 `default_price` 到单价输入框。
- 重量与单价联动计算小计金额，点击保存时拦截校验。

**Tech Stack:** Vue 3 (Composition API), Vue Router, Tailwind CSS, Axios.

---

### Task 1: 路由与基础页面骨架

**Files:**
- Modify: `d:\Fish\src-mobile\router\index.ts:18-24`
- Create: `d:\Fish\src-mobile\pages\BillingForm.vue`

- [x] **Step 1: 注册表单路由**

修改 `d:\Fish\src-mobile\router\index.ts`，在 children 中增加路由。

```typescript
// src-mobile/router/index.ts
// ...
      children: [
        { path: '', redirect: '/dashboard' },
        { path: 'dashboard', name: 'MobileDashboard', component: () => import('../pages/Dashboard.vue') },
        { path: 'billing', name: 'MobileBilling', component: () => import('../pages/Billing.vue') },
        { path: 'billing/new', name: 'MobileBillingNew', component: () => import('../pages/BillingForm.vue') },
        { path: 'billing/edit/:id', name: 'MobileBillingEdit', component: () => import('../pages/BillingForm.vue') },
        { path: 'billing/:id', name: 'MobileBillingDetail', component: () => import('../pages/BillingDetail.vue') },
        { path: 'species', name: 'MobileSpecies', component: () => import('../pages/Species.vue') },
      ]
// ...
```

- [x] **Step 2: 创建基础表单组件**

创建 `d:\Fish\src-mobile\pages\BillingForm.vue`，写入基础骨架。

```vue
<template>
  <section class="p-4 space-y-4">
    <div class="flex items-center justify-between gap-3">
      <div class="flex items-center gap-3 min-w-0">
        <button
          class="rounded-full border border-[#d8c1a0] bg-white/80 px-3 py-1.5 text-sm text-[#6d4f32] active:opacity-70 shrink-0"
          @click="goBack"
        >
          返回
        </button>
        <h1 class="truncate text-xl font-serif text-[#6d4f32]">
          {{ isEdit ? '编辑账单' : '记一笔' }}
        </h1>
      </div>
    </div>
    
    <div class="rounded-2xl bg-white/90 p-4 shadow-sm">
      <p class="text-sm text-[#8a6b4a]">表单内容占位</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => route.name === 'MobileBillingEdit')

const goBack = () => {
  router.back()
}
</script>
```

- [x] **Step 3: 检查路由是否正常解析**

无需测试文件，可以通过 `npx vite build -c vite.mobile.config.ts` 检查语法错误。

```bash
npx vite build -c vite.mobile.config.ts
```

- [x] **Step 4: Commit**

```bash
git add src-mobile/router/index.ts src-mobile/pages/BillingForm.vue
git commit -m "feat(mobile): add routing and skeleton for billing form"
```

---

### Task 2: 添加入口按钮

**Files:**
- Modify: `d:\Fish\src-mobile\pages\Billing.vue`
- Modify: `d:\Fish\src-mobile\pages\BillingDetail.vue`

- [x] **Step 1: 列表页增加悬浮“记一笔”按钮**

在 `d:\Fish\src-mobile\pages\Billing.vue` 的 `<template>` 最后（`<section>` 内的末尾）添加一个绝对定位的 FAB 按钮。

```vue
<!-- ... 在 </section> 闭合标签之前添加 ... -->
    <!-- FAB 按钮 -->
    <button
      class="fixed bottom-24 right-6 flex h-14 w-14 items-center justify-center rounded-full bg-[#8b6914] text-white shadow-lg active:opacity-80 z-50"
      @click="$router.push('/billing/new')"
    >
      <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
      </svg>
    </button>
```

- [x] **Step 2: 详情页增加“编辑”按钮**

在 `d:\Fish\src-mobile\pages\BillingDetail.vue` 的顶部操作栏中，在“返回”按钮旁边增加一个“编辑”按钮。

```vue
<!-- 修改 d:\Fish\src-mobile\pages\BillingDetail.vue -->
    <div class="flex items-center gap-3">
      <button
        class="rounded-full border border-[#d8c1a0] bg-white/80 px-3 py-1.5 text-sm text-[#6d4f32] active:opacity-70 shrink-0"
        @click="goBackToList"
      >
        返回
      </button>
      <!-- 新增编辑按钮 -->
      <button
        v-if="bill"
        class="rounded-full border border-[#d8c1a0] bg-white/80 px-3 py-1.5 text-sm text-[#6d4f32] active:opacity-70 shrink-0"
        @click="$router.push(`/billing/edit/${billId}`)"
      >
        编辑
      </button>
```

- [x] **Step 3: 运行检查**

```bash
npx vite build -c vite.mobile.config.ts
```

- [x] **Step 4: Commit**

```bash
git add src-mobile/pages/Billing.vue src-mobile/pages/BillingDetail.vue
git commit -m "feat(mobile): add entry buttons for billing form"
```

---

### Task 3: 实现 BillingForm 视图与品种拉取

**Files:**
- Modify: `d:\Fish\src-mobile\pages\BillingForm.vue`

- [x] **Step 1: 编写表单模板和拉取品种接口**

在 `d:\Fish\src-mobile\pages\BillingForm.vue` 中实现表单状态定义、品种列表拉取。

```vue
<template>
  <section class="p-4 space-y-4 pb-24">
    <div class="flex items-center justify-between gap-3">
      <div class="flex items-center gap-3 min-w-0">
        <button
          class="rounded-full border border-[#d8c1a0] bg-white/80 px-3 py-1.5 text-sm text-[#6d4f32] active:opacity-70 shrink-0"
          @click="goBack"
        >
          返回
        </button>
        <h1 class="truncate text-xl font-serif text-[#6d4f32]">
          {{ isEdit ? '编辑账单' : '记一笔' }}
        </h1>
      </div>
    </div>
    
    <p v-if="errorMsg" class="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">
      {{ errorMsg }}
    </p>
    
    <form @submit.prevent="handleSave" class="space-y-4">
      <div class="rounded-2xl bg-white/90 p-4 shadow-sm space-y-4">
        <!-- 日期选择 -->
        <div>
          <label class="mb-1 block text-sm font-medium text-[#8a6b4a]">日期 (Release Date)</label>
          <input
            v-model="formData.release_date"
            type="date"
            class="w-full rounded-xl border border-[#d8c1a0] bg-white px-3 py-2.5 text-[#5c4033] outline-none focus:border-[#8b6914]"
          />
        </div>
        
        <!-- 品种选择 -->
        <div>
          <label class="mb-1 block text-sm font-medium text-[#8a6b4a]">品种 (必填)</label>
          <select
            v-model="formData.species_id"
            @change="onSpeciesChange"
            class="w-full rounded-xl border border-[#d8c1a0] bg-white px-3 py-2.5 text-[#5c4033] outline-none focus:border-[#8b6914]"
            :disabled="loadingSpecies"
          >
            <option value="">请选择品种...</option>
            <option v-for="sp in speciesList" :key="sp.id" :value="sp.id">
              {{ sp.name_zh }} ({{ sp.default_unit }})
            </option>
          </select>
        </div>
        
        <!-- 重量 -->
        <div>
          <label class="mb-1 block text-sm font-medium text-[#8a6b4a]">重量 (必填)</label>
          <div class="relative">
            <input
              v-model="formData.weight"
              type="number"
              step="0.01"
              min="0"
              inputmode="decimal"
              class="w-full rounded-xl border border-[#d8c1a0] bg-white px-3 py-2.5 pr-12 text-[#5c4033] outline-none focus:border-[#8b6914]"
              placeholder="0.00"
            />
            <span class="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-[#8a6b4a]">
              {{ selectedSpeciesUnit || 'kg' }}
            </span>
          </div>
        </div>
        
        <!-- 单价 -->
        <div>
          <label class="mb-1 block text-sm font-medium text-[#8a6b4a]">单价 (必填)</label>
          <div class="relative">
            <input
              v-model="formData.unit_price"
              type="number"
              step="0.01"
              min="0"
              inputmode="decimal"
              class="w-full rounded-xl border border-[#d8c1a0] bg-white px-3 py-2.5 pr-12 text-[#5c4033] outline-none focus:border-[#8b6914]"
              placeholder="0.00"
            />
            <span class="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-[#8a6b4a]">元</span>
          </div>
        </div>
        
        <!-- 小计展示 -->
        <div class="rounded-xl bg-[#fcf7ef] p-3 text-right">
          <span class="text-sm text-[#8a6b4a]">小计金额：</span>
          <span class="text-lg font-bold text-[#8b6914]">¥ {{ subtotal.toFixed(2) }}</span>
        </div>
        
        <!-- 状态选择 -->
        <div>
          <label class="mb-1 block text-sm font-medium text-[#8a6b4a]">状态</label>
          <div class="flex gap-2">
            <button
              type="button"
              class="flex-1 rounded-xl border py-2.5 text-sm transition-colors"
              :class="formData.status === 'COMPLETED' ? 'border-[#8b6914] bg-[#8b6914] text-white' : 'border-[#d8c1a0] bg-white text-[#6d4f32]'"
              @click="formData.status = 'COMPLETED'"
            >
              已完成
            </button>
            <button
              type="button"
              class="flex-1 rounded-xl border py-2.5 text-sm transition-colors"
              :class="formData.status === 'DRAFT' ? 'border-[#8b6914] bg-[#8b6914] text-white' : 'border-[#d8c1a0] bg-white text-[#6d4f32]'"
              @click="formData.status = 'DRAFT'"
            >
              待处理
            </button>
          </div>
        </div>
      </div>
      
      <button
        type="submit"
        class="w-full rounded-2xl bg-[#8b6914] py-3.5 text-center font-bold text-white shadow-md active:opacity-80 disabled:opacity-50"
        :disabled="saving"
      >
        {{ saving ? '保存中...' : '保存' }}
      </button>
    </form>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { apiErrorMessage, isAuthError } from '../../src/lib/error'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => route.name === 'MobileBillingEdit')
const billId = computed(() => route.params.id)

const errorMsg = ref('')
const loadingSpecies = ref(false)
const saving = ref(false)
const speciesList = ref<any[]>([])

const formData = ref({
  release_date: new Date().toISOString().slice(0, 10),
  species_id: '' as number | string,
  weight: '',
  unit_price: '',
  status: 'COMPLETED',
  fee_value: 0,
})

const selectedSpecies = computed(() => {
  return speciesList.value.find(s => s.id === formData.value.species_id)
})

const selectedSpeciesUnit = computed(() => selectedSpecies.value?.default_unit || '')

const subtotal = computed(() => {
  const w = parseFloat(String(formData.value.weight)) || 0
  const p = parseFloat(String(formData.value.unit_price)) || 0
  return w * p
})

const onSpeciesChange = () => {
  if (selectedSpecies.value && !isEdit.value) {
    // 仅在新增模式下，选择品种时自动覆盖单价
    formData.value.unit_price = String(selectedSpecies.value.default_price || '')
  }
}

const fetchSpecies = async () => {
  loadingSpecies.value = true
  try {
    const res = await api.get('/species', { params: { include_images: false, limit: 1000 } })
    speciesList.value = res.data.items || []
  } catch (error: any) {
    if (!isAuthError(error)) {
      errorMsg.value = apiErrorMessage(error, '获取品种失败')
    }
  } finally {
    loadingSpecies.value = false
  }
}

const goBack = () => {
  router.back()
}

const handleSave = async () => {
  // TODO: Validation and API calls
}

onMounted(() => {
  fetchSpecies()
})
</script>
```

- [x] **Step 2: 运行检查**

```bash
npx vite build -c vite.mobile.config.ts
```

- [x] **Step 3: Commit**

```bash
git add src-mobile/pages/BillingForm.vue
git commit -m "feat(mobile): build billing form layout and fetch species"
```

---

### Task 4: 实现数据加载与保存逻辑

**Files:**
- Modify: `d:\Fish\src-mobile\pages\BillingForm.vue`

- [x] **Step 1: 实现详情拉取（编辑模式）与保存提交逻辑**

更新 `<script setup>` 部分的 `handleSave` 和生命周期。引入 `Toast` 机制（为了简单可靠，可以手写一个临时状态，或用原生 alert，这里用简单局部状态或原生 alert）。

```vue
<!-- 修改 src-mobile/pages/BillingForm.vue 的 script 部分 -->
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { apiErrorMessage, isAuthError } from '../../src/lib/error'

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => route.name === 'MobileBillingEdit')
const billId = computed(() => route.params.id)

const errorMsg = ref('')
const loadingSpecies = ref(false)
const saving = ref(false)
const speciesList = ref<any[]>([])

const formData = ref({
  release_date: new Date().toISOString().slice(0, 10),
  species_id: '' as number | string,
  weight: '',
  unit_price: '',
  status: 'COMPLETED',
  fee_value: 0,
})

const selectedSpecies = computed(() => {
  return speciesList.value.find(s => s.id === formData.value.species_id)
})

const selectedSpeciesUnit = computed(() => selectedSpecies.value?.default_unit || '')

const subtotal = computed(() => {
  const w = parseFloat(String(formData.value.weight)) || 0
  const p = parseFloat(String(formData.value.unit_price)) || 0
  return w * p
})

const onSpeciesChange = () => {
  if (selectedSpecies.value && !isEdit.value) {
    formData.value.unit_price = String(selectedSpecies.value.default_price || '')
  }
}

const fetchSpecies = async () => {
  loadingSpecies.value = true
  try {
    const res = await api.get('/species', { params: { include_images: false, limit: 1000 } })
    speciesList.value = res.data.items || []
  } catch (error: any) {
    if (!isAuthError(error)) {
      errorMsg.value = apiErrorMessage(error, '获取品种失败')
    }
  } finally {
    loadingSpecies.value = false
  }
}

const fetchBillDetail = async () => {
  if (!isEdit.value) return
  try {
    const res = await api.get(`/bills/${billId.value}`)
    const data = res.data
    formData.value = {
      release_date: data.release_date ? data.release_date.slice(0, 10) : '',
      species_id: data.species_id,
      weight: String(data.weight),
      unit_price: String(data.unit_price),
      status: data.status,
      fee_value: data.fee_value || 0,
    }
  } catch (error: any) {
    if (!isAuthError(error)) {
      errorMsg.value = apiErrorMessage(error, '加载账单详情失败')
    }
  }
}

const goBack = () => {
  router.back()
}

const handleSave = async () => {
  errorMsg.value = ''
  
  // Validation
  if (!formData.value.species_id) {
    errorMsg.value = '请选择品种'
    return
  }
  if (!formData.value.weight || parseFloat(String(formData.value.weight)) <= 0) {
    errorMsg.value = '请输入有效的重量'
    return
  }
  if (!formData.value.unit_price || parseFloat(String(formData.value.unit_price)) <= 0) {
    errorMsg.value = '请输入有效的单价'
    return
  }

  saving.value = true
  try {
    const payload = {
      ...formData.value,
      weight: parseFloat(String(formData.value.weight)),
      unit_price: parseFloat(String(formData.value.unit_price)),
      species_id: Number(formData.value.species_id)
    }

    if (isEdit.value) {
      await api.put(`/bills/${billId.value}`, payload)
      alert('修改成功')
      goBack()
    } else {
      await api.post('/bills', payload)
      alert('保存成功')
      // 重置表单，但保留日期
      const keptDate = formData.value.release_date
      formData.value = {
        release_date: keptDate,
        species_id: '',
        weight: '',
        unit_price: '',
        status: 'COMPLETED',
        fee_value: 0,
      }
    }
  } catch (error: any) {
    if (!isAuthError(error)) {
      errorMsg.value = apiErrorMessage(error, '保存失败')
    }
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await fetchSpecies()
  await fetchBillDetail()
})
</script>
```

- [x] **Step 2: 运行检查**

```bash
npx vite build -c vite.mobile.config.ts
```

- [x] **Step 3: Commit**

```bash
git add src-mobile/pages/BillingForm.vue
git commit -m "feat(mobile): implement bill save and edit logic"
```

---

Plan complete and saved to `docs/superpowers/plans/2026-06-09-mobile-billing-form.md`. Two execution options:

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?