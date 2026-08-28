<template>
  <transition name="bar-fade">
    <div v-if="visible" class="loading-bar">
      <div class="loading-bar-inner"></div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useUiStore } from '@/stores/ui'

const ui = useUiStore()
const visible = ref(false)
let hideTimer: ReturnType<typeof setTimeout> | null = null

watch(
  () => ui.loading,
  (loading) => {
    if (loading) {
      visible.value = true
      if (hideTimer) {
        clearTimeout(hideTimer)
        hideTimer = null
      }
    } else {
      // 保证进度条至少可见一小段时间，避免快速加载时闪烁
      hideTimer = setTimeout(() => {
        visible.value = false
      }, 300)
    }
  }
)
</script>

<style scoped>
.loading-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 3000;
  overflow: hidden;
  background: transparent;
}

.loading-bar-inner {
  height: 100%;
  width: 40%;
  border-radius: 999px;
  background: linear-gradient(90deg, #34d399, #10b981, #0d9488);
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
  animation: bar-slide 1.1s ease-in-out infinite;
}

@keyframes bar-slide {
  0% {
    transform: translateX(-110%);
  }
  100% {
    transform: translateX(350%);
  }
}

.bar-fade-enter-active,
.bar-fade-leave-active {
  transition: opacity 0.25s ease;
}

.bar-fade-enter-from,
.bar-fade-leave-to {
  opacity: 0;
}
</style>
