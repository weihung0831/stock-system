<script setup lang="ts">
import { computed } from 'vue'
import { useSectorTagsStore } from '@/stores/sector-tags-store'

interface Props {
  industry: string | null
}

const props = defineProps<Props>()
const store = useSectorTagsStore()

const sectorInfo = computed(() => {
  if (!props.industry) return { color: '#9ca3af', label: '其他' }

  for (const tag of store.tags) {
    const keywords = tag.keywords || tag.name
    if (props.industry.includes(keywords)) {
      return { color: tag.color, label: tag.name }
    }
  }

  return { color: '#9ca3af', label: '其他' }
})
</script>

<template>
  <span class="sector-tag" :style="{ borderColor: sectorInfo.color + '40', color: sectorInfo.color }">
    <span class="cat-dot" :style="{ background: sectorInfo.color }"></span>
    {{ sectorInfo.label }}
  </span>
</template>
