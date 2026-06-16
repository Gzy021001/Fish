import { ref, shallowRef, computed, watch, type Ref } from "vue"
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
  const bills = shallowRef<any[]>([])
  const selectedBillIds = ref<number[]>([])

  const deleteConfirm = ref({
    show: false,
    id: null as number | null,
    isBatch: false,
  })

  // activeTab 的状态同步已在 switchTab 中手动处理，避免触发多余的 watcher

  watch(billingSearch, () => {
    if (currentPage.value !== 1) {
      currentPage.value = 1 // 这会触发 currentPage 的 watcher 来请求数据
    } else {
      fetchBills()
    }
  })

  const currentPage = ref(1)
  const pageSize = ref(10)

  watch(currentPage, () => {
    fetchBills()
  })

  watch(pageSize, () => {
    if (currentPage.value !== 1) {
      currentPage.value = 1
    } else {
      fetchBills()
    }
  })

  const filteredBills = computed(() => {
    return bills.value
  })

  const totalItems = ref(0)
  const totalPages = computed(() => Math.ceil(totalItems.value / pageSize.value))

  const paginatedBills = computed(() => {
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
      params.set("limit", "0") // Disable old limit
      params.set("page", currentPage.value.toString())
      params.set("page_size", pageSize.value.toString())
      params.set("status", activeTab.value === "current" ? "DRAFT" : "COMPLETED")

      if (filterDateFrom.value) {
        params.set("date_from", filterDateFrom.value)
      }
      if (filterDateTo.value) {
        params.set("date_to", filterDateTo.value)
      }
      if (billingSearch.value.trim()) {
        params.set("q", billingSearch.value.trim())
      }


      const res = await api.get(`/bills?${params.toString()}`)

      if (res.data && typeof res.data.total === 'number') {
        bills.value = res.data.items || []
        totalItems.value = res.data.total

        tableSumWeight.value = res.data.sum_weight || 0
        tableSumSubtotal.value = res.data.sum_subtotal || 0
        tableSumTotal.value = res.data.sum_total_amount || 0
        tableSumFee.value = tableSumTotal.value - tableSumSubtotal.value
      } else {
        // Fallback
        bills.value = Array.isArray(res.data) ? res.data : []
        totalItems.value = bills.value.length

        tableSumWeight.value = Number(bills.value.reduce((s, b) => s + (b.weight || 0), 0).toFixed(2))
        tableSumSubtotal.value = Number(bills.value.reduce((s, b) => s + (b.subtotal || 0), 0).toFixed(2))
        tableSumTotal.value = Number(bills.value.reduce((s, b) => s + (b.total_amount || 0), 0).toFixed(2))
        tableSumFee.value = tableSumTotal.value - tableSumSubtotal.value
      }
    } catch (error: any) {
      if (isAuthError(error)) return
      console.error("Failed to fetch bills", error)
    }
  }

  const switchTab = (tab: string) => {
    if (activeTab.value === tab) return
    bills.value = [] // 立即清空当前数据，消除显示旧数据的视觉延迟
    activeTab.value = tab
    selectedBillIds.value = []

    // 切换 tab 时保留搜索和日期筛选，只由 status 参数区分不同标签
    if (currentPage.value !== 1) {
      currentPage.value = 1
    } else {
      fetchBills()
    }
  }

  const clearDateFilter = () => {
    filterDateFrom.value = ""
    filterDateTo.value = ""
    fetchBills()
  }

  const exportBills = async () => {
    toast.info("正在准备导出数据...")
    let source = []
    try {
      const params = new URLSearchParams()
      params.set("limit", "0")
      params.set("page_size", "-1") // 获取全部
      params.set("status", activeTab.value === "current" ? "DRAFT" : "COMPLETED")

      if (filterDateFrom.value) params.set("date_from", filterDateFrom.value)
      if (filterDateTo.value) params.set("date_to", filterDateTo.value)
      if (billingSearch.value.trim()) params.set("q", billingSearch.value.trim())


      const res = await api.get(`/bills?${params.toString()}`)
      if (res.data && res.data.items) {
        source = res.data.items
      } else {
        source = Array.isArray(res.data) ? res.data : []
      }
    } catch (error) {
      toast.error("获取导出数据失败")
      return
    }

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
        selectedBillIds.value = []
        deleteConfirm.value.show = false
        toast.success("批量删除成功！")
        await fetchBills()
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
        await fetchBills()
      } catch (error: any) {
        if (isAuthError(error)) return
        toast.error(apiErrorMessage(error, "删除单据"))
      }
    }
  }

  const upsertBill = async (data: any) => {
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
    confirmDeleteBill,
    confirmBatchDeleteBills,
    executeDeleteBill,
    upsertBill,
  }
}
