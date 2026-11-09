import { ref, shallowRef, computed, watch, type Ref } from 'vue'
import api from '../api'
import { apiErrorMessage, isAuthError } from '../lib/error'
import { formatMoney } from '../lib/utils'
import { useToast } from './useToast'
import type { Species, Bill, ApiError } from '../types'

export function useBillTable(speciesList: Ref<Species[]>) {
  const toast = useToast()
  const activeTab = ref('current')
  const filterDateFrom = ref('')
  const filterDateTo = ref('')
  const billingSearch = ref('')
  const filterStatus = ref('')
  const bills = shallowRef<Bill[]>([])
  const selectedBillIds = ref<number[]>([])

  const deleteConfirm = ref({
    show: false,
    id: null as number | null,
    isBatch: false,
  })

  const speciesMap = computed(() => {
    const map = new Map<number, Species>()
    for (const sp of speciesList.value) {
      map.set(sp.id, sp)
    }
    return map
  })

  const currentPage = ref(1)
  const pageSize = ref(10)
  // 翻页请求序号：只接受最后一次请求的响应，防止旧页响应后到覆盖新页数据
  let fetchGen = 0

  watch(currentPage, () => {
    fetchBills()
  })

  watch(pageSize, () => {
    if (currentPage.value !== 1) {
      currentPage.value = 1 // watch(currentPage) 统一拉取
    } else {
      fetchBills()
    }
  })

  const totalItems = ref(0)
  const totalPages = computed(() => Math.ceil(totalItems.value / pageSize.value))

  const paginatedBills = computed(() => {
    // 历史 tab 已改为服务端分页（exclude_packaging 后端过滤），返回的即是当前页
    return bills.value
  })

  const tableSumWeight = ref(0)
  const tableSumSubtotal = ref(0)
  const tableSumFee = ref(0)
  const tableSumTotal = ref(0)

  const isAllSelected = computed({
    get: () => {
      return (
        paginatedBills.value.length > 0 &&
        paginatedBills.value.every((b) => selectedBillIds.value.includes(b.id))
      )
    },
    set: (val) => {
      if (val) {
        const idsToAdd = paginatedBills.value
          .filter((b) => !selectedBillIds.value.includes(b.id))
          .map((b) => b.id)
        selectedBillIds.value.push(...idsToAdd)
      } else {
        const paginatedIds = paginatedBills.value.map((b) => b.id)
        selectedBillIds.value = selectedBillIds.value.filter(
          (id) => !paginatedIds.includes(id),
        )
      }
    },
  })

  const toggleSelectAll = (e: Event) => {
    isAllSelected.value = (e.target as HTMLInputElement).checked
  }

  const getSpeciesName = (id: number) => {
    const sp = speciesMap.value.get(id)
    return sp ? sp.name_zh : `未知品种(${id})`
  }

  const formatFee = (b: Bill) => {
    const actualFee = (b.total_amount || 0) - (b.subtotal || 0)
    return formatMoney(actualFee)
  }

  const formatDateLabel = (d: string) => {
    if (!d) return ''
    const parts = d.split('-')
    if (parts.length !== 3) return d
    return `${parseInt(parts[1])}月${parseInt(parts[2])}日`
  }

  const dateRangeLabel = computed(() => {
    const from = filterDateFrom.value
    const to = filterDateTo.value
    if (from && to) return `${formatDateLabel(from)} — ${formatDateLabel(to)}`
    if (from) return `${formatDateLabel(from)} 起`
    if (to) return `至 ${formatDateLabel(to)}`
    return ''
  })

  const fetchBills = async () => {
    const gen = ++fetchGen
    try {
      const params = new URLSearchParams()
      params.set('limit', '0')
      if (activeTab.value === 'history') {
        params.set('status', 'COMPLETED')
        params.set('page', currentPage.value.toString())
        params.set('page_size', pageSize.value.toString())
        // 历史视图排除打包耗材（冰/打包/袋），后端过滤，不再全量拉到前端
        params.set('exclude_packaging', '1')
      } else {
        params.set('page', currentPage.value.toString())
        params.set('page_size', pageSize.value.toString())
        if (filterStatus.value) {
          params.set('status', filterStatus.value)
        }
      }

      if (filterDateFrom.value) {
        params.set('date_from', filterDateFrom.value)
      }
      if (filterDateTo.value) {
        params.set('date_to', filterDateTo.value)
      }
      if (billingSearch.value.trim()) {
        params.set('q', billingSearch.value.trim())
      }

      const res = await api.get(`/bills?${params.toString()}`)
      if (gen !== fetchGen) return

      if (res.data && typeof res.data.total === 'number') {
        bills.value = res.data.items || []
        totalItems.value = res.data.total

        tableSumWeight.value = res.data.sum_weight || 0
        tableSumSubtotal.value = res.data.sum_subtotal || 0
        tableSumTotal.value = res.data.sum_total_amount || 0
        tableSumFee.value = tableSumTotal.value - tableSumSubtotal.value
      } else {
        const rawBills: Bill[] = Array.isArray(res.data) ? res.data : []
        tableSumWeight.value = Number(rawBills.reduce((s, b) => s + (b.weight || 0), 0).toFixed(2))
        tableSumSubtotal.value = Number(rawBills.reduce((s, b) => s + (b.subtotal || 0), 0).toFixed(2))
        tableSumTotal.value = Number(rawBills.reduce((s, b) => s + (b.total_amount || 0), 0).toFixed(2))
        tableSumFee.value = tableSumTotal.value - tableSumSubtotal.value
        bills.value = rawBills
        totalItems.value = bills.value.length
      }

      // 删除/筛选后当前页可能越界：回退到最后一页（watch(currentPage) 统一重新拉取）
      const maxPage = Math.max(1, Math.ceil(totalItems.value / pageSize.value))
      if (currentPage.value > maxPage) {
        currentPage.value = maxPage
      }
    } catch (error: unknown) {
      if (gen !== fetchGen) return
      if (isAuthError(error as ApiError)) return
      console.error('Failed to fetch bills', error)
    }
  }

  const switchTab = (tab: string) => {
    if (activeTab.value === tab) return
    bills.value = []
    activeTab.value = tab
    selectedBillIds.value = []
    // 历史单据没有状态筛选，清掉避免徽标计数与面板不一致
    if (tab === 'history') {
      filterStatus.value = ''
    }

    if (currentPage.value !== 1) {
      currentPage.value = 1 // watch(currentPage) 统一拉取
    } else {
      fetchBills()
    }
  }

  // 筛选变化后统一回到第一页重新拉取；避免依赖 watch 副作用导致漏拉或双拉
  const refetchFromFirstPage = async () => {
    if (currentPage.value !== 1) {
      currentPage.value = 1 // 触发 watch(currentPage) 自动拉取
    } else {
      await fetchBills()
    }
  }

  const clearDateFilter = () => {
    filterDateFrom.value = ''
    filterDateTo.value = ''
    filterStatus.value = ''
    fetchBills()
  }

  const exportBills = async () => {
    // 有勾选 -> 只导勾选的单据；没勾选 -> 全量导出（不再要求先设置日期范围）
    const params: Record<string, string> = {}
    if (selectedBillIds.value.length > 0) {
      params.bill_ids = selectedBillIds.value.join(',')
    }
    toast.info(
      selectedBillIds.value.length > 0
        ? `正在导出选中的 ${selectedBillIds.value.length} 条单据...`
        : '正在导出全部单据...',
    )
    try {
      const res = await api.get('/bills/export', {
        params,
        responseType: 'blob',
        timeout: 120000,
      })
      const blob = res.data as Blob
      if (!blob || blob.size === 0) {
        toast.error('导出失败：文件为空')
        return
      }
      let filename = '慈悲组购生明细表.xlsx'
      const disposition = res.headers?.['content-disposition'] as string | undefined
      if (disposition) {
        const match = disposition.match(/filename\*=UTF-8''([^;]+)/i)
        if (match) filename = decodeURIComponent(match[1])
      }
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = filename
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
      URL.revokeObjectURL(url)
      toast.success('导出完成')
    } catch (error: unknown) {
      if (isAuthError(error as ApiError)) return
      toast.error(apiErrorMessage(error as ApiError, '导出明细表'))
    }
  }

  const confirmDeleteBill = (id: number) => {
    deleteConfirm.value = { show: true, id, isBatch: false }
  }

  const confirmBatchDeleteBills = () => {
    if (selectedBillIds.value.length === 0) return
    deleteConfirm.value = { show: true, id: null, isBatch: true }
  }

  const executeDeleteBill = async () => {
    if (deleteConfirm.value.isBatch) {
      try {
        await Promise.all(selectedBillIds.value.map((id) => api.delete(`/bills/${id}`)))
        selectedBillIds.value = []
        deleteConfirm.value.show = false
        toast.success('批量删除成功！')
        await fetchBills()
      } catch (error: unknown) {
        if (isAuthError(error as ApiError)) return
        toast.error(apiErrorMessage(error as ApiError, '批量删除'))
        deleteConfirm.value.show = false
        await fetchBills()
      }
    } else {
      const id = deleteConfirm.value.id
      if (!id) return

      try {
        await api.delete(`/bills/${id}`)
        deleteConfirm.value.show = false
        await fetchBills()
      } catch (error: unknown) {
        if (isAuthError(error as ApiError)) return
        toast.error(apiErrorMessage(error as ApiError, '删除单据'))
      }
    }
  }

  const upsertBill = async () => {
    if (currentPage.value === 1) {
      await fetchBills()
    } else {
      currentPage.value = 1
    }
  }

  return {
    activeTab,
    filterDateFrom,
    filterDateTo,
    filterStatus,
    dateRangeLabel,
    billingSearch,
    bills,
    selectedBillIds,
    deleteConfirm,
    pageSize,
    currentPage,
    totalPages,
    totalItems,
    paginatedBills,
    tableSumWeight,
    tableSumSubtotal,
    tableSumFee,
    tableSumTotal,
    isAllSelected,
    toggleSelectAll,
    getSpeciesName,
    formatFee,
    fetchBills,
    switchTab,
    refetchFromFirstPage,
    clearDateFilter,
    exportBills,
    confirmDeleteBill,
    confirmBatchDeleteBills,
    executeDeleteBill,
    upsertBill,
  }
}
