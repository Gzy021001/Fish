import * as XLSX from "xlsx"
import { isPackagingItem } from "./utils"

const COLUMN_MAPS: Record<string, string[]> = {
  species: ["品种", "品名", "鱼种", "物种", "名称", "商品名", "鱼类", "品种名称", "水产名称", "货物名称", "品称", "品类", "name", "product", "species", "type"],
  weight: ["重量", "公斤", "斤", "净重", "毛重", "总重", "重量(斤)", "重量（斤）", "重量(公斤)", "重量（公斤）", "数量", "weight", "kg"],
  unit_price: ["单价", "价格", "售价", "定价", "单价(元)", "单价（元）", "元/公斤", "元/斤", "price", "unit_price"],
  fee_value: ["服务费", "手续费", "附加费", "费用", "其他费用", "服务费(元)", "服务费（元）", "fee"],
  paid_amount: ["实付", "实付金额", "实际付款", "付款金额", "paid", "paid_amount"],
  release_date: ["放生日期", "日期", "时间", "出货日期", "交易日期", "发货日期", "date", "time", "release"],
};
function normalizeHeader(h: string): string {
  return h.replace(/\uff08/g, "(").replace(/\uff09/g, ")").replace(/\s+/g, "").replace(/[\uff01-\uff5e]/g, c => String.fromCharCode(c.charCodeAt(0) - 0xfee0)).toLowerCase()
}

export function detectColumns(headers: string[]): Record<string, string | null> {
  const nh = headers.map(normalizeHeader)
  const r: Record<string, string | null> = { species: null, weight: null, unit_price: null, fee_value: null, paid_amount: null, release_date: null }
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

/**
 * 对 Excel 里的简单算术公式求值（如 "79+77"、"61.3+60.8+63.6"、"(2+3)*4"）。
 * 背景：有些表格由程序生成、公式没有缓存值，SheetJS 读不到 cell.v（读成 0/空），
 * 供应商把多次称重写成「=79+77」这类公式，直接读会丢重量。
 * 只接受数字、+ - * /、括号、空格；SUM(...)、单元格引用等一律返回 null（调用方回退为空）。
 */
export function evalSimpleFormula(formula: unknown): number | null {
  if (formula == null) return null
  const src = String(formula).trim().replace(/^=/, "").replace(/\s+/g, "")
  if (!src || !/^[\d+\-*/().]+$/.test(src)) return null

  let i = 0
  function parseExpr(): number | null {
    let left = parseTerm()
    if (left === null) return null
    while (i < src.length && (src[i] === "+" || src[i] === "-")) {
      const op = src[i++]
      const right = parseTerm()
      if (right === null) return null
      left = op === "+" ? left + right : left - right
    }
    return left
  }
  function parseTerm(): number | null {
    let left = parseFactor()
    if (left === null) return null
    while (i < src.length && (src[i] === "*" || src[i] === "/")) {
      const op = src[i++]
      const right = parseFactor()
      if (right === null) return null
      if (op === "*") left = left * right
      else {
        if (right === 0) return null
        left = left / right
      }
    }
    return left
  }
  function parseFactor(): number | null {
    if (src[i] === "+") {
      i++
      return parseFactor()
    }
    if (src[i] === "-") {
      i++
      const v = parseFactor()
      return v === null ? null : -v
    }
    if (src[i] === "(") {
      i++
      const v = parseExpr()
      if (v === null || src[i] !== ")") return null
      i++
      return v
    }
    const start = i
    while (i < src.length && /[0-9.]/.test(src[i])) i++
    if (start === i) return null
    const n = Number(src.slice(start, i))
    return Number.isFinite(n) ? n : null
  }

  const value = parseExpr()
  if (value === null || i !== src.length || !Number.isFinite(value)) return null
  // 消除浮点尾差（如 185.70000000000002）
  return Math.round(value * 1e6) / 1e6
}

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

// 明细表里按「件/个」报价的品种：1 件（个）= N 斤。
// 模板把这些单位写在品种名上（「蛏子（件）」「带子（个）」），若直接按表头「重量(斤)」处理，
// 会被当成「2 斤 × 120 元/斤」入库（重量缩小、单价放大，金额虽对得上，但均价/重量统计全被带偏）。
// 处理方式：先把件数/个数折成斤、元/件（个）折成元/斤，再统一走斤→公斤换算，金额不变。
//   · 蛏子：1 件 = 10 斤（2026-11-05 确认；只在写了「（件）」的行生效，其余行仍按斤）
//   · 带子：整年按个卖（「（个）」标注时有时无），默认就按个折算；江珧/大带子按个卖，
//     大的一个约一斤、小的半斤（青岛早报：40 多个约 50 斤），取 1 个 ≈ 1 斤，
//     与惠农网「带子 2.6 元/斤」及本表 2.3~5.5 元/个 的价格区间对得上
//   · 草龟：只有「小草龟（个）」这类标注行按个；水产市场中华草龟批发价 50 元/千克
//     （2026-09 佛山南海环球水产市场）＝25 元/斤，5.5 元/个 ÷ 25 ≈ 0.22 斤/个
// 件重/个重与实际不符时只改这张表，别处不用动。
interface UnitRule { unit: string; jin: number; always?: boolean }
const UNIT_RULES: Record<string, UnitRule> = {
  "\u86cf\u5b50": { unit: "\u4ef6", jin: 10 },
  "\u5e26\u5b50": { unit: "\u4e2a", jin: 1, always: true },
  "\u8349\u9f9f": { unit: "\u4e2a", jin: 0.22 },
}

/** 取品种单元格里的单位标注（「蛏子（件）」→ 件），全角/半角括号都认 */
function detectUnit(raw: string): string | null {
  const m = raw.match(/[（(]\s*([\u4ef6\u4e2a\u7bb1\u5757\u6761\u53ea\u5305\u888b\u6876\u76d2\u4e32\u7c92\u9897\u6839\u4efd\u7247\u679a\u5bf9\u53cc\u6253\u677f\u63d0\u5934])\s*[）)]/)
  return m ? m[1] : null
}

/** 该品种这一行按哪条单位规则折算；没有返回 null（保持按表头斤处理） */
function resolveUnit(name: string, marker: string | null): { unit: string; jin: number } | null {
  const rule = UNIT_RULES[name]
  if (!rule) return null
  // always=true 的品种（带子）默认就是按个卖，允许没写「（个）」；
  // 但若写的是别的单位（如「带子（件）」）就不猜，交给原有逻辑
  const matched = rule.always ? marker === null || marker === rule.unit : marker === rule.unit
  return matched ? { unit: rule.unit, jin: rule.jin } : null
}

function round6(v: number): number { return Math.round(v * 1e6) / 1e6 }

export interface ParsedRow {
  name_zh: string
  weight: number
  unit_price: number
  fee_value: number
  release_date: string | null
  /** 源表原始计价单位（件/个）；null 表示按斤。导出时据此还原模板写法 */
  unit?: string | null
  /** 1 件/个 合多少斤（与 unit 配套，导出还原数量/单价用） */
  unit_jin?: number | null
  /** 模板「实付」列的值（一般只写在该批首行） */
  paid_amount?: number | null
  /** 本周现场随喜（模板表尾一行，只挂到当天第一张单据上） */
  weekly_donation?: number | null
  /** 上周余款（模板表尾一行，只挂到当天第一张单据上，导出照抄模板用） */
  week_carry_in?: number | null
  alipay_amount?: number | null
  wechat_amount?: number | null
  suixi_amount?: number | null
  /** 收款行对应的随喜类型（支付宝/微信/随喜放生），列表的"随喜类型"列用它展示 */
  payment_method?: string | null
  /** jsonData 内的行号（0 起），用于把收款区的逐笔行挂到同一行的单据上 */
  matrixRow?: number
}

/** 车费/船费等表尾支出（不打进物命单据，单独落库） */
export interface ParsedExpense {
  name: string
  amount: number
  release_date: string | null
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
export interface ParseResult {
  validRows: ParsedRow[]
  skippedRows: SkippedRow[]
  expenseRows: ParsedExpense[]
  /** 本周现场随喜（模板表尾一行，记到当天第一张单据上） */
  onsiteDonation?: number | null
  /** 上周余款（模板表尾一行，记到当天第一张单据上） */
  weekCarryIn?: number | null
}

/** 表尾费用行：金额写在「实付」列 */
const EXPENSE_KW = ["车费", "船费"]

/**
 * 表尾汇总行（本周现场随喜 / 上周余款）的金额取值。
 *
 * 这类行没有稳定表头：值一般写在「总计」列（模板 F 列），个别文件写在「实付」列。
 * 旧逻辑按 columns 里的 实付/服务费/重量/单价 逐个取，遇到「总计」列会全部取空，
 * 于是导入后「本周现场随喜」恒为空、导出整年都是 0（2026 模板 43 个 sheet 全是这种写法）。
 * 这里从「品种」标签所在列往右找第一个数字格，与列名无关，模板换列也取得到。
 */
function pickSummaryAmount(raw: Record<string, unknown>, labelKey?: string | null): number | null {
  const keys = Object.keys(raw)
  const start = labelKey ? keys.indexOf(labelKey) : -1
  if (start < 0) return null
  for (let i = start + 1; i < keys.length; i++) {
    const value = raw[keys[i]]
    if (value === null || value === undefined || value === "") continue
    const n = typeof value === "number" ? value : parseFloat(String(value).replace(/,/g, ""))
    if (Number.isFinite(n)) return n
  }
  return null
}

export function parseImportRows(jsonData: Record<string, unknown>[], columns: Record<string, string | null>, fallbackReleaseDate?: string | null): ParseResult {
  const validRows: ParsedRow[] = []
  const skippedRows: SkippedRow[] = []
  const expenseRows: ParsedExpense[] = []
  let onsiteDonation: number | null = null
  let weekCarryIn: number | null = null
  const fallbackYear = fallbackReleaseDate ? parseInt(fallbackReleaseDate.substring(0, 4)) : undefined

  for (const [idx, raw] of jsonData.entries()) {
    const rs = columns.species ? raw[columns.species] : null
    const rw = columns.weight ? raw[columns.weight] : null
    const rp = columns.unit_price ? raw[columns.unit_price] : null
    const rf = columns.fee_value ? raw[columns.fee_value] : null
    let rd = columns.release_date ? raw[columns.release_date] : null
    if (!rd && fallbackReleaseDate) rd = fallbackReleaseDate

    // 完全空白的行（品种/重量/单价/服务费都为空）直接忽略，不计入"跳过"统计
    const isBlankRow = [rs, rw, rp, rf].every(
      (v) => v === null || v === undefined || String(v).trim() === ""
    )
    if (isBlankRow) continue

    const rawName = String(rs ?? "")
    const nm = normalizeSpeciesName(rawName)
    if (!nm) { skippedRows.push({ rowIndex: idx + 2, reason: "\u54c1\u79cd\u540d\u79f0\u4e3a\u7a7a\u6216\u65e0\u6cd5\u8bc6\u522b", rawData: raw }); continue }
    // 车费/船费：模板表尾的费用行，金额写在「实付」列，单独落库（不算物命单据）
    const expenseKw = EXPENSE_KW.find((k) => rawName.includes(k) || nm.includes(k))
    if (expenseKw) {
      const paidCell = columns.paid_amount ? raw[columns.paid_amount] : null
      const amt = parseFloat(String(paidCell ?? ""))
      if (!isNaN(amt) && amt > 0) {
        expenseRows.push({ name: expenseKw, amount: amt, release_date: parseExcelDate(rd, fallbackYear) })
      }
      continue
    }
    // 本周现场随喜：模板表尾的一行（值写在「总计」列，个别模板写在「实付」列），
    // 记到当天第一张单据上，导出时用来还原「本周现场随喜」和「本周随喜累计」链条
    if (rawName.includes("现场随喜") && !rawName.includes("累计")) {
      if (onsiteDonation === null) onsiteDonation = pickSummaryAmount(raw, columns.species)
      continue
    }
    // 上周余款：同样是表尾一行，导出时优先照抄模板原值（bills.week_carry_in）
    if (rawName.includes("上周余款")) {
      if (weekCarryIn === null) weekCarryIn = pickSummaryAmount(raw, columns.species)
      continue
    }
    // 汇总行（本周现场随喜/累计等）不是错误，直接忽略，不进入"查看原因"列表
    if (isNonBillRow(nm) || isNonBillRow(String(rs ?? ""))) { continue }
    // 打包耗材（冰块/打包袋等）不是物命品种，直接忽略（与物命列表/导出的过滤规则一致）
    if (isPackagingItem(nm)) { continue }
    let up = parseFloat(String(rp ?? 0))
    if (isNaN(up) || up <= 0) { skippedRows.push({ rowIndex: idx + 2, reason: "\u5355\u4ef7\u65e0\u6548", rawData: raw }); continue }
    let wt = isNaN(parseFloat(String(rw ?? ""))) ? 0 : parseFloat(String(rw ?? ""))
    // 按件/个报价的行先折成斤：件数 × 斤/件 → 斤、元/件 ÷ 斤/件 → 元/斤，后面再统一走斤→公斤换算
    const pieceUnit = resolveUnit(nm, detectUnit(rawName))
    if (pieceUnit) {
      if (wt > 0) wt = round6(wt * pieceUnit.jin)
      up = round6(up / pieceUnit.jin)
    }
    // 系统内部单位：重量=公斤、单价=元/公斤；模板表头「重量(斤)」「单价(元)」是斤制。
    // 只换算重量会导致 总计=公斤×元/斤 少一半，单价必须同步 ×2（斤价 → 公斤价）。
    const isJinUnit = detectJinUnit(columns.weight)
    if (isJinUnit && wt > 0) wt = wt * JIN_TO_KG
    if (isJinUnit) up = up * 2
    const fv = isNaN(parseFloat(String(rf ?? ""))) ? 0 : parseFloat(String(rf ?? ""))
    const rd2 = parseExcelDate(rd, fallbackYear)
    // 模板「实付」列：有值就原样带上（一般只在该批首行），空则不计
    const paidCell = columns.paid_amount ? raw[columns.paid_amount] : null
    const paidNum = parseFloat(String(paidCell ?? ""))
    validRows.push({
      name_zh: nm, weight: wt, unit_price: up, fee_value: fv, release_date: rd2,
      matrixRow: idx,
      unit: pieceUnit ? pieceUnit.unit : null,
      unit_jin: pieceUnit ? pieceUnit.jin : null,
      paid_amount: !isNaN(paidNum) && paidNum > 0 ? paidNum : null,
    })
  }
  return { validRows, skippedRows, expenseRows, onsiteDonation, weekCarryIn }
}

/**
 * 把导入行切成「不可拆的批次组」：后端 apportion_rows 只在单个分片内按批分摊实付，
 * 同一批实付被分片切断时，两片会各自把整批金额摊一遍（整批金额重复计）——
 * 表现为列表里同一批的实付合计翻倍、导出「批次实付合计 - 已摊实付」为负、
 * 凭空多出一条金额为正的「耗材」行。分片前先用这个函数成组，只在组边界切开。
 *
 * 成组规则与后端一致：一批 = 有实付的行 + 紧跟其后没写实付的行
 * （合并单元格被广播成同额的行也算同一批），遇到另一笔实付才断开。
 */
export function splitIntoBatchGroups<T extends { release_date?: string | null; paid_amount?: number | null }>(
  rows: T[],
): T[][] {
  const groups: T[][] = []
  let i = 0
  while (i < rows.length) {
    const start = i
    const day = rows[i].release_date
    const paid = rows[i].paid_amount ?? null
    i++
    while (i < rows.length && rows[i].release_date === day) {
      const next = rows[i].paid_amount ?? null
      if (next !== null && (paid === null || Number(next) !== Number(paid))) break
      i++
    }
    groups.push(rows.slice(start, i))
  }
  return groups
}
