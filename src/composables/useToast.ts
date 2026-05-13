import { reactive } from "vue"

export interface Toast {
  id: number
  message: string
  type: "success" | "error" | "warning" | "info"
  timerId: ReturnType<typeof setTimeout> | null
}

const toasts = reactive<Toast[]>([])

let nextId = 1

export const TOAST_DURATION = 3500

function add(message: string, type: Toast["type"] = "info") {
  const id = nextId++
  const toast: Toast = { id, message, type, timerId: null }
  toasts.push(toast)
  toast.timerId = setTimeout(() => {
    remove(id)
  }, TOAST_DURATION)
}

function remove(id: number) {
  const idx = toasts.findIndex((t) => t.id === id)
  if (idx < 0) return
  const toast = toasts[idx]
  if (toast.timerId) {
    clearTimeout(toast.timerId)
    toast.timerId = null
  }
  toasts.splice(idx, 1)
}

export function useToast() {
  return {
    toasts,
    remove,
    success: (msg: string) => add(msg, "success"),
    error: (msg: string) => add(msg, "error"),
    warning: (msg: string) => add(msg, "warning"),
    info: (msg: string) => add(msg, "info"),
  }
}
