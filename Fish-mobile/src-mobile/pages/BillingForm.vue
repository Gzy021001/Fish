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
        <div>
          <label class="mb-1 block text-sm font-medium text-[#8a6b4a]">日期</label>
          <MobileDatePicker
            v-model="formData.release_date"
            title="放生日期"
            placeholder="请选择日期"
          />
        </div>
        
        <div>
          <label class="mb-1 block text-sm font-medium text-[#8a6b4a]">品种 (必填)</label>
          <button
            type="button"
            class="w-full rounded-xl border border-[#d8c1a0] bg-white px-3 py-2.5 text-left text-[#5c4033] outline-none focus:border-[#8b6914] flex items-center justify-between gap-2"
            @click="showSpeciesPicker = true"
          >
            <span :class="!selectedSpecies ? 'text-[#b8a68a]' : ''">
              {{ selectedSpecies ? `${selectedSpecies.name_zh}（${selectedSpecies.default_unit}）` : '请选择品种...' }}
            </span>
            <svg class="h-4 w-4 shrink-0 text-[#8a6b4a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7l4-4 4 4m0 6l4 4-4 4M8 17l-4-4 4-4"></path>
            </svg>
          </button>
        </div>
        
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
        
        <div class="rounded-xl bg-[#fcf7ef] p-3 text-right">
          <span class="text-sm text-[#8a6b4a]">小计金额：</span>
          <span class="text-lg font-bold text-[#8b6914]">¥ {{ subtotal.toFixed(2) }}</span>
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

    <Transition name="sheet">
      <div
        v-if="showSpeciesPicker"
        class="fixed inset-0 z-[100] flex flex-col bg-black/20"
        @click.self="showSpeciesPicker = false"
      >
        <div class="mt-auto flex max-h-[70vh] flex-col rounded-t-3xl bg-[#f7efe2] shadow-2xl">
          <div class="shrink-0 flex items-center justify-between border-b border-[#ead9bc] px-5 py-4">
            <h2 class="text-base font-semibold text-[#5c4033]">选择品种</h2>
            <button
              class="rounded-full bg-white/80 px-3 py-1 text-xs text-[#6d4f32] border border-[#d8c1a0] active:opacity-70"
              @click="showSpeciesPicker = false"
            >
              取消
            </button>
          </div>

          <div class="shrink-0 px-5 py-3">
            <div class="relative">
              <svg class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#b8a68a]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
              <input
                v-model="speciesSearch"
                type="text"
                class="w-full rounded-xl border border-[#d8c1a0] bg-white py-2.5 pl-9 pr-3 text-sm text-[#5c4033] outline-none focus:border-[#8b6914]"
                placeholder="搜索品种名称..."
              />
            </div>
          </div>

          <div class="flex-1 overflow-y-auto px-5 pb-6">
            <div v-if="filteredSpeciesList.length === 0" class="py-10 text-center text-sm text-[#8a6b4a]">
              {{ speciesSearch ? '没有匹配的品种' : '暂无品种数据' }}
            </div>
            <div v-else class="space-y-1.5">
              <button
                v-for="sp in filteredSpeciesList"
                :key="sp.id"
                type="button"
                class="w-full rounded-xl px-4 py-3 text-left transition-colors active:bg-[#ebd9be]"
                :class="sp.id === formData.species_id ? 'bg-[#ebd9be] ring-1 ring-[#8b6914]/30' : 'bg-white'"
                @click="selectSpecies(sp)"
              >
                <div class="flex items-center justify-between gap-3">
                  <div class="min-w-0">
                    <p class="truncate text-sm font-medium text-[#5c4033]">{{ sp.name_zh }}</p>
                    <p class="mt-0.5 text-xs text-[#8a6b4a]">{{ sp.default_unit || '--' }}</p>
                  </div>
                  <div class="shrink-0 text-right">
                    <p class="text-sm font-semibold text-[#8b6914]">¥{{ Number(sp.default_price || 0).toFixed(2) }}</p>
                    <p class="text-[10px] text-[#b8a68a]">参考价</p>
                  </div>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MobileDatePicker from '../components/MobileDatePicker.vue'
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
const showSpeciesPicker = ref(false)
const speciesSearch = ref('')

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

const filteredSpeciesList = computed(() => {
  const q = speciesSearch.value.trim().toLowerCase()
  if (!q) return speciesList.value
  return speciesList.value.filter(sp => sp.name_zh.toLowerCase().includes(q))
})

const subtotal = computed(() => {
  const w = parseFloat(String(formData.value.weight)) || 0
  const p = parseFloat(String(formData.value.unit_price)) || 0
  return w * p
})

const selectSpecies = (sp: any) => {
  formData.value.species_id = sp.id
  showSpeciesPicker.value = false
  speciesSearch.value = ''
  if (!isEdit.value) {
    formData.value.unit_price = String(sp.default_price || '')
  }
}

const fetchSpecies = async () => {
  loadingSpecies.value = true
  try {
    const res = await api.get('/species', { params: { include_images: false, limit: 1000 } })
    speciesList.value = Array.isArray(res.data) ? res.data : []
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
