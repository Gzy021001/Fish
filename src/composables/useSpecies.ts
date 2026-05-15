import { ref } from "vue"
import api from "../api"
import { isAuthError } from "../lib/error"

const speciesList = ref<any[]>([])
let fetchPromise: Promise<void> | null = null

const preloadImages = (list: any[]) => {
  for (const sp of list) {
    if (sp.image_url) {
      const img = new Image()
      img.src = sp.image_url
    }
  }
}

export function useSpecies() {
  const fetchSpecies = async () => {
    if (fetchPromise) return fetchPromise

    fetchPromise = (async () => {
      try {
        const res = await api.get("/species")
        speciesList.value = res.data || []
        preloadImages(speciesList.value)
      } catch (error: any) {
        if (isAuthError(error)) return
        console.error("获取品种列表失败", error)
      } finally {
        fetchPromise = null
      }
    })()
    return fetchPromise
  }

  const invalidateCache = () => {
    speciesList.value = []
  }

  return { speciesList, fetchSpecies, invalidateCache }
}
