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
