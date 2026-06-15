function parseUTC(dateStr: string | undefined | null): Date | null {
  if (!dateStr) return null
  // 处理 yyyy-mm 格式（缺日期），自动补为当月1日
  if (/^\d{4}-\d{2}$/.test(dateStr)) {
    dateStr = dateStr + "-01"
  }
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

/**
 * 压缩图片
 * @param file 原始文件
 * @param maxWidth 最大宽度
 * @param maxHeight 最大高度
 * @param quality 压缩质量 (0-1)
 */
export async function compressImage(
  file: File,
  maxWidth = 800,
  maxHeight = 800,
  quality = 0.8,
): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = (e) => {
      const img = new Image()
      img.src = e.target?.result as string
      img.onload = () => {
        const canvas = document.createElement("canvas")
        let width = img.width
        let height = img.height

        if (width > height) {
          if (width > maxWidth) {
            height *= maxWidth / width
            width = maxWidth
          }
        } else {
          if (height > maxHeight) {
            width *= maxHeight / height
            height = maxHeight
          }
        }

        canvas.width = width
        canvas.height = height
        const ctx = canvas.getContext("2d")
        ctx?.drawImage(img, 0, 0, width, height)

        canvas.toBlob(
          (blob) => {
            if (blob) {
              resolve(blob)
            } else {
              reject(new Error("Canvas to Blob failed"))
            }
          },
          "image/jpeg",
          quality,
        )
      }
      img.onerror = reject
    }
    reader.onerror = reject
  })
}
