import { shallowRef } from 'vue'
import api from '../api'
import { isAuthError } from '../lib/error'
import type { Species, ApiError } from '../types'

const speciesList = shallowRef<Species[]>([])
let fetchPromise: Promise<void> | null = null

const preloadImages = (list: Species[]) => {
  const batch = list.slice(0, 10)
  for (const sp of batch) {
    if (sp.image_url) {
      const img = new Image()
      img.src = sp.image_url
    }
  }
  for (let i = 10; i < list.length; i++) {
    const sp = list[i]
    if (sp.image_url) {
      const img = new Image()
      img.loading = 'lazy'
      img.src = sp.image_url
    }
  }
}

export function useSpecies() {
  const fetchSpecies = async () => {
    if (fetchPromise) return fetchPromise

    fetchPromise = (async () => {
      try {
        const res = await api.get('/species')
        speciesList.value = Array.isArray(res.data) ? res.data : []
        preloadImages(speciesList.value)
      } catch (error: unknown) {
        if (isAuthError(error as ApiError)) return
        console.error('获取品种列表失败', error)
      } finally {
        fetchPromise = null
      }
    })()
    return fetchPromise
  }

  const invalidateCache = () => {
    speciesList.value = []
    return fetchSpecies()
  }

  return { speciesList, fetchSpecies, invalidateCache }
}
