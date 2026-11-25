import { ref, computed, watch } from 'vue'
import api from '../api'
import { isAuthError } from '../lib/error'
import type { ApiError } from '../types'

/** 随喜汇总行：后端 /bills?group_by_date=1 按放生日期聚合出来的一天一行 */
export interface SuixiDailyRow {
  release_date: string | null
  alipay_amount: number | null
  wechat1_amount: number | null
  wechat2_amount: number | null
  suixi_amount: number | null
  /** 本周现场随喜（整周一个值，记在该周第一张单据上） */
  weekly_donation?: number | null
  /** 当天车费/船费（模板表尾的费用行） */
  expense_car?: number
  expense_ship?: number
  expense_other?: number
  /** 其它支出明细（冰块/打包袋等），列表里用小字标注 */
  expense_other_items?: { name: string; amount: number }[]
  expense_total?: number
}

/**
 * 随喜汇总（独立模块）的数据层：
 * 已归档 + 排除打包耗材 + 只看带随喜记录的单据，按放生日期一天一行；
 * 微信拆两列（微信1 = 当天第一笔，微信2 = 当天其余合计，与导出模板一致）。
 */
export function useSuixiSummary() {
  const rows = ref<SuixiDailyRow[]>([])
  const filterDateFrom = ref('')
  const filterDateTo = ref('')
  const currentPage = ref(1)
  const pageSize = ref(10)
  const totalItems = ref(0)
  const loading = ref(false)
  // 四类合计（全量口径，与当前页无关）
  const sumAlipay = ref(0)
  const sumWechat1 = ref(0)
  const sumWechat2 = ref(0)
  const sumSuixi = ref(0)
  // 现场随喜合计（全量口径，与当前页无关）
  const sumWeeklyDonation = ref(0)
  // 车费/船费合计（与当前筛选一致）
  const sumExpenseCar = ref(0)
  const sumExpenseShip = ref(0)
  const sumExpense = ref(0)

  const totalPages = computed(() => Math.ceil(totalItems.value / pageSize.value))

  // 翻页请求序号：只接受最后一次请求的响应，防止旧页响应后到覆盖新页数据
  let fetchGen = 0

  watch(currentPage, () => {
    fetchSummary()
  })

  watch(pageSize, () => {
    if (currentPage.value !== 1) {
      currentPage.value = 1 // watch(currentPage) 统一拉取
    } else {
      fetchSummary()
    }
  })

  const fetchSummary = async () => {
    const gen = ++fetchGen
    loading.value = true
    try {
      const params = new URLSearchParams()
      params.set('limit', '0')
      params.set('status', 'COMPLETED')
      params.set('exclude_packaging', '1')
      params.set('has_suixi', '1')
      params.set('group_by_date', '1')
      params.set('page', currentPage.value.toString())
      params.set('page_size', pageSize.value.toString())
      if (filterDateFrom.value) params.set('date_from', filterDateFrom.value)
      if (filterDateTo.value) params.set('date_to', filterDateTo.value)

      const res = await api.get(`/bills?${params.toString()}`)
      if (gen !== fetchGen) return

      const data = res.data
      if (data && typeof data.total === 'number') {
        rows.value = data.items || []
        totalItems.value = data.total
        sumAlipay.value = Number(data.sum_alipay || 0)
        sumWechat1.value = Number(data.sum_wechat1 ?? data.sum_wechat ?? 0)
        sumWechat2.value = Number(data.sum_wechat2 || 0)
        sumSuixi.value = Number(data.sum_suixi || 0)
        sumWeeklyDonation.value = Number(data.sum_weekly_donation || 0)
        sumExpenseCar.value = Number(data.sum_expense_car || 0)
        sumExpenseShip.value = Number(data.sum_expense_ship || 0)
        sumExpense.value = Number(data.sum_expense || 0)
      } else {
        rows.value = []
        totalItems.value = 0
        sumAlipay.value = 0
        sumWechat1.value = 0
        sumWechat2.value = 0
        sumSuixi.value = 0
        sumWeeklyDonation.value = 0
        sumExpenseCar.value = 0
        sumExpenseShip.value = 0
        sumExpense.value = 0
      }

      // 删除/筛选后当前页可能越界：回退到最后一页（watch(currentPage) 统一重新拉取）
      const maxPage = Math.max(1, Math.ceil(totalItems.value / pageSize.value))
      if (currentPage.value > maxPage) {
        currentPage.value = maxPage
      }
    } catch (error: unknown) {
      if (gen !== fetchGen) return
      if (isAuthError(error as ApiError)) return
      console.error('Failed to fetch suixi summary', error)
    } finally {
      if (gen === fetchGen) loading.value = false
    }
  }

  const refetchFromFirstPage = async () => {
    if (currentPage.value !== 1) {
      currentPage.value = 1 // 触发 watch(currentPage) 自动拉取
    } else {
      await fetchSummary()
    }
  }

  /** 应用日期筛选（起止写反时自动交换） */
  const applyFilters = async () => {
    let from = filterDateFrom.value || ''
    let to = filterDateTo.value || ''
    if (from && to && from > to) {
      const swap = from
      from = to
      to = swap
    }
    filterDateFrom.value = from
    filterDateTo.value = to
    await refetchFromFirstPage()
  }

  const resetFilters = async () => {
    filterDateFrom.value = ''
    filterDateTo.value = ''
    await refetchFromFirstPage()
  }

  return {
    rows,
    filterDateFrom,
    filterDateTo,
    currentPage,
    pageSize,
    totalItems,
    totalPages,
    loading,
    sumAlipay,
    sumWechat1,
    sumWechat2,
    sumSuixi,
    sumWeeklyDonation,
    sumExpenseCar,
    sumExpenseShip,
    sumExpense,
    fetchSummary,
    applyFilters,
    resetFilters,
  }
}
