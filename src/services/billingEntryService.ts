import api from '../api'
import type { Species, ApiError } from '../types'

export interface ImportRow {
  name_zh: string
  weight: number
  unit_price: number
  fee_value: number
  release_date?: string
  /** 源表原始计价单位（件/个），导出还原模板写法用；null/缺省=按斤 */
  unit?: string | null
  unit_jin?: number | null
}

export interface BillEntryInput {
  species_id: number
  weight: number
  unit_price: number
  fee_value: number
  release_date?: string
  unit?: string | null
  unit_jin?: number | null
  payment_method?: string | null
  weekly_donation?: number | null
  alipay_amount?: number | null
  wechat_amount?: number | null
  suixi_amount?: number | null
}

export async function ensureSpecies(
  nameZh: string,
  defaultPrice: number,
  existingList: Species[],
  releaseDate?: string,
): Promise<Species> {
  const found = existingList.find((s) => s.name_zh === nameZh)
  if (found) return found

  const spRes = await api.post('/species', {
    name_zh: nameZh,
    default_price: defaultPrice,
    default_unit: '公斤',
    release_date: releaseDate || new Date().toLocaleDateString('sv-SE'),
  })
  const species = spRes.data as Species
  existingList.push(species)
  return species
}

export function buildBillPayload(entry: BillEntryInput) {
  return {
    species_id: entry.species_id,
    weight: entry.weight,
    unit_price: entry.unit_price,
    fee_type: 'FIXED',
    fee_value: entry.fee_value,
    currency: 'CNY',
    status: 'DRAFT',
    release_date: entry.release_date || null,
    unit: entry.unit ?? null,
    unit_jin: entry.unit_jin ?? null,
    payment_method: entry.payment_method || null,
    weekly_donation: entry.weekly_donation ?? null,
    alipay_amount: entry.alipay_amount ?? null,
    wechat_amount: entry.wechat_amount ?? null,
    suixi_amount: entry.suixi_amount ?? null,
  }
}

export async function saveEntry(entry: BillEntryInput) {
  const payload = buildBillPayload(entry)
  const response = await api.post('/bills', payload)
  return response.data
}

export async function saveImportedRows(
  rows: ImportRow[],
  speciesList: Species[],
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
      unit: row.unit ?? null,
      unit_jin: row.unit_jin ?? null,
    }
    await saveEntry(payload)
    saved++
  }
  return saved
}


/** Batch import: single API call for all rows. Much faster than sequential. */
export async function saveImportedRowsBatch(rows: ImportRow[], replace = false): Promise<{ success_count: number; skip_count: number; errors: string[] }> {
  const res = await api.post('/bills/batch', { rows, replace }, { timeout: 60000 })
  return res.data
}

const CHUNK_SIZE = 25

/** Chunked batch import: splits large imports into small chunks to avoid serverless timeout.
 *  覆盖模式（默认开启）：首片带上整份文件的全部放生日期，先按日期清空旧数据；其余分片只追加。
 *  这样跨多个日期的导入（如整年模板）也能正确覆盖，不会留下重复数据。 */
export async function saveImportedRowsChunked(
  rows: ImportRow[],
  onProgress?: (done: number, total: number) => void,
  options?: { replace?: boolean },
): Promise<{ success_count: number; skip_count: number; errors: string[] }> {
  // 快速健康检查，唤醒 serverless 冷启动
  try { await api.get('/bills?limit=1', { timeout: 15000 }) } catch (_) { /* 忽略 */ }

  const replaceEnabled = options?.replace ?? true
  // 整份文件涉及的所有放生日期（覆盖时一次性清空，避免跨分片重复）
  const allDates = Array.from(
    new Set(rows.map((r) => r.release_date).filter((d): d is string => !!d)),
  )

  const chunks: ImportRow[][] = []
  for (let i = 0; i < rows.length; i += CHUNK_SIZE) {
    chunks.push(rows.slice(i, i + CHUNK_SIZE))
  }

  let totalSuccess = 0
  let totalSkip = 0
  const allErrors: string[] = []

  for (let ci = 0; ci < chunks.length; ci++) {
    const isFirst = ci === 0
    const replace = isFirst && replaceEnabled
    try {
      const payload: Record<string, unknown> = {
        rows: chunks[ci],
        replace,
      }
      if (replace && allDates.length > 0) {
        payload.replace_dates = allDates
      }
      const res = await api.post('/bills/batch', payload, { timeout: 45000 })
      totalSuccess += res.data.success_count ?? 0
      totalSkip += res.data.skip_count ?? 0
      if (res.data.errors) allErrors.push(...res.data.errors)
    } catch (err: unknown) {
      const error = err as ApiError
      const msg = error.response?.data?.detail || error.message || '未知错误'
      allErrors.push(`分片 ${ci + 1}/${chunks.length} 失败: ${msg}`)
    }
    if (onProgress) onProgress(ci + 1, chunks.length)
  }

  return { success_count: totalSuccess, skip_count: totalSkip, errors: allErrors }
}
