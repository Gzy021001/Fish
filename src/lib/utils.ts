import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function parseUTC(dateStr: string | undefined | null): Date | null {
  if (!dateStr) return null
  if (dateStr.endsWith("Z") || dateStr.includes("+") || dateStr.includes("[")) {
    return new Date(dateStr)
  }
  return new Date(dateStr + "Z")
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

// ============================================================
//  审计日志差异对比
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
