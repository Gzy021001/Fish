import { computed, ref, type Ref } from 'vue'
import api from '../api'
import { isAuthError } from '../lib/error'
import { diffFields } from '../lib/utils'
import type { Species, Bill, AuditLog, ApiError } from '../types'

export function useBillAudit(speciesList: Ref<Species[]>) {
  const showViewModal = ref(false)
  const viewingBill = ref<Bill | null>(null)
  const viewingBillLogs = ref<AuditLog[]>([])
  const loadingLogs = ref(false)

  const getSpeciesName = (id: number) => {
    const sp = speciesList.value.find((s) => s.id === id)
    return sp ? sp.name_zh : `未知品种(${id})`
  }

  const formatAction = (action: string) => {
    const map: Record<string, string> = {
      CREATE: '新增单据',
      UPDATE: '修改单据',
      DELETE: '删除单据',
      COMPLETED: '单据归档',
    }
    return map[action] || action
  }

  const formatUpdateDiff = (
    oldDataStr: string | null,
    newDataStr: string | null,
  ) => {
    if (!oldDataStr || !newDataStr) return []
    try {
      const result = diffFields(oldDataStr, newDataStr, [
        {
          key: 'species_id',
          label: '品种',
          format: (v) => getSpeciesName(v as number),
        },
        { key: 'weight', label: '重量', format: (v) => String(v) },
        { key: 'unit_price', label: '单价', format: (v) => String(v) },
        { key: 'release_date', label: '放生日期', format: (v) => v ? String(v).slice(0, 10) : '-' },
      ])

      const oldD = JSON.parse(oldDataStr)
      const newD = JSON.parse(newDataStr)
      if (oldD.fee_type !== newD.fee_type || oldD.fee_value !== newD.fee_value) {
        const oldFee = String(Number(oldD.fee_value || 0).toFixed(2))
        const newFee = String(Number(newD.fee_value || 0).toFixed(2))
        if (oldFee !== newFee)
          result.push({ label: '服务费', old: oldFee, new: newFee })
      }
      return result
    } catch {
      return []
    }
  }

  const filteredViewingBillLogs = computed(() =>
    viewingBillLogs.value.filter(
      (log) => log.action !== 'UPDATE' || formatUpdateDiff(log.old_data, log.new_data).length > 0,
    ),
  )

  const viewBill = async (b: Bill) => {
    viewingBill.value = b
    viewingBillLogs.value = []
    showViewModal.value = true
    loadingLogs.value = true
    try {
      const res = await api.get(`/logs/bill/${b.id}`)
      viewingBillLogs.value = Array.isArray(res.data) ? res.data : []
    } catch (error: unknown) {
      if (isAuthError(error as ApiError)) return
      console.error('Failed to fetch bill logs', error)
    } finally {
      loadingLogs.value = false
    }
  }

  return {
    showViewModal,
    viewingBill,
    filteredViewingBillLogs,
    loadingLogs,
    viewBill,
    formatAction,
    formatUpdateDiff,
  }
}
