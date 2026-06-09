<template>
  <section class="p-4 space-y-4">
    <div class="flex items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-serif text-[#6d4f32]">账单</h1>
        <p class="mt-1 text-xs text-[#8a6b4a]">紧凑清单模式</p>
      </div>
      <button
        class="rounded-full border border-[#d8c1a0] bg-white/80 px-3 py-1.5 text-xs text-[#6d4f32] active:opacity-70"
        :disabled="loading"
        @click="fetchBills"
      >
        {{ loading ? '刷新中...' : '刷新' }}
      </button>
    </div>

    <div class="flex gap-2 overflow-x-auto pb-1">
      <button
        v-for="item in statusOptions"
        :key="item.value"
        class="shrink-0 rounded-full border px-3 py-1.5 text-xs transition-colors"
        :class="
          status === item.value
            ? 'border-[#8b6914] bg-[#8b6914] text-white'
            : 'border-[#d8c1a0] bg-white/80 text-[#6d4f32]'
        "
        @click="changeStatus(item.value)"
      >
        {{ item.label }}
      </button>
    </div>

    <div class="rounded-2xl bg-white/90 p-4 shadow-sm space-y-3">
      <input
        v-model.trim="searchText"
        class="w-full rounded-2xl border border-[#d8c1a0] bg-white px-4 py-3 text-sm text-[#5c4033] outline-none"
        placeholder="搜索品种名称"
        @keydown.enter="applyFilters"
      />

      <div class="flex gap-2 overflow-x-auto pb-1">
        <button
          v-for="item in quickDateRanges"
          :key="item.key"
          class="shrink-0 rounded-full border px-3 py-1.5 text-xs transition-colors"
          :class="
            activeQuickRange === item.key
              ? 'border-[#8b6914] bg-[#8b6914] text-white'
              : 'border-[#d8c1a0] bg-white text-[#6d4f32]'
          "
          @click="applyQuickRange(item.key)"
        >
          {{ item.label }}
        </button>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="mb-1 block text-xs text-[#8a6b4a]">开始日期</label>
          <input
            v-model="dateFrom"
            type="date"
            class="w-full rounded-2xl border border-[#d8c1a0] bg-white px-3 py-3 text-sm text-[#5c4033] outline-none"
          />
        </div>
        <div>
          <label class="mb-1 block text-xs text-[#8a6b4a]">结束日期</label>
          <input
            v-model="dateTo"
            type="date"
            class="w-full rounded-2xl border border-[#d8c1a0] bg-white px-3 py-3 text-sm text-[#5c4033] outline-none"
          />
        </div>
      </div>

      <div class="flex items-center gap-2">
        <button
          class="flex-1 rounded-2xl bg-[#8b6914] px-4 py-3 text-sm text-white disabled:opacity-50"
          :disabled="loading"
          @click="applyFilters"
        >
          应用筛选
        </button>
        <button
          class="rounded-2xl border border-[#d8c1a0] bg-white px-4 py-3 text-sm text-[#6d4f32] disabled:opacity-50"
          :disabled="loading"
          @click="resetFilters"
        >
          清空
        </button>
      </div>
    </div>

    <p v-if="errorMsg" class="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">
      {{ errorMsg }}
    </p>

    <div class="rounded-2xl bg-white/90 px-4 py-3 shadow-sm">
      <div class="grid grid-cols-3 gap-3 text-center">
        <div>
          <p class="text-[11px] text-[#8a6b4a]">账单数</p>
          <p class="mt-1 text-sm font-semibold text-[#5c4033]">{{ total }}</p>
        </div>
        <div>
          <p class="text-[11px] text-[#8a6b4a]">总重量</p>
          <p class="mt-1 text-sm font-semibold text-[#5c4033]">{{ sumWeightLabel }}</p>
        </div>
        <div>
          <p class="text-[11px] text-[#8a6b4a]">总金额</p>
          <p class="mt-1 text-sm font-semibold text-[#8b6914]">{{ sumTotalAmountLabel }}</p>
        </div>
      </div>

      <div class="mt-3 flex items-center justify-between border-t border-[#efe1c8] pt-3 text-xs text-[#8a6b4a]">
        <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
        <span>小计合计 {{ sumSubtotalLabel }}</span>
      </div>
    </div>

    <div v-if="activeFilterTags.length > 0" class="rounded-2xl bg-[#fcf7ef] px-4 py-3 shadow-sm">
      <div class="flex items-start justify-between gap-3">
        <div class="flex flex-wrap gap-2">
          <span
            v-for="tag in activeFilterTags"
            :key="tag"
            class="rounded-full bg-white px-3 py-1 text-xs text-[#6d4f32] border border-[#ead9bc]"
          >
            {{ tag }}
          </span>
        </div>
        <button
          class="shrink-0 text-xs text-[#8b6914] active:opacity-70"
          :disabled="loading"
          @click="resetFilters"
        >
          清空筛选
        </button>
      </div>
    </div>

    <div
      v-if="loading && bills.length === 0"
      class="rounded-2xl bg-white/90 p-6 text-center text-sm text-[#8a6b4a] shadow-sm"
    >
      正在加载账单...
    </div>

    <div
      v-else-if="bills.length === 0"
      class="rounded-2xl bg-white/90 p-6 text-center shadow-sm"
    >
      <p class="text-sm text-[#8a6b4a]">
        {{ hasActiveFilters ? '当前筛选条件下没有结果' : '暂无账单数据' }}
      </p>
      <button
        v-if="hasActiveFilters"
        class="mt-3 rounded-full border border-[#d8c1a0] bg-white px-4 py-2 text-xs text-[#6d4f32] active:opacity-70"
        :disabled="loading"
        @click="resetFilters"
      >
        清空筛选条件
      </button>
    </div>

    <div v-else class="space-y-2">
      <article
        v-for="item in bills"
        :key="item.id"
        class="rounded-2xl border border-[#efe1c8] bg-white/95 px-4 py-3 shadow-sm active:opacity-80"
        @click="goToDetail(item.id)"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-semibold text-[#5c4033]">
              {{ item.species?.name_zh || `账单 #${item.id}` }}
            </p>
            <p class="mt-1 text-xs text-[#8a6b4a]">
              {{ formatWeight(item.weight, item.species?.default_unit) }}
            </p>
          </div>
          <p class="shrink-0 text-base font-semibold text-[#8b6914]">
            {{ formatMoney(item.total_amount) }}
          </p>
        </div>

        <div class="mt-2 flex items-center justify-between border-t border-[#f2e5cf] pt-2 text-xs text-[#8a6b4a]">
          <span>{{ formatDate(item.release_date || item.created_at) }}</span>
          <span>单价 {{ formatMoney(item.unit_price) }}</span>
          <span>小计 {{ formatMoney(item.subtotal) }}</span>
        </div>
      </article>
    </div>

    <div class="flex items-center gap-2">
      <button
        class="flex-1 rounded-2xl border border-[#d8c1a0] bg-white/80 px-4 py-3 text-sm text-[#6d4f32] disabled:opacity-50"
        :disabled="currentPage <= 1 || loading"
        @click="currentPage -= 1"
      >
        上一页
      </button>
      <button
        class="flex-1 rounded-2xl border border-[#d8c1a0] bg-white/80 px-4 py-3 text-sm text-[#6d4f32] disabled:opacity-50"
        :disabled="currentPage >= totalPages || loading"
        @click="currentPage += 1"
      >
        下一页
      </button>
    </div>

    <!-- FAB 按钮 -->
    <button
      class="fixed bottom-24 right-6 flex h-14 w-14 items-center justify-center rounded-full bg-[#8b6914] text-white shadow-lg active:opacity-80 z-50"
      @click="$router.push('/billing/new')"
    >
      <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
      </svg>
    </button>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { useBillingContextStore } from '../stores/billingContext'
import { apiErrorMessage, isAuthError } from '../../src/lib/error'

type BillItem = {
  id: number
  weight: number
  unit_price: number
  subtotal: number
  total_amount: number
  release_date?: string | null
  created_at?: string | null
  species?: {
    name_zh?: string
    default_unit?: string
  } | null
}

const pageSize = 20
const router = useRouter()
const billingContextStore = useBillingContextStore()
const loading = ref(false)
const errorMsg = ref('')
const total = ref(0)
const sumWeight = ref(0)
const sumSubtotal = ref(0)
const sumTotalAmount = ref(0)
const currentPage = ref(1)
const status = ref<string>('')
const searchText = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const activeQuickRange = ref('')
const bills = ref<BillItem[]>([])

const statusOptions = [
  { label: '全部', value: '' },
  { label: '待处理', value: 'DRAFT' },
  { label: '已完成', value: 'COMPLETED' },
]

const quickDateRanges = [
  { key: 'today', label: '今天' },
  { key: '7d', label: '近7天' },
  { key: '30d', label: '近30天' },
]

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(total.value / pageSize))
})

const sumWeightLabel = computed(() => `${Number(sumWeight.value || 0).toFixed(2)} kg`)
const sumSubtotalLabel = computed(() => formatMoney(sumSubtotal.value))
const sumTotalAmountLabel = computed(() => formatMoney(sumTotalAmount.value))
const hasActiveFilters = computed(() => {
  return Boolean(status.value || searchText.value || dateFrom.value || dateTo.value)
})
const activeFilterTags = computed(() => {
  const tags: string[] = []
  const statusLabel = statusOptions.find(item => item.value === status.value)?.label

  if (statusLabel && status.value) {
    tags.push(`状态：${statusLabel}`)
  }
  if (searchText.value) {
    tags.push(`搜索：${searchText.value}`)
  }
  if (dateFrom.value) {
    tags.push(`开始：${dateFrom.value}`)
  }
  if (dateTo.value) {
    tags.push(`结束：${dateTo.value}`)
  }

  return tags
})

const formatMoney = (value: number) => {
  return `¥${Number(value || 0).toFixed(2)}`
}

const formatWeight = (value: number, unit?: string) => {
  return `${Number(value || 0).toFixed(2)} ${unit || 'kg'}`
}

const formatDate = (value?: string | null) => {
  if (!value) return '--'
  return value.slice(0, 10)
}

const formatInputDate = (value: Date) => {
  const year = value.getFullYear()
  const month = `${value.getMonth() + 1}`.padStart(2, '0')
  const day = `${value.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

const restoreStateFromContext = () => {
  const saved = billingContextStore.restoreListState()
  currentPage.value = saved.page
  status.value = saved.status
  searchText.value = saved.q
  dateFrom.value = saved.dateFrom
  dateTo.value = saved.dateTo
}

const syncListState = () => {
  billingContextStore.setListState({
    page: currentPage.value,
    status: status.value,
    q: searchText.value,
    dateFrom: dateFrom.value,
    dateTo: dateTo.value,
  })
}

const syncPageBills = () => {
  billingContextStore.setPageBills(bills.value.map(item => item.id))
}

const fetchBills = async () => {
  loading.value = true
  errorMsg.value = ''

  try {
    const params = new URLSearchParams({
      page: String(currentPage.value),
      page_size: String(pageSize),
      limit: '0',
    })

    if (status.value) {
      params.set('status', status.value)
    }
    if (searchText.value) {
      params.set('q', searchText.value)
    }
    if (dateFrom.value) {
      params.set('date_from', dateFrom.value)
    }
    if (dateTo.value) {
      params.set('date_to', dateTo.value)
    }

    const response = await api.get(`/bills?${params.toString()}`)
    const data = response.data || {}

    bills.value = Array.isArray(data.items) ? data.items : []
    total.value = Number(data.total || 0)
    sumWeight.value = Number(data.sum_weight || 0)
    sumSubtotal.value = Number(data.sum_subtotal || 0)
    sumTotalAmount.value = Number(data.sum_total_amount || 0)
    syncListState()
    syncPageBills()
  } catch (error: any) {
    if (isAuthError(error)) return
    errorMsg.value = apiErrorMessage(error, '加载账单列表')
  } finally {
    loading.value = false
  }
}

const changeStatus = (value: string) => {
  if (status.value === value) return
  status.value = value
  if (currentPage.value === 1) {
    fetchBills()
    return
  }
  currentPage.value = 1
}

const applyQuickRange = (key: string) => {
  const today = new Date()
  const end = formatInputDate(today)
  let start = end

  if (key === '7d') {
    const next = new Date(today)
    next.setDate(today.getDate() - 6)
    start = formatInputDate(next)
  } else if (key === '30d') {
    const next = new Date(today)
    next.setDate(today.getDate() - 29)
    start = formatInputDate(next)
  }

  dateFrom.value = start
  dateTo.value = end
  activeQuickRange.value = key
  applyFilters()
}

const applyFilters = () => {
  if (currentPage.value === 1) {
    fetchBills()
    return
  }
  currentPage.value = 1
}

const resetFilters = () => {
  searchText.value = ''
  dateFrom.value = ''
  dateTo.value = ''
  status.value = ''
  activeQuickRange.value = ''
  if (currentPage.value === 1) {
    fetchBills()
    return
  }
  currentPage.value = 1
}

const goToDetail = (billId: number) => {
  const currentIndex = bills.value.findIndex(item => item.id === billId)
  syncListState()
  billingContextStore.setPageBills(
    bills.value.map(item => item.id),
    currentIndex,
  )
  router.push(`/billing/${billId}`)
}

watch(currentPage, () => {
  fetchBills()
})

onMounted(() => {
  restoreStateFromContext()
  fetchBills()
})
</script>
