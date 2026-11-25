import { ref } from 'vue'
import type { Bill } from '../types'

/**
 * 单据详情弹窗状态。
 * 详情内容只读展示，弹窗不再拉取「操作记录」。
 */
export function useBillAudit() {
  const showViewModal = ref(false)
  const viewingBill = ref<Bill | null>(null)

  const viewBill = (b: Bill) => {
    viewingBill.value = b
    showViewModal.value = true
  }

  return {
    showViewModal,
    viewingBill,
    viewBill,
  }
}
