import { ref, computed, type Ref } from "vue"
import api from "../api"
import { apiErrorMessage, isAuthError } from "../lib/error"
import { saveEntry } from "../services/billingEntryService"
import { useToast } from "./useToast"

export interface BillEntry {
  species_id: number
  weight: string
  unit_price: number
  fee_value: string
  release_date: string
}

export interface BillFormState {
  id: number | null
  species_id: string
  weight: string
  unit_price: number
  fee_type: string
  fee_value: string
  currency: string
  status: string
  release_date: string
}

export function useBillForm(speciesList: Ref<any[]>) {
  const toast = useToast()
  const showForm = ref(false)
  const saving = ref(false)

  const bill = ref<BillFormState>({
    id: null,
    species_id: "",
    weight: "0.00",
    unit_price: 0,
    currency: "CNY",
    fee_type: "FIXED",
    fee_value: "0.00",
    status: "DRAFT",
    release_date: "",
  })

  const billEntries = ref<BillEntry[]>([])

  const newEntryDefaults = (speciesId: number): BillEntry => {
    const sp = speciesList.value.find((s) => s.id === speciesId)
    return {
      species_id: speciesId,
      weight: "0.00",
      unit_price: sp?.default_price ?? 0,
      fee_value: "0.00",
      release_date: "",
    }
  }

  const isEntrySelected = (id: number) =>
    billEntries.value.some((e) => e.species_id === id)

  const toggleEntry = (sp: any) => {
    const idx = billEntries.value.findIndex((e) => e.species_id === sp.id)
    if (idx >= 0) {
      removeEntry(idx)
    } else {
      billEntries.value.push(newEntryDefaults(sp.id))
    }
  }

  const removeEntry = (idx: number) => {
    billEntries.value.splice(idx, 1)
  }

  const getEntrySpecies = (speciesId: number) =>
    speciesList.value.find((s) => s.id === speciesId)

  const getEntryName = (speciesId: number) =>
    getEntrySpecies(speciesId)?.name_zh ?? ""

  const getEntryUnit = (speciesId: number) =>
    getEntrySpecies(speciesId)?.default_unit ?? ""

  const editingSpecies = computed(
    () => speciesList.value.find((s) => s.id == bill.value.species_id) || null,
  )

  const initNewBill = () => {
    billEntries.value = []
    bill.value.release_date = ""
  }

  const batchSubtotal = computed(() =>
    billEntries.value.reduce(
      (s, e) => s + Number(((+e.weight || 0) * (+e.unit_price || 0)).toFixed(2)),
      0,
    ),
  )

  const batchFee = computed(() =>
    billEntries.value.reduce(
      (s, e) => s + Number((+e.fee_value || 0).toFixed(2)),
      0,
    ),
  )

  const batchTotal = computed(() =>
    Number((batchSubtotal.value + batchFee.value).toFixed(2)),
  )

  const editSubtotal = computed(() =>
    Number(((+bill.value.weight || 0) * (+bill.value.unit_price || 0)).toFixed(2)),
  )

  const editFee = computed(() => Number((+bill.value.fee_value || 0).toFixed(2)))

  const editTotal = computed(() =>
    Number((editSubtotal.value + editFee.value).toFixed(2)),
  )

  const goBackToList = () => {
    showForm.value = false
    bill.value.id = null
    bill.value.weight = "0.00"
  }

  const saveBill = async (onSaved?: (data: any) => void) => {
    if (bill.value.id) {
      if (!Number.isFinite(+bill.value.weight) || +bill.value.weight <= 0) {
        toast.warning("重量必须大于0")
        return
      }
      if (!Number.isFinite(+bill.value.unit_price) || +bill.value.unit_price <= 0) {
        toast.warning("单价必须大于0")
        return
      }
      saving.value = true
      try {
        const payload = {
          ...bill.value,
          species_id: Number(bill.value.species_id),
          weight: Number(bill.value.weight),
          fee_value: Number(bill.value.fee_value),
          unit_price: Number(bill.value.unit_price),
          status: "COMPLETED",
          release_date: bill.value.release_date || null,
        }
        const response = await api.put(`/bills/${bill.value.id}`, payload)
        if (onSaved) onSaved(response.data)
        toast.success("单据更新成功")
        bill.value.id = null
        showForm.value = false
      } catch (error: any) {
        if (isAuthError(error)) return
        toast.error(apiErrorMessage(error, "保存单据"))
      } finally {
        saving.value = false
      }
      return
    }

    const validEntries = billEntries.value.filter(
      (e) => +e.weight > 0 && e.unit_price > 0,
    )
    if (validEntries.length === 0) {
      toast.warning("请选择品种并填写重量和单价")
      return
    }

    saving.value = true
    try {
      let saved = 0
      for (const entry of validEntries) {
        const data = await saveEntry({
          ...entry,
          weight: Number(entry.weight),
          fee_value: Number(entry.fee_value),
          release_date: entry.release_date || bill.value.release_date,
        })
        if (onSaved) onSaved(data)
        saved++
      }
      billEntries.value = []
      bill.value.release_date = ""
      showForm.value = false
      toast.success(`成功保存 ${saved} 条`)
    } catch (error: any) {
      if (isAuthError(error)) return
      toast.error(apiErrorMessage(error, "保存单据"))
    } finally {
      saving.value = false
    }
  }

  const editBill = (b: any) => {
    bill.value = {
      id: b.id,
      species_id: String(b.species_id),
      weight: Number(b.weight ?? 0).toFixed(2),
      unit_price: b.unit_price,
      currency: b.currency,
      fee_type: "FIXED",
      fee_value:
        b.fee_type === "PERCENTAGE"
          ? (b.weight * b.unit_price * (b.fee_value / 100)).toFixed(2)
          : Number(b.fee_value ?? 0).toFixed(2),
      status: b.status,
      release_date: b.release_date
        ? new Date(b.release_date).toISOString().slice(0, 10)
        : "",
    }
    showForm.value = true
    window.scrollTo({ top: 0, behavior: "smooth" })
  }

  return {
    showForm,
    saving,
    bill,
    billEntries,
    isEntrySelected,
    toggleEntry,
    removeEntry,
    getEntrySpecies,
    getEntryName,
    getEntryUnit,
    editingSpecies,
    initNewBill,
    batchSubtotal,
    batchFee,
    batchTotal,
    editSubtotal,
    editFee,
    editTotal,
    goBackToList,
    saveBill,
    editBill,
  }
}
