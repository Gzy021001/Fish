import api from '../api'
import type { Species, ApiError } from '../types'
import { splitIntoBatchGroups } from '../lib/importUtils'
import { apiErrorMessage } from '../lib/error'

export interface ImportRow {
  name_zh: string
  weight: number
  unit_price: number
  fee_value: number
  release_date?: string
  /** 源表原始计价单位（件/个），导出还原模板写法用；null/缺省=按斤 */
  unit?: string | null
  unit_jin?: number | null
  /** 模板「实付」列的值（一般只写在该批首行），没有则留空 */
  paid_amount?: number | null
  /** 本周现场随喜（整周一个值，挂到当天第一张单据上） */
  weekly_donation?: number | null
  /** 上周余款（整周一个值，挂到当天第一张单据上，导出照抄模板用） */
  week_carry_in?: number | null
}

/** 车费/船费等表尾支出（不打进物命单据） */
export interface ImportExpenseRow {
  name: string
  amount: number
  release_date?: string
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
    default_unit: '斤',
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

/**
 * 等后端真正就绪再开始导入。
 *
 * 线上（Vercel Serverless）冷启动时，除 /api/health 外的请求都会被 503 拦下并提示
 * 「服务器正在启动，请稍后重试」；而写请求明确不能自动重试（避免重复落库），
 * 所以导入前必须先轮询 /api/health 直到 initialized，别让第一片白白撞上 503。
 */
export async function waitForBackendReady(timeoutMs = 60_000): Promise<void> {
  const deadline = Date.now() + timeoutMs
  let last = '服务器正在启动'
  while (Date.now() < deadline) {
    try {
      const res = await api.get('/health', { timeout: 8000 })
      const data = res.data || {}
      if (data.initialized) return
      last = data.status === 'error' ? '服务初始化失败（数据库连接异常）' : '服务器正在启动'
    } catch (err) {
      last = apiErrorMessage(err as ApiError, '连接服务器')
    }
    await new Promise((resolve) => setTimeout(resolve, 1500))
  }
  throw new Error(`${last}，已等待 ${Math.round(timeoutMs / 1000)} 秒仍未就绪，请稍后重试`)
}

/** 只认「启动守卫」的 503：它由后端中间件在进入业务代码之前返回，绝对没有落库，
 *  重试是安全的。其它 503（如数据库瞬时异常）可能已执行一部分，按项目约定写请求不重试。 */
function isStartingUpError(error: ApiError): boolean {
  return (
    error?.response?.status === 503 &&
    String(error.response.data?.detail || '').includes('服务器正在启动')
  )
}

/** Chunked batch import: splits large imports into small chunks to avoid serverless timeout.
 *  覆盖模式（默认开启）：首片带上整份文件的全部放生日期，先按日期清空旧数据；其余分片只追加。
 *  这样跨多个日期的导入（如整年模板）也能正确覆盖，不会留下重复数据。
 *  分片只在批次边界处切开，同一批实付不会被拆到两个分片里重复分摊。 */
export async function saveImportedRowsChunked(
  rows: ImportRow[],
  onProgress?: (done: number, total: number) => void,
  options?: { replace?: boolean; expenses?: ImportExpenseRow[] },
): Promise<{ success_count: number; skip_count: number; errors: string[] }> {
  // 冷启动保护：先等后端初始化完成，再发第一片（守卫 503 在片内还会补发一次）
  await waitForBackendReady()

  const replaceEnabled = options?.replace ?? true
  const expenses = options?.expenses ?? []
  // 整份文件涉及的所有放生日期（覆盖时一次性清空，避免跨分片重复）
  const allDates = Array.from(
    new Set([
      ...rows.map((r) => r.release_date).filter((d): d is string => !!d),
      ...expenses.map((e) => e.release_date).filter((d): d is string => !!d),
    ]),
  )

  const chunks: ImportRow[][] = []
  let current: ImportRow[] = []
  for (const group of splitIntoBatchGroups(rows)) {
    if (current.length > 0 && current.length + group.length > CHUNK_SIZE) {
      chunks.push(current)
      current = []
    }
    current.push(...group)
    if (current.length >= CHUNK_SIZE) {
      chunks.push(current)
      current = []
    }
  }
  if (current.length > 0) chunks.push(current)

  let totalSuccess = 0
  let totalSkip = 0
  const allErrors: string[] = []

  for (let ci = 0; ci < chunks.length; ci++) {
    const isFirst = ci === 0
    const replace = isFirst && replaceEnabled
    let attempt = 0
    for (;;) {
      try {
        const payload: Record<string, unknown> = {
          rows: chunks[ci],
          replace,
        }
        if (replace && allDates.length > 0) {
          payload.replace_dates = allDates
        }
        // 车费/船费只需在首片随同提交（后端按日期覆盖），避免重复插入
        if (isFirst && expenses.length > 0) {
          payload.expenses = expenses
          payload.expense_dates = allDates
        }
        const res = await api.post('/bills/batch', payload, { timeout: 45000 })
        totalSuccess += res.data.success_count ?? 0
        totalSkip += res.data.skip_count ?? 0
        if (res.data.errors) allErrors.push(...res.data.errors)
        break
      } catch (err: unknown) {
        const error = err as ApiError
        // 冷启动守卫：等实例初始化完再重发同一片，最多补 2 次（不会写入脏数据）
        if (isStartingUpError(error) && attempt < 2) {
          attempt += 1
          await waitForBackendReady()
          continue
        }
        const msg = error.response?.data?.detail || error.message || '未知错误'
        // 一片失败就整单停下：首片失败说明「按日期覆盖」根本没执行，继续追加会和旧数据重复；
        // 中途失败则会留下「一半已覆盖、一半没写」的半套数据。停下并提示重试更安全
        // （重试仍是覆盖模式，会按日期重新清空后再写）。
        throw new Error(
          `导入已停止：第 ${ci + 1}/${chunks.length} 片失败（${msg}）。` +
            (ci === 0 ? '未写入任何数据。' : `已写入前 ${ci} 片，数据不完整。`) +
            '请稍后重试。',
        )
      }
    }
    if (onProgress) onProgress(ci + 1, chunks.length)
  }

  return { success_count: totalSuccess, skip_count: totalSkip, errors: allErrors }
}
