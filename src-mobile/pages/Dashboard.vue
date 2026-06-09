<template>
  <section class="p-4 space-y-4">
    <div class="flex items-center justify-between">
      <h1 class="text-xl font-serif text-[#6d4f32]">首页</h1>
      <button
        class="rounded-full border border-[#d8c1a0] bg-white/80 px-3 py-1.5 text-xs text-[#6d4f32] active:opacity-70"
        :disabled="loading"
        @click="fetchDashboard"
      >
        {{ loading ? '刷新中...' : '刷新' }}
      </button>
    </div>

    <p v-if="errorMsg" class="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">
      {{ errorMsg }}
    </p>

    <div class="grid grid-cols-2 gap-3">
      <article class="rounded-2xl bg-white/90 p-4 shadow-sm">
        <p class="text-xs text-[#8a6b4a]">品种总数</p>
        <p class="mt-2 text-2xl font-semibold text-[#5c4033]">{{ speciesCount }}</p>
      </article>

      <article class="rounded-2xl bg-white/90 p-4 shadow-sm">
        <p class="text-xs text-[#8a6b4a]">近 30 天有走势</p>
        <p class="mt-2 text-2xl font-semibold text-[#5c4033]">{{ trendingCount }}</p>
      </article>
    </div>

    <article class="rounded-2xl bg-white/90 p-4 shadow-sm">
      <div class="flex items-center justify-between">
        <h2 class="text-base font-serif text-[#6d4f32]">周单价趋势</h2>
        <span class="text-xs text-[#8a6b4a]">最近趋势</span>
      </div>

      <div v-if="loading && weeklyTrendCards.length === 0" class="py-8 text-center text-sm text-[#8a6b4a]">
        正在加载走势数据...
      </div>

      <div v-else-if="weeklyTrendCards.length === 0" class="py-8 text-center text-sm text-[#8a6b4a]">
        暂无周单价趋势数据
      </div>

      <div v-else class="mt-3 space-y-3">
        <div
          v-for="item in weeklyTrendCards"
          :key="item.id"
          class="rounded-2xl border border-[#ead9bc] bg-[#fcf8f2] px-4 py-3"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="truncate text-sm font-semibold text-[#5c4033]">{{ item.name }}</p>
              <p class="mt-1 text-xs text-[#8a6b4a]">{{ item.startDate }} -> {{ item.endDate }}</p>
            </div>
            <p
              class="shrink-0 text-xs font-semibold"
              :class="item.changeValue >= 0 ? 'text-red-500' : 'text-green-600'"
            >
              {{ item.changeLabel }}
            </p>
          </div>

          <div class="mt-2 flex items-center justify-between text-xs text-[#8a6b4a]">
            <span>{{ item.startPrice }}</span>
            <span>-></span>
            <span class="font-semibold text-[#5c4033]">{{ item.currentPrice }}</span>
          </div>

          <div class="mt-3 space-y-1.5">
            <div
              v-for="point in item.recentPoints"
              :key="`${item.id}-${point.date}-${point.price}`"
              class="flex items-center justify-between rounded-xl bg-white/80 px-3 py-2 text-xs"
            >
              <span class="text-[#8a6b4a]">{{ point.date }}</span>
              <span class="tabular-nums text-[#5c4033]">{{ point.price }}</span>
              <span
                class="tabular-nums"
                :class="
                  point.diff > 0
                    ? 'text-red-500'
                    : point.diff < 0
                      ? 'text-green-600'
                      : 'text-[#8a6b4a]'
                "
              >
                {{ point.diffLabel }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </article>

    <article class="rounded-2xl bg-white/90 p-4 shadow-sm">
      <div class="flex items-center justify-between">
        <h2 class="text-base font-serif text-[#6d4f32]">单价浮动</h2>
        <span class="text-xs text-[#8a6b4a]">最高 - 最低</span>
      </div>

      <div v-if="loading && priceFluctuationRows.length === 0" class="py-8 text-center text-sm text-[#8a6b4a]">
        正在加载品种数据...
      </div>

      <div v-else-if="priceFluctuationRows.length === 0" class="py-8 text-center text-sm text-[#8a6b4a]">
        暂无单价浮动数据
      </div>

      <div v-else class="mt-3 space-y-2">
        <div
          v-for="item in priceFluctuationRows"
          :key="item.id"
          class="rounded-2xl border border-[#f0e2ca] px-4 py-3"
        >
          <div class="flex items-center justify-between gap-3">
            <p class="truncate text-sm font-medium text-[#5c4033]">{{ item.name }}</p>
            <p class="text-xs font-semibold text-[#8b6914]">
              {{ formatPrice(item.rangeValue) }}
            </p>
          </div>
          <div class="mt-2 grid grid-cols-2 gap-3 text-xs">
            <div class="rounded-xl bg-[#fcf8f2] px-3 py-2">
              <p class="text-[#8a6b4a]">最低</p>
              <p class="mt-1 font-semibold text-[#5c4033]">{{ formatPrice(item.minPrice) }}</p>
            </div>
            <div class="rounded-xl bg-[#fcf8f2] px-3 py-2">
              <p class="text-[#8a6b4a]">最高</p>
              <p class="mt-1 font-semibold text-[#5c4033]">{{ formatPrice(item.maxPrice) }}</p>
            </div>
          </div>
        </div>
      </div>
    </article>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import api from '../api'
import { apiErrorMessage, isAuthError } from '../../src/lib/error'

type SpeciesItem = {
  id: number
  name_zh: string
  default_unit: string
  default_price: number
  created_at?: string | null
}

type TrendPoint = {
  date: string
  avg_price: number
}

const loading = ref(false)
const errorMsg = ref('')
const speciesList = ref<SpeciesItem[]>([])
const trendMap = ref<Record<number, TrendPoint[]>>({})

const speciesCount = computed(() => speciesList.value.length)
const trendingCount = computed(() => Object.keys(trendMap.value).length)

const recentSpecies = computed(() => {
  return [...speciesList.value]
    .sort((a, b) => {
      const timeA = a.created_at ? new Date(a.created_at).getTime() : 0
      const timeB = b.created_at ? new Date(b.created_at).getTime() : 0
      return timeB - timeA
    })
    .slice(0, 5)
})

const trendCards = computed(() => {
  return speciesList.value
    .map(species => {
      const points = trendMap.value[species.id] || []
      if (points.length === 0) return null

      const sortedPoints = [...points].sort((a, b) => a.date.localeCompare(b.date))
      const first = sortedPoints[0]
      const last = sortedPoints[sortedPoints.length - 1]
      const changeValue = Number(last.avg_price) - Number(first.avg_price)

      return {
        id: species.id,
        name: species.name_zh,
        firstDate: formatDate(first.date),
        lastDate: formatDate(last.date),
        latestPrice: formatPrice(Number(last.avg_price)),
        changeValue,
        changeLabel: `${changeValue >= 0 ? '+' : ''}${formatPrice(changeValue)}`,
      }
    })
    .filter((item): item is NonNullable<typeof item> => Boolean(item))
    .sort((a, b) => Math.abs(b.changeValue) - Math.abs(a.changeValue))
    .slice(0, 6)
})

const isPackagingItem = (name: string) => {
  const keywords = ['袋', '打包', '包装', '绳子', '胶带', '泡沫', '保温', '耗材']
  return keywords.some(keyword => name.includes(keyword))
}

const weeklyTrendCards = computed(() => {
  return speciesList.value
    .map(species => {
      if (isPackagingItem(species.name_zh)) return null

      const points = [...(trendMap.value[species.id] || [])]
        .filter(point => point.date && point.avg_price != null)
        .sort((a, b) => a.date.localeCompare(b.date))

      if (points.length < 2) return null

      const start = points[0]
      const current = points[points.length - 1]
      const recentPoints = points.slice(-3).map((point, index, arr) => {
        const prev = index === 0 ? null : arr[index - 1]
        const diff = prev ? Number(point.avg_price) - Number(prev.avg_price) : 0

        return {
          date: formatDate(point.date),
          price: formatPrice(Number(point.avg_price)),
          diff,
          diffLabel: index === 0 ? '-' : `${diff >= 0 ? '+' : ''}${formatPrice(diff)}`,
        }
      })

      const changeValue = Number(current.avg_price) - Number(start.avg_price)

      return {
        id: species.id,
        name: species.name_zh,
        startDate: formatDate(start.date),
        endDate: formatDate(current.date),
        startPrice: formatPrice(Number(start.avg_price)),
        currentPrice: formatPrice(Number(current.avg_price)),
        changeValue,
        changeLabel: `${changeValue >= 0 ? '+' : ''}${formatPrice(changeValue)}`,
        recentPoints,
      }
    })
    .filter((item): item is NonNullable<typeof item> => Boolean(item))
    .sort((a, b) => Math.abs(b.changeValue) - Math.abs(a.changeValue))
    .slice(0, 6)
})

const priceFluctuationRows = computed(() => {
  return speciesList.value
    .map(species => {
      if (isPackagingItem(species.name_zh)) return null

      const prices = (trendMap.value[species.id] || [])
        .map(point => Number(point.avg_price))
        .filter(price => !Number.isNaN(price))

      if (prices.length === 0) return null

      const minPrice = Math.min(...prices)
      const maxPrice = Math.max(...prices)

      return {
        id: species.id,
        name: species.name_zh,
        minPrice,
        maxPrice,
        rangeValue: maxPrice - minPrice,
      }
    })
    .filter((item): item is NonNullable<typeof item> => Boolean(item))
    .sort((a, b) => b.rangeValue - a.rangeValue)
    .slice(0, 6)
})

const formatDate = (value: string) => {
  return value ? value.slice(5, 10) : '--'
}

const formatPrice = (value: number) => {
  return `¥${Number(value || 0).toFixed(2)}`
}

const fetchDashboard = async () => {
  loading.value = true
  errorMsg.value = ''

  try {
    const speciesRes = await api.get('/species?include_images=false')
    const list = Array.isArray(speciesRes.data) ? speciesRes.data : []
    speciesList.value = list

    if (list.length === 0) {
      trendMap.value = {}
      return
    }

    const speciesIds = list.map((item: SpeciesItem) => item.id).join(',')
    const trendRes = await api.get(`/stats/price-trend-batch?species_ids=${speciesIds}`)
    const nextTrendMap: Record<number, TrendPoint[]> = {}

    if (trendRes.data && typeof trendRes.data === 'object') {
      Object.entries(trendRes.data).forEach(([id, items]) => {
        nextTrendMap[Number(id)] = Array.isArray(items) ? (items as TrendPoint[]) : []
      })
    }

    trendMap.value = nextTrendMap
  } catch (error: any) {
    if (isAuthError(error)) return
    errorMsg.value = apiErrorMessage(error, '加载首页数据')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDashboard()
})
</script>
