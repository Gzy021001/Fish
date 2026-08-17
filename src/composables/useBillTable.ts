import { ref, shallowRef, computed, watch, type Ref } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import * as XLSX from 'xlsx'
import api from '../api'
import { apiErrorMessage, isAuthError } from '../lib/error'
import { dateStr, dateTimeStr, formatMoney, isPackagingItem } from '../lib/utils'
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

  const debouncedSearchFetch = useDebounceFn(() => {
    if (currentPage.value !== 1) {
      currentPage.value = 1
    } else {
      fetchBills()
    }
  }, 300)

  watch(billingSearch, () => {
    debouncedSearchFetch()
  })

  const currentPage = ref(1)
  const pageSize = ref(10)

  watch(currentPage, () => {
    if (activeTab.value !== 'history') {
      fetchBills()
    }
  })

  watch(pageSize, () => {
    currentPage.value = 1
    if (activeTab.value !== 'history') {
      fetchBills()
    }
  })

  const totalItems = ref(0)
  const totalPages = computed(() => Math.ceil(totalItems.value / pageSize.value))

  const paginatedBills = computed(() => {
    if (activeTab.value === 'history') {
      const start = (currentPage.value - 1) * pageSize.value
      return bills.value.slice(start, start + pageSize.value)
    }
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
    try {
      const params = new URLSearchParams()
      params.set('limit', '0')
      if (activeTab.value === 'history') {
        params.set('page_size', '-1')
      } else {
        params.set('page', currentPage.value.toString())
        params.set('page_size', pageSize.value.toString())
      }
      if (activeTab.value === 'history') {
        params.set('status', 'COMPLETED')
      } else if (filterStatus.value) {
        params.set('status', filterStatus.value)
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

      if (res.data && typeof res.data.total === 'number') {
        let items: Bill[] = res.data.items || []
        if (activeTab.value === 'history') {
          items = items.filter((b) => !isPackagingItem(getSpeciesName(b.species_id)))
        }
        bills.value = items
        totalItems.value = activeTab.value === 'history' ? items.length : res.data.total

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

        if (activeTab.value === 'history') {
          bills.value = rawBills.filter((b) => !isPackagingItem(getSpeciesName(b.species_id)))
        } else {
          bills.value = rawBills
        }
        totalItems.value = bills.value.length
      }
    } catch (error: unknown) {
      if (isAuthError(error as ApiError)) return
      console.error('Failed to fetch bills', error)
    }
  }

  const switchTab = (tab: string) => {
    if (activeTab.value === tab) return
    bills.value = []
    activeTab.value = tab
    selectedBillIds.value = []

    if (currentPage.value !== 1) {
      currentPage.value = 1
    } else {
      fetchBills()
    }
  }

  const clearDateFilter = () => {
    filterDateFrom.value = ''
    filterDateTo.value = ''
    filterStatus.value = ''
    fetchBills()
  }

  const exportBills = async () => {
    toast.info('正在准备导出数据...')
    let source: Bill[] = []
    try {
      const params = new URLSearchParams()
      params.set('limit', '0')
      params.set('page_size', '-1')
      params.set('status', activeTab.value === 'current' ? 'DRAFT' : 'COMPLETED')

      if (filterDateFrom.value) params.set('date_from', filterDateFrom.value)
      if (filterDateTo.value) params.set('date_to', filterDateTo.value)
      if (billingSearch.value.trim()) params.set('q', billingSearch.value.trim())

      const res = await api.get(`/bills?${params.toString()}`)
      if (res.data && res.data.items) {
        source = res.data.items
      } else {
        source = Array.isArray(res.data) ? res.data : []
      }
    } catch {
      toast.error('获取导出数据失败')
      return
    }

    if (source.length === 0) {
      toast.info('没有可导出的单据数据')
      return
    }

    const formatNum = (v: number) => {
      if (!Number.isFinite(v)) return '0.00'
      return v.toFixed(2)
    }

    const actualFee = (b: Bill) => ((b.total_amount || 0) - (b.subtotal || 0))

    const exportData = source
      .filter((b) => !isPackagingItem(getSpeciesName(b.species_id)))
      .map((b, i) => ({
        '序号': i + 1,
        '品种': getSpeciesName(b.species_id),
        '单据状态': b.status === 'COMPLETED' ? '已归档' : '草稿',
        '重量': (b.weight ?? 0).toFixed(2),
        '单价（元）': formatNum(b.unit_price),
        '小计（元）': formatNum(b.subtotal),
        '服务费（元）': formatNum(actualFee(b)),
        '总金额（元）': formatNum(b.total_amount),
        '放生日期': dateStr(b.release_date || b.species?.release_date || null),
        '添加时间': dateTimeStr(b.created_at),
      }))

    const worksheet = XLSX.utils.json_to_sheet(exportData)
    const workbook = XLSX.utils.book_new()
    const sheetName = activeTab.value === 'current' ? '最新单据' : '历史单据'
    XLSX.utils.book_append_sheet(workbook, worksheet, sheetName)

    const fileDate = new Date().toISOString().slice(0, 10).replace(/-/g, '')
    const prefix = activeTab.value === 'current' ? '最新单据' : '历史单据'
    XLSX.writeFile(workbook, `${prefix}_${fileDate}.xlsx`)
  }

  const syncBillsToHistory = async () => {
    try {
      const dateStr_new = new Date().toISOString().slice(0, 10)
      const res = await api.post('/bills/sync', { date: dateStr_new })
      if (res.data && res.data.count > 0) {
        toast.success(res.data.message)
        await fetchBills()
      } else {
        toast.info('当前没有符合归档条件的过期单据')
      }
    } catch (error: unknown) {
      if (isAuthError(error as ApiError)) return
      toast.error(apiErrorMessage(error as ApiError, '归档单据'))
    }
  }

  const confirmArchiveBills = async () => {
    if (selectedBillIds.value.length === 0) return
    try {
      const res = await api.post('/bills/archive', { bill_ids: selectedBillIds.value })
      if (res.data && res.data.count > 0) {
        toast.success(res.data.message)
        selectedBillIds.value = []
        await fetchBills()
      } else {
        toast.info('选中的单据可能已经是归档状态')
      }
    } catch (error: unknown) {
      if (isAuthError(error as ApiError)) return
      toast.error(apiErrorMessage(error as ApiError, '归档单据'))
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
    clearDateFilter,
    exportBills,
    confirmArchiveBills,
    confirmDeleteBill,
    confirmBatchDeleteBills,
    executeDeleteBill,
    upsertBill,
  }
}
