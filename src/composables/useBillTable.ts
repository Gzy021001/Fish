import { ref, computed, watch, type Ref } from "vue"
import * as XLSX from "xlsx"
import api from "../api"
import { apiErrorMessage, isAuthError } from "../lib/error"
import { dateStr, dateTimeStr, formatMoney } from "../lib/utils"
import { useToast } from "./useToast"

export function useBillTable(speciesList: Ref<any[]>) {
  const toast = useToast()
  const activeTab = ref("current")
  const filterDateFrom = ref("")
  const filterDateTo = ref("")
  const billingSearch = ref("")
  const bills = ref<any[]>([])
  const selectedBillIds = ref<number[]>([])

  const deleteConfirm = ref({
    show: false,
    id: null as number | null,
    isBatch: false,
  })

  watch(
    () => activeTab.value,
    (newTab) => {
      billingSearch.value = ""
      if (newTab === "history") {
        filterDateFrom.value = ""
        filterDateTo.value = ""
      }
    },
  )

  watch(billingSearch, () => {
    currentPage.value = 1
  })

  const currentPage = ref(1)
  const pageSize = 10

  const filteredBills = computed(() => {
    const q = billingSearch.value.trim().toLowerCase()
    return q
      ? bills.value.filter((b: any) => {
        const sp = speciesList.value.find((s: any) => s.id === b.species_id)
        return sp && sp.name_zh.toLowerCase().includes(q)
      })
      : bills.value
  })

  const totalItems = computed(() => filteredBills.value.length)
  const totalPages = computed(() => Math.ceil(totalItems.value / pageSize))

  const paginatedBills = computed(() => {
    const start = (currentPage.value - 1) * pageSize
    const end = start + pageSize
    return filteredBills.value.slice(start, end)
  })

  const tableSumWeight = computed(() =>
    Number(
      filteredBills.value.reduce((s, b) => s + (b.weight || 0), 0).toFixed(2),
    ),
  )

  const tableSumSubtotal = computed(() =>
    Number(
      filteredBills.value.reduce((s, b) => s + (b.subtotal || 0), 0).toFixed(2),
    ),
  )

  const tableSumFee = computed(() =>
    Number(
      filteredBills.value
        .reduce((s, b) => s + ((b.total_amount || 0) - (b.subtotal || 0)), 0)
        .toFixed(2),
    ),
  )

  const tableSumTotal = computed(() =>
    Number(
      filteredBills.value
        .reduce((s, b) => s + (b.total_amount || 0), 0)
        .toFixed(2),
    ),
  )

  const displayedPages = computed(() => {
    const pages = []
    let start = Math.max(1, currentPage.value - 2)
    let end = Math.min(totalPages.value, start + 4)

    if (end - start < 4) {
      start = Math.max(1, end - 4)
    }

    for (let i = start; i <= end; i++) {
      pages.push(i)
    }
    return pages
  })

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
    const sp = speciesList.value.find((s) => s.id === id)
    return sp ? sp.name_zh : `未知品种(${id})`
  }

  const formatFee = (b: any) => {
    const actualFee = (b.total_amount || 0) - (b.subtotal || 0)
    return formatMoney(actualFee)
  }

  const formatDateLabel = (d: string) => {
    if (!d) return ""
    const parts = d.split("-")
    if (parts.length !== 3) return d
    return `${parseInt(parts[1])}月${parseInt(parts[2])}日`
  }

  const dateRangeLabel = computed(() => {
    const from = filterDateFrom.value
    const to = filterDateTo.value
    if (from && to) return `${formatDateLabel(from)} — ${formatDateLabel(to)}`
    if (from) return `${formatDateLabel(from)} 起`
    if (to) return `至 ${formatDateLabel(to)}`
    return ""
  })

  const fetchBills = async () => {
    try {
      const params = new URLSearchParams()
      params.set("limit", "0")
      if (filterDateFrom.value) {
        params.set("date_from", filterDateFrom.value)
      }
      if (filterDateTo.value) {
        params.set("date_to", filterDateTo.value)
      }
      const res = await api.get(`/bills?${params.toString()}`)
      bills.value = res.data || []
      currentPage.value = 1
    } catch (error: any) {
      if (isAuthError(error)) return
      console.error("Failed to fetch bills", error)
    }
  }

  const switchTab = (tab: string) => {
    activeTab.value = tab
    selectedBillIds.value = []
    currentPage.value = 1
    fetchBills()
  }

  const clearDateFilter = () => {
    filterDateFrom.value = ""
    filterDateTo.value = ""
    fetchBills()
  }

  const exportBills = () => {
    const source = filteredBills.value
    if (source.length === 0) {
      toast.info("没有可导出的单据数据")
      return
    }

    const formatNum = (v: number) => {
      if (!Number.isFinite(v)) return "0.00"
      return v.toFixed(2)
    }

    const actualFee = (b: any) => ((b.total_amount || 0) - (b.subtotal || 0))

    const exportData = source.map((b, i) => ({
      序号: i + 1,
      品种: getSpeciesName(b.species_id),
      重量: b.weight.toFixed(2),
      "单价（元）": formatNum(b.unit_price),
      "小计（元）": formatNum(b.subtotal),
      "服务费（元）": formatNum(actualFee(b)),
      "总金额（元）": formatNum(b.total_amount),
      放生日期: dateStr(b.release_date || b.created_at),
      添加时间: dateTimeStr(b.created_at),
    }))

    const worksheet = XLSX.utils.json_to_sheet(exportData)
    const workbook = XLSX.utils.book_new()
    const sheetName = activeTab.value === "current" ? "最新单据" : "历史单据"
    XLSX.utils.book_append_sheet(workbook, worksheet, sheetName)

    const fileDate = new Date().toISOString().slice(0, 10).replace(/-/g, "")
    const prefix = activeTab.value === "current" ? "最新单据" : "历史单据"
    XLSX.writeFile(workbook, `${prefix}_${fileDate}.xlsx`)
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
        for (const id of selectedBillIds.value) {
          await api.delete(`/bills/${id}`)
        }
        bills.value = bills.value.filter(
          (b) => !selectedBillIds.value.includes(b.id),
        )
        selectedBillIds.value = []
        deleteConfirm.value.show = false
        toast.success("批量删除成功！")
      } catch (error: any) {
        if (isAuthError(error)) return
        toast.error(apiErrorMessage(error, "批量删除"))
        deleteConfirm.value.show = false
        await fetchBills()
      }
    } else {
      const id = deleteConfirm.value.id
      if (!id) return

      try {
        await api.delete(`/bills/${id}`)
        deleteConfirm.value.show = false
        bills.value = bills.value.filter((b) => b.id !== id)
      } catch (error: any) {
        if (isAuthError(error)) return
        toast.error(apiErrorMessage(error, "删除单据"))
      }
    }
  }

  const upsertBill = (data: any) => {
    const index = bills.value.findIndex((b: any) => b.id === data.id)
    if (index !== -1) {
      bills.value[index] = data
    } else {
      bills.value.unshift(data)
    }
    currentPage.value = 1
  }

  return {
    activeTab,
    filterDateFrom,
    filterDateTo,
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
    displayedPages,
    isAllSelected,
    toggleSelectAll,
    getSpeciesName,
    formatFee,
    fetchBills,
    switchTab,
    clearDateFilter,
    exportBills,
    confirmDeleteBill,
    confirmBatchDeleteBills,
    executeDeleteBill,
    upsertBill,
  }
}
