<template>
  <section class="p-4 space-y-4">
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
      <button
        v-if="previousBillId"
        class="rounded-full border border-[#d8c1a0] bg-white/80 px-3 py-1.5 text-sm text-[#6d4f32] active:opacity-70"
        @click="goPrevious"
      >
        上一条
      </button>
      <button
        v-if="nextBillId"
        class="rounded-full border border-[#d8c1a0] bg-white/80 px-3 py-1.5 text-sm text-[#6d4f32] active:opacity-70"
        @click="goNext"
      >
        下一条
      </button>
      <div class="min-w-0">
        <h1 class="truncate text-xl font-serif text-[#6d4f32]">
          {{ bill?.species?.name_zh || '账单详情' }}
        </h1>
        <p class="mt-1 text-xs text-[#8a6b4a]">只读详情</p>
      </div>
    </div>

    <p v-if="errorMsg" class="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">
      {{ errorMsg }}
    </p>

    <div
      v-if="loading"
      class="rounded-2xl bg-white/90 p-6 text-center text-sm text-[#8a6b4a] shadow-sm"
    >
      正在加载账单详情...
    </div>

    <div
      v-else-if="!bill"
      class="rounded-2xl bg-white/90 p-6 text-center text-sm text-[#8a6b4a] shadow-sm"
    >
      未找到账单详情
    </div>

    <template v-else>
      <article class="rounded-2xl bg-white/95 p-4 shadow-sm">
        <div class="flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="text-xs text-[#8a6b4a]">总金额</p>
            <p class="mt-2 text-2xl font-semibold text-[#8b6914]">
              {{ formatMoney(bill.total_amount) }}
            </p>
          </div>
        </div>
      </article>

      <article class="rounded-2xl bg-white/95 p-4 shadow-sm">
        <h2 class="text-sm font-semibold text-[#6d4f32]">基础信息</h2>
        <div class="mt-3 space-y-3">
          <div class="flex items-center justify-between gap-3 text-sm">
            <span class="text-[#8a6b4a]">品种</span>
            <span class="truncate text-right text-[#5c4033]">{{ bill.species?.name_zh || '--' }}</span>
          </div>
          <div class="flex items-center justify-between gap-3 text-sm">
            <span class="text-[#8a6b4a]">重量</span>
            <span class="text-[#5c4033]">{{ formatWeight(bill.weight, bill.species?.default_unit) }}</span>
          </div>
          <div class="flex items-center justify-between gap-3 text-sm">
            <span class="text-[#8a6b4a]">单价</span>
            <span class="text-[#5c4033]">{{ formatMoney(bill.unit_price) }}</span>
          </div>
          <div class="flex items-center justify-between gap-3 text-sm">
            <span class="text-[#8a6b4a]">小计</span>
            <span class="text-[#5c4033]">{{ formatMoney(bill.subtotal) }}</span>
          </div>
          <div class="flex items-center justify-between gap-3 text-sm">
            <span class="text-[#8a6b4a]">总金额</span>
            <span class="text-[#8b6914] font-semibold">{{ formatMoney(bill.total_amount) }}</span>
          </div>
        </div>
      </article>

      <article class="rounded-2xl bg-white/95 p-4 shadow-sm">
        <h2 class="text-sm font-semibold text-[#6d4f32]">时间信息</h2>
        <div class="mt-3 space-y-3">
          <div class="flex items-center justify-between gap-3 text-sm">
            <span class="text-[#8a6b4a]">放生日期</span>
            <span class="text-[#5c4033]">{{ formatDate(bill.release_date) }}</span>
          </div>
          <div class="flex items-center justify-between gap-3 text-sm">
            <span class="text-[#8a6b4a]">创建时间</span>
            <span class="text-[#5c4033]">{{ formatDateTime(bill.created_at) }}</span>
          </div>
        </div>
      </article>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { useBillingContextStore } from '../stores/billingContext'
import { apiErrorMessage, isAuthError } from '../../src/lib/error'

type BillDetail = {
  id: number
  weight: number
  unit_price: number
  subtotal: number
  total_amount: number
  status: string
  release_date?: string | null
  created_at?: string | null
  species?: {
    name_zh?: string
    default_unit?: string
  } | null
}

const route = useRoute()
const router = useRouter()
const billingContextStore = useBillingContextStore()
const loading = ref(false)
const errorMsg = ref('')
const bill = ref<BillDetail | null>(null)

const billId = computed(() => Number(route.params.id))
const billIds = computed(() => billingContextStore.billIds)
const currentIndex = computed(() => billingContextStore.currentIndex)
const previousBillId = computed(() => {
  return currentIndex.value > 0 ? billIds.value[currentIndex.value - 1] : null
})
const nextBillId = computed(() => {
  return currentIndex.value >= 0 && currentIndex.value < billIds.value.length - 1
    ? billIds.value[currentIndex.value + 1]
    : null
})

const goBackToList = () => {
  router.push('/billing')
}

const goPrevious = () => {
  if (!previousBillId.value) return
  billingContextStore.setCurrentIndex(currentIndex.value - 1)
  router.push(`/billing/${previousBillId.value}`)
}

const goNext = () => {
  if (!nextBillId.value) return
  billingContextStore.setCurrentIndex(currentIndex.value + 1)
  router.push(`/billing/${nextBillId.value}`)
}

const formatMoney = (value: number) => {
  return `¥${Number(value || 0).toFixed(2)}`
}

const formatWeight = (value: number, unit?: string) => {
  return `${Number(value || 0).toFixed(2)} ${unit || 'kg'}`
}

const formatDate = (value?: string | null) => {
  return value ? value.slice(0, 10) : '--'
}

const formatDateTime = (value?: string | null) => {
  if (!value) return '--'
  return value.slice(0, 16).replace('T', ' ')
}

const fetchBillDetail = async () => {
  loading.value = true
  errorMsg.value = ''

  try {
    const response = await api.get(`/bills/${billId.value}`)
    bill.value = response.data || null
  } catch (error: any) {
    if (isAuthError(error)) return
    errorMsg.value = apiErrorMessage(error, '加载账单详情')
  } finally {
    loading.value = false
  }
}

const syncCurrentIndex = () => {
  const matchedIndex = billIds.value.indexOf(billId.value)
  billingContextStore.setCurrentIndex(matchedIndex)
}

onMounted(() => {
  syncCurrentIndex()
  fetchBillDetail()
})

watch(
  () => route.params.id,
  () => {
    syncCurrentIndex()
    fetchBillDetail()
  },
)
</script>
