import { computed, ref, type Ref } from "vue"
import api from "../api"
import { isAuthError } from "../lib/error"
import { diffFields } from "../lib/utils"

export function useBillAudit(speciesList: Ref<any[]>) {
  const showViewModal = ref(false)
  const viewingBill = ref<any>(null)
  const viewingBillLogs = ref<any[]>([])

  const getSpeciesName = (id: number) => {
    const sp = speciesList.value.find((s) => s.id === id)
    return sp ? sp.name_zh : `未知品种(${id})`
  }

  const formatAction = (action: string) => {
    const map: Record<string, string> = {
      CREATE: "新增单据",
      UPDATE: "修改单据",
      DELETE: "删除单据",
      COMPLETED: "单据归档",
    }
    return map[action] || action
  }

  const formatUpdateDiff = (
    oldDataStr: string | null,
    newDataStr: string | null,
  ) => {
    if (!oldDataStr || !newDataStr) return []
    try {
      const oldD = JSON.parse(oldDataStr)
      const newD = JSON.parse(newDataStr)
      const result = diffFields(oldDataStr, newDataStr, [
        {
          key: "species_id",
          label: "品种",
          format: (v) => getSpeciesName(v as number),
        },
        { key: "weight", label: "重量", format: (v) => v },
        { key: "unit_price", label: "单价", format: (v) => v },
        { key: "release_date", label: "放生日期", format: (v) => v ? String(v).slice(0, 10) : "-" },
      ])

      if (oldD.fee_type !== newD.fee_type || oldD.fee_value !== newD.fee_value) {
        const oldFee = String(Number(oldD.fee_value || 0).toFixed(2))
        const newFee = String(Number(newD.fee_value || 0).toFixed(2))
        if (oldFee !== newFee)
          result.push({ label: "服务费", old: oldFee, new: newFee })
      }
      return result
    } catch {
      return []
    }
  }

  const filteredViewingBillLogs = computed(() =>
    viewingBillLogs.value.filter(
      (log) => log.action !== "UPDATE" || formatUpdateDiff(log.old_data, log.new_data).length > 0,
    ),
  )

  const viewBill = async (b: any) => {
    viewingBill.value = b
    viewingBillLogs.value = []
    showViewModal.value = true
    try {
      const res = await api.get(`/logs/bill/${b.id}`)
      viewingBillLogs.value = res.data || []
    } catch (error: any) {
      if (isAuthError(error)) return
      console.error("Failed to fetch bill logs", error)
    }
  }

  return {
    showViewModal,
    viewingBill,
    filteredViewingBillLogs,
    viewBill,
    formatAction,
    formatUpdateDiff,
  }
}
