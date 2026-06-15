<template>
  <section class="p-4 space-y-4">
    <div class="flex items-center justify-between gap-3">
      <h1 class="text-xl font-serif text-[#6d4f32]">品种</h1>
      <button
        class="rounded-full border border-[#d8c1a0] bg-white/80 px-3 py-1.5 text-xs text-[#6d4f32] active:opacity-70"
        :disabled="loading"
        @click="fetchSpecies"
      >
        {{ loading ? '刷新中...' : '刷新' }}
      </button>
    </div>

    <input
      v-model.trim="searchText"
      class="w-full rounded-2xl border border-[#d8c1a0] bg-white px-4 py-3 text-sm text-[#5c4033] outline-none"
      placeholder="搜索品种名称"
    />

    <p v-if="errorMsg" class="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-600">
      {{ errorMsg }}
    </p>

    <div v-if="loading && filteredSpecies.length === 0" class="rounded-2xl bg-white/90 p-6 text-center text-sm text-[#8a6b4a] shadow-sm">
      正在加载品种数据...
    </div>

    <div v-else-if="filteredSpecies.length === 0" class="rounded-2xl bg-white/90 p-6 text-center text-sm text-[#8a6b4a] shadow-sm">
      {{ searchText ? '没有匹配的品种' : '暂无品种数据' }}
    </div>

    <div v-else class="space-y-3">
      <article
        v-for="item in filteredSpecies"
        :key="item.id"
        class="rounded-2xl bg-white/90 p-4 shadow-sm"
      >
        <div class="flex items-start gap-3">
          <img
            v-if="item.image_url"
            :src="item.image_url"
            :alt="item.name_zh"
            class="h-16 w-16 shrink-0 rounded-2xl object-cover border border-[#ead9bc]"
          />
          <div
            v-else
            class="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-[#f6ead5] text-lg font-semibold text-[#8b6914]"
          >
            {{ item.name_zh.slice(0, 1) }}
          </div>

          <div class="min-w-0 flex-1">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="truncate text-sm font-semibold text-[#5c4033]">{{ item.name_zh }}</p>
                <p class="mt-1 text-xs text-[#8a6b4a]">{{ item.default_unit || '未设置单位' }}</p>
              </div>
              <p class="shrink-0 text-sm font-semibold text-[#8b6914]">
                {{ formatPrice(item.default_price) }}
              </p>
            </div>

            <p v-if="item.supplier_name" class="mt-3 text-xs text-[#8a6b4a]">
              供应商：{{ item.supplier_name }}
            </p>
            <p v-if="item.release_date" class="mt-1 text-xs text-[#8a6b4a]">
              放生日期：{{ item.release_date }}
            </p>
          </div>
        </div>
      </article>
    </div>
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
  image_url?: string | null
  supplier_name?: string | null
  release_date?: string | null
}

const loading = ref(false)
const errorMsg = ref('')
const searchText = ref('')
const speciesList = ref<SpeciesItem[]>([])

const filteredSpecies = computed(() => {
  const keyword = searchText.value.trim().toLowerCase()
  if (!keyword) return speciesList.value
  return speciesList.value.filter(item =>
    item.name_zh.toLowerCase().includes(keyword)
  )
})

const formatPrice = (value: number) => {
  return `¥${Number(value || 0).toFixed(2)}`
}

const fetchSpecies = async () => {
  loading.value = true
  errorMsg.value = ''

  try {
    const response = await api.get('/species?include_images=false')
    speciesList.value = Array.isArray(response.data) ? response.data : []
  } catch (error: any) {
    if (isAuthError(error)) return
    errorMsg.value = apiErrorMessage(error, '加载品种列表')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchSpecies()
})
</script>
