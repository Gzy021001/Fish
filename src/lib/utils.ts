function parseUTC(dateStr: string | undefined | null): Date | null {
  if (!dateStr) return null
  if (dateStr.endsWith("Z") || dateStr.includes("+") || dateStr.includes("[")) {
    return new Date(dateStr)
  }
  if (dateStr.includes("T")) {
    return new Date(dateStr + "Z")
  }
  return new Date(dateStr + "T00:00:00Z")
}

export function dateTimeStr(dateStr: string | undefined | null): string {
  const d = parseUTC(dateStr)
  if (!d) return ""
  return d.toLocaleString("zh-CN", { hour12: false })
}

export function dateStr(dateStr: string | undefined | null): string {
  const d = parseUTC(dateStr)
  if (!d) return ""
  return d.toLocaleDateString("zh-CN")
}

export function formatMoney(value: number | undefined | null): string {
  if (value == null || !Number.isFinite(value)) return "0.00"
  return value.toLocaleString("zh-CN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

// ============================================================
//  操作记录差异对比
// ============================================================

export interface DiffItem {
  label: string
  old: string
  new: string
}

/**
 * 对比 old/new JSON 数据，返回差异项列表
 * fields: [{ key, label, format? }] 描述需要对比的字段
 */
export function diffFields(
  oldDataStr: string | null,
  newDataStr: string | null,
  fields: { key: string; label: string; format?: (v: unknown) => string }[],
): DiffItem[] {
  if (!oldDataStr || !newDataStr) return []
  try {
    const oldD = JSON.parse(oldDataStr)
    const newD = JSON.parse(newDataStr)
    const result: DiffItem[] = []

    for (const { key, label, format } of fields) {
      const ov = oldD[key]
      const nv = newD[key]
      if (ov === nv) continue
      result.push({
        label,
        old: format ? format(ov) : String(ov ?? ""),
        new: format ? format(nv) : String(nv ?? ""),
      })
    }
    return result
  } catch {
    return []
  }
}
