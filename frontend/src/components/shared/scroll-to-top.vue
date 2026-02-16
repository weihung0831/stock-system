<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const isVisible = ref(false)

function handleScroll() {
  isVisible.value = window.scrollY > 300
}

function scrollToTop() {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>

<template>
  <Transition name="fade">
    <button
      v-if="isVisible"
      class="scroll-to-top"
      @click="scrollToTop"
      aria-label="回到頂部"
    >
      <svg
        width="24"
        height="24"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <polyline points="18 15 12 9 6 15"></polyline>
      </svg>
    </button>
  </Transition>
</template>

<style scoped>
.scroll-to-top {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--amber-dim), var(--amber));
  border: none;
  color: var(--bg-dark);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(229, 169, 26, 0.3);
  transition: all 0.3s ease;
  z-index: 999;
}

.scroll-to-top:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 16px rgba(229, 169, 26, 0.4);
}

.scroll-to-top:active {
  transform: translateY(-2px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* 手機版調整 */
@media (max-width: 768px) {
  .scroll-to-top {
    bottom: 16px;
    right: 16px;
    width: 44px;
    height: 44px;
  }
}
</style>
