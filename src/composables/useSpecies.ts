import { ref } from "vue"
import api from "../api"
import { isAuthError } from "../lib/error"

/**
 * 品种数据共享 composable
 * 多个页面复用同一份 speciesList，避免重复请求
 */
const speciesList = ref<any[]>([])
let fetchPromise: Promise<void> | null = null

export function useSpecies() {
  const fetchSpecies = async () => {
    if (speciesList.value.length > 0) return
    if (fetchPromise) return fetchPromise

    fetchPromise = (async () => {
      try {
        const res = await api.get("/species")
        speciesList.value = res.data || []
      } catch (error: any) {
        if (isAuthError(error)) return
        console.error("获取品种列表失败", error)
      } finally {
        fetchPromise = null
      }
    })()
    return fetchPromise
  }

  return { speciesList, fetchSpecies }
}
