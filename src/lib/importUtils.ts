import * as XLSX from "xlsx"
import { isPackagingItem } from "./utils"

const COLUMN_MAPS: Record<string, string[]> = {
  species: ["品种", "品名", "鱼种", "物种", "名称", "商品名", "鱼类", "品种名称", "水产名称", "货物名称", "品称", "品类", "name", "product", "species", "type"],
  weight: ["重量", "公斤", "斤", "净重", "毛重", "总重", "重量(斤)", "重量（斤）", "重量(公斤)", "重量（公斤）", "数量", "weight", "kg"],
  unit_price: ["单价", "价格", "售价", "定价", "单价(元)", "单价（元）", "元/公斤", "元/斤", "price", "unit_price"],
  fee_value: ["服务费", "手续费", "附加费", "费用", "其他费用", "服务费(元)", "服务费（元）", "fee"],
  release_date: ["放生日期", "日期", "时间", "出货日期", "交易日期", "发货日期", "date", "time", "release"],
};
function normalizeHeader(h: string): string {
  return h.replace(/\uff08/g, "(").replace(/\uff09/g, ")").replace(/\s+/g, "").replace(/[\uff01-\uff5e]/g, c => String.fromCharCode(c.charCodeAt(0) - 0xfee0)).toLowerCase()
}

export function detectColumns(headers: string[]): Record<string, string | null> {
  const nh = headers.map(normalizeHeader)
  const r: Record<string, string | null> = { species: null, weight: null, unit_price: null, fee_value: null, release_date: null }
  for (const [k, cand] of Object.entries(COLUMN_MAPS)) {
    const nc = cand.map(normalizeHeader)
    for (const [i, h] of nh.entries()) {
      // 跳过空表头，防止 !h 时 c.includes("") === true 导致的误匹配
      if (!h) continue
      if (nc.includes(h) || nc.some(c => h.includes(c) || c.includes(h))) { r[k] = headers[i]; break }
    }
  }
  return r
}

// 括号内若是这些单位词，不当作品种名（否则「蛏子（件）」会被清洗成「件」）
const UNIT_WORDS = new Set([
  "\u4ef6", "\u5757", "\u4e2a", "\u65a4", "\u516c\u65a4", "\u7bb1", "\u6876", "\u6761", "\u53ea",
  "\u5c3e", "\u5305", "\u888b", "\u76d2", "\u4e32", "\u7c92", "\u9897", "\u6839", "\u628a",
  "\u4efd", "\u7247", "\u679a", "\u5bf9", "\u53cc", "\u6253", "\u677f", "\u63d0", "\u5934",
])

export function normalizeSpeciesName(raw: string): string {
  if (!raw) return ""
  let s = String(raw).trim()
  s = s.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{FE0F}]/gu, "")
  s = s.replace(/[\u3010\u3011]/g, "")
  const sw = "(\u53f0\u5c0f|\u53f0\u6bdb|\u53f0\u5927|\u53f0\u4e2d|\u7259\u7b7e|\u4e2d\u5c0f|\u5927|\u4e2d|\u5c0f|\u4e2a)"
  s = s.replace(new RegExp("[\\(（]" + sw + "[\\)）]$"), "")
  s = s.replace(new RegExp("^[\\(（]" + sw + "[\\)）]"), "")
  s = s.replace(/^(\u5927|\u5c0f|\u4e2d|\u7279|\u8d85|\u53f0)([\u4e00-\u9fff]{2,})/, "$2")
  const pm = s.match(/^([\u4e00-\u9fff]{1,2})[（(]([\u4e00-\u9fff]+)[）)]$/)
  if (pm && /^(\u5927|\u5c0f|\u4e2d|\u82b1|\u9ed1|\u767d|\u9ec4|\u9752|\u7ea2|\u8089|\u751f|\u5e72|\u9c9c)$/.test(pm[1])) s = pm[2]
  // 括号内名称优先（如「大头（鳙鱼）」→「鳙鱼」），但括号内若是单位词（件/块/个…）
  // 则保留括号外的品种名，交给后续剥离单位括号（如「蛏子（件）」→「蛏子」）
  const pm2 = s.match(/^([\u4e00-\u9fff]{1,3})[（(]([\u4e00-\u9fff]+)[）)]$/)
  if (pm2 && !UNIT_WORDS.has(pm2[2])) s = pm2[2]
  s = s.replace(/[（(]\u4e2a[）)]/g, "")
  s = s.replace(/[\(（][^)）]*[\)）]/g, "")
  if (s.length > 4) { s = s.replace(/鱼鱻$/, "") }
  s = s.replace(/[\uff01-\uff5e]/g, (c: string) => String.fromCharCode(c.charCodeAt(0) - 0xfee0))
  return s.trim()
}

// 删除了多余的函数

export function parseExcelDate(raw: unknown, fallbackYear?: number): string | null {
  if (raw == null) return null
  if (raw instanceof Date) {
    const m = String(raw.getMonth() + 1).padStart(2, "0")
    const d = String(raw.getDate()).padStart(2, "0")
    return raw.getFullYear() + "-" + m + "-" + d
  }
  if (typeof raw === "number") {
    const jd = XLSX.SSF.parse_date_code(raw)
    if (jd) { const m = String(jd.m).padStart(2, "0"); const d = String(jd.d).padStart(2, "0"); return jd.y + "-" + m + "-" + d }
  }
  const s = String(raw).trim()

  // 已经是标准格式 YYYY-MM-DD
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;

  // 带年份：2025-07-03 / 2025/7/3 / 2025年7月3日
  const matchFull = s.match(/(\d{4})[\u5e74\/\.\-](\d{1,2})[\u6708\/\.\-](\d{1,2})/)
  if (matchFull) { return matchFull[1] + "-" + String(parseInt(matchFull[2])).padStart(2, "0") + "-" + String(parseInt(matchFull[3])).padStart(2, "0") }
  // 无年份：7月3日 / 7/3
  const matchShort = s.match(/(\d{1,2})[\u6708\/\.\-](\d{1,2})/)
  if (matchShort && fallbackYear) {
    return fallbackYear + "-" + String(parseInt(matchShort[1])).padStart(2, "0") + "-" + String(parseInt(matchShort[2])).padStart(2, "0")
  }
  return null
}

// 删除了 parseSheetDate

const NON_BILL_KW = ["\u8d2d\u751f\u603b\u91cd\u91cf", "\u8d2d\u751f\u603b\u65a4\u6570", "\u5b9e\u4ed8\u91d1\u989d", "\u4f59\u6b3e", "\u968f\u559c", "\u8f66\u8d39", "\u8239\u8d39", "\u6253\u5305\u888b", "\u8d2d\u751f\u4ed8\u6b3e\u660e\u7ec6", "\u4e0a\u5468", "\u672c\u5468", "\u73b0\u573a\u968f\u559c", "\u968f\u559c\u7d2f\u8ba1", "\u6148\u60b2\u62a4\u751f", "\u8d2d\u4e70\u603b\u91cd\u91cf", "\u8d2d\u4e70\u603b\u65a4\u6570"]

function isNonBillRow(name: string): boolean { return NON_BILL_KW.some(k => name.includes(k)) }

const JIN_TO_KG = 0.5
function detectJinUnit(wc: string | null): boolean { return !!wc && wc.includes("\u65a4") && !wc.includes("\u516c\u65a4") }

export interface ParsedRow {
  name_zh: string
  weight: number
  unit_price: number
  fee_value: number
  release_date: string | null
  alipay_amount?: number | null
  wechat_amount?: number | null
  suixi_amount?: number | null
  /** 收款行对应的随喜类型（支付宝/微信/随喜放生），列表的"随喜类型"列用它展示 */
  payment_method?: string | null
  /** jsonData 内的行号（0 起），用于把收款区的逐笔行挂到同一行的单据上 */
  matrixRow?: number
}

export type PaymentKind = "alipay" | "wechat" | "suixi"

export interface RowPayment {
  kind: PaymentKind
  amount: number
}

const PAYMENT_LABELS: Record<string, PaymentKind> = {
  "支付宝": "alipay",
  "微信": "wechat",
  "随喜放生": "suixi",
}

/**
 * 从导入模板（慈悲组购生明细表格式）右侧收款区抓取逐笔收款行，按出现顺序返回。
 * 注意：模板里收款行与数据行不一定严格同行（有些文件收款区从表头行就开始），
 * 所以这里只按顺序收集，交给调用方按顺序对应到当天的单据上。
 */
export function extractRowPayments(matrix: any[][]): RowPayment[] {
  const result: RowPayment[] = []
  matrix.forEach((row) => {
    if (!row) return
    for (let c = 0; c < row.length; c++) {
      const label = String(row[c] ?? "").trim()
      const kind = PAYMENT_LABELS[label]
      if (!kind) continue
      // 金额在标签右侧第 1~2 格
      for (let k = c + 1; k <= Math.min(c + 2, row.length - 1); k++) {
        const v = row[k]
        if (v === "" || v === null || v === undefined) continue
        const n = typeof v === "number" ? v : parseFloat(String(v))
        if (!isNaN(n) && n > 0) {
          result.push({ kind, amount: n })
        }
        break
      }
      break
    }
  })
  return result
}
export interface SkippedRow { rowIndex: number; reason: string; rawData: Record<string, unknown> }
export interface ParseResult { validRows: ParsedRow[]; skippedRows: SkippedRow[] }

export function parseImportRows(jsonData: Record<string, unknown>[], columns: Record<string, string | null>, fallbackReleaseDate?: string | null): ParseResult {
  const validRows: ParsedRow[] = []
  const skippedRows: SkippedRow[] = []
  const fallbackYear = fallbackReleaseDate ? parseInt(fallbackReleaseDate.substring(0, 4)) : undefined

  console.log("[parseImportRows] input rows:", jsonData.length, "| columns:", JSON.stringify(columns), "| fallbackDate:", fallbackReleaseDate);
  let debugCount = 0;

  for (const [idx, raw] of jsonData.entries()) {
    const rs = columns.species ? raw[columns.species] : null
    const rw = columns.weight ? raw[columns.weight] : null
    const rp = columns.unit_price ? raw[columns.unit_price] : null
    const rf = columns.fee_value ? raw[columns.fee_value] : null
    let rd = columns.release_date ? raw[columns.release_date] : null
    if (!rd && fallbackReleaseDate) rd = fallbackReleaseDate

    if (debugCount < 5) {
      console.log(`[parseImportRows] row[${idx}]: rs="${rs}" rw="${rw}" rp="${rp}" rf="${rf}" rd="${rd}"`);
    }

    // 完全空白的行（品种/重量/单价/服务费都为空）直接忽略，不计入"跳过"统计
    const isBlankRow = [rs, rw, rp, rf].every(
      (v) => v === null || v === undefined || String(v).trim() === ""
    )
    if (isBlankRow) continue

    const nm = normalizeSpeciesName(String(rs ?? ""))
    if (!nm) { skippedRows.push({ rowIndex: idx + 2, reason: "\u54c1\u79cd\u540d\u79f0\u4e3a\u7a7a\u6216\u65e0\u6cd5\u8bc6\u522b", rawData: raw }); continue }
    // 汇总行（本周现场随喜/累计等）不是错误，直接忽略，不进入"查看原因"列表
    if (isNonBillRow(nm) || isNonBillRow(String(rs ?? ""))) { continue }
    // 打包耗材（冰块/打包袋等）不是物命品种，直接忽略（与物命列表/导出的过滤规则一致）
    if (isPackagingItem(nm)) { continue }
    const up = parseFloat(String(rp ?? 0))
    if (isNaN(up) || up <= 0) { skippedRows.push({ rowIndex: idx + 2, reason: "\u5355\u4ef7\u65e0\u6548", rawData: raw }); continue }
    let wt = isNaN(parseFloat(String(rw ?? ""))) ? 0 : parseFloat(String(rw ?? ""))
    if (detectJinUnit(columns.weight) && wt > 0) wt = wt * JIN_TO_KG
    const fv = isNaN(parseFloat(String(rf ?? ""))) ? 0 : parseFloat(String(rf ?? ""))
    const rd2 = parseExcelDate(rd, fallbackYear)
    validRows.push({ name_zh: nm, weight: wt, unit_price: up, fee_value: fv, release_date: rd2, matrixRow: idx })
    if (debugCount < 5) {
      console.log(`[parseImportRows] row[${idx}] → VALID: nm="${nm}" weight=${wt} up=${up} fee=${fv} date=${rd2}`);
    }
    debugCount++;
  }
  return { validRows, skippedRows }
}
