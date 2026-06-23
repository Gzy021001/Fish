import api from "../api"

export interface ImportRow {
  name_zh: string
  weight: number
  unit_price: number
  fee_value: number
  release_date?: string
}

export interface BillEntryInput {
  species_id: number
  weight: number
  unit_price: number
  fee_value: number
  release_date?: string
}

export async function ensureSpecies(
  nameZh: string,
  defaultPrice: number,
  existingList: any[],
  releaseDate?: string,
): Promise<any> {
  const found = existingList.find((s) => s.name_zh === nameZh)
  if (found) return found

  const spRes = await api.post("/species", {
    name_zh: nameZh,
    default_price: defaultPrice,
    default_unit: "公斤",
    release_date: releaseDate || new Date().toLocaleDateString("sv-SE"),
  })
  const species = spRes.data
  existingList.push(species)
  return species
}

export function buildBillPayload(entry: BillEntryInput) {
  return {
    species_id: entry.species_id,
    weight: entry.weight,
    unit_price: entry.unit_price,
    fee_type: "FIXED",
    fee_value: entry.fee_value,
    currency: "CNY",
    status: "DRAFT",
    release_date: entry.release_date || null,
  }
}

export async function saveEntry(entry: BillEntryInput) {
  const payload = buildBillPayload(entry)
  const response = await api.post("/bills", payload)
  return response.data
}

export async function saveImportedRows(
  rows: ImportRow[],
  speciesList: any[],
): Promise<number> {
  let saved = 0
  for (const row of rows) {
    const species = await ensureSpecies(row.name_zh, row.unit_price, speciesList, row.release_date)
    const payload: BillEntryInput = {
      species_id: species.id,
      weight: row.weight || 0,
      unit_price: row.unit_price,
      fee_value: row.fee_value || 0,
      release_date: row.release_date,
    }
    await saveEntry(payload)
    saved++
  }
  return saved
}


/** Batch import: single API call for all rows. Much faster than sequential. */
export async function saveImportedRowsBatch(rows: ImportRow[], replace = false): Promise<{ success_count: number; skip_count: number; errors: string[] }> {
  const res = await api.post('/bills/batch', { rows, replace })
  return res.data
}
