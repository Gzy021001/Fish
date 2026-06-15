import { defineStore } from 'pinia'

type BillingListState = {
  page: number
  q: string
  dateFrom: string
  dateTo: string
}

type BillingContextState = BillingListState & {
  billIds: number[]
  currentIndex: number
}

const getDefaultState = (): BillingContextState => ({
  page: 1,
  q: '',
  dateFrom: '',
  dateTo: '',
  billIds: [],
  currentIndex: -1,
})

export const useBillingContextStore = defineStore('mobile-billing-context', {
  state: (): BillingContextState => getDefaultState(),
  actions: {
    restoreListState(): BillingListState {
      return {
        page: this.page,
        q: this.q,
        dateFrom: this.dateFrom,
        dateTo: this.dateTo,
      }
    },
    setListState(payload: BillingListState) {
      this.page = payload.page
      this.q = payload.q
      this.dateFrom = payload.dateFrom
      this.dateTo = payload.dateTo
    },
    setPageBills(ids: number[], currentIndex = -1) {
      this.billIds = ids
      this.currentIndex = currentIndex
    },
    setCurrentIndex(index: number) {
      this.currentIndex = index
    },
    resetNavigation() {
      this.billIds = []
      this.currentIndex = -1
    },
  },
})
