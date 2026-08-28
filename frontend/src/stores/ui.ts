import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUiStore = defineStore('ui', () => {
  const pendingCount = ref(0)
  const startedAt = ref(0)

  const loading = computed(() => pendingCount.value > 0)

  function start() {
    if (pendingCount.value === 0) {
      startedAt.value = Date.now()
    }
    pendingCount.value++
  }

  function stop() {
    pendingCount.value = Math.max(0, pendingCount.value - 1)
  }

  return { pendingCount, startedAt, loading, start, stop }
})
