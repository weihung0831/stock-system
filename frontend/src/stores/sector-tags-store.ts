import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  getSectorTags,
  createSectorTag,
  updateSectorTag,
  deleteSectorTag,
  seedSectorTags,
  type SectorTag,
  type SectorTagCreate,
  type SectorTagUpdate,
} from '@/api/sector-tags-api'

export const useSectorTagsStore = defineStore('sectorTags', () => {
  const tags = ref<SectorTag[]>([])
  const loading = ref(false)

  async function fetchTags() {
    loading.value = true
    try {
      tags.value = await getSectorTags()
      // Auto-seed if empty
      if (tags.value.length === 0) {
        tags.value = await seedSectorTags()
      }
    } catch (e) {
      console.error('Failed to fetch sector tags', e)
    } finally {
      loading.value = false
    }
  }

  async function addTag(body: SectorTagCreate) {
    const tag = await createSectorTag(body)
    tags.value.push(tag)
    return tag
  }

  async function editTag(id: number, body: SectorTagUpdate) {
    const tag = await updateSectorTag(id, body)
    const idx = tags.value.findIndex((t) => t.id === id)
    if (idx !== -1) tags.value[idx] = tag
    return tag
  }

  async function removeTag(id: number) {
    await deleteSectorTag(id)
    tags.value = tags.value.filter((t) => t.id !== id)
  }

  return { tags, loading, fetchTags, addTag, editTag, removeTag }
})
