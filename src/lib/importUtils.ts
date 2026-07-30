import * as XLSX from "xlsx"

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
  const pm2 = s.match(/^([\u4e00-\u9fff]{1,3})[（(]([\u4e00-\u9fff]+)[）)]$/)
  if (pm2) s = pm2[2]
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

export interface ParsedRow { name_zh: string; weight: number; unit_price: number; fee_value: number; release_date: string | null }
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

    const nm = normalizeSpeciesName(String(rs ?? ""))
    if (!nm) { skippedRows.push({ rowIndex: idx + 2, reason: "\u54c1\u79cd\u540d\u79f0\u4e3a\u7a7a\u6216\u65e0\u6cd5\u8bc6\u522b", rawData: raw }); continue }
    if (isNonBillRow(nm) || isNonBillRow(String(rs ?? ""))) { skippedRows.push({ rowIndex: idx + 2, reason: "\u975e\u8d2d\u751f\u6761\u76ee", rawData: raw }); continue }
    const up = parseFloat(String(rp ?? 0))
    if (isNaN(up) || up <= 0) { skippedRows.push({ rowIndex: idx + 2, reason: "\u5355\u4ef7\u65e0\u6548", rawData: raw }); continue }
    let wt = isNaN(parseFloat(String(rw ?? ""))) ? 0 : parseFloat(String(rw ?? ""))
    if (detectJinUnit(columns.weight) && wt > 0) wt = wt * JIN_TO_KG
    const fv = isNaN(parseFloat(String(rf ?? ""))) ? 0 : parseFloat(String(rf ?? ""))
    const rd2 = parseExcelDate(rd, fallbackYear)
    validRows.push({ name_zh: nm, weight: wt, unit_price: up, fee_value: fv, release_date: rd2 })
    if (debugCount < 5) {
      console.log(`[parseImportRows] row[${idx}] → VALID: nm="${nm}" weight=${wt} up=${up} fee=${fv} date=${rd2}`);
    }
    debugCount++;
  }
  return { validRows, skippedRows }
}
