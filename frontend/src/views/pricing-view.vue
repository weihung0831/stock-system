<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth-store'

const authStore = useAuthStore()
const currentTier = computed(() =>
  authStore.user?.is_admin ? 'premium' : authStore.user?.membership_tier ?? 'free'
)

const plans = [
  {
    key: 'free',
    name: 'Free',
    label: '免費方案',
    price: 'NT$0',
    period: '永久免費',
    features: [
      'AI 聊天 10 則/天',
      'AI 報告 5 檔/天',
      '全部篩選功能',
      '回測功能',
      '籌碼分析',
    ],
    highlight: false,
  },
  {
    key: 'premium',
    name: 'Premium',
    label: '進階方案',
    price: '即將推出',
    period: '',
    features: [
      'AI 聊天 100 則/天',
      'AI 報告不限檔數',
      '全部篩選功能',
      '回測功能',
      '籌碼分析',
      '優先客服支援',
    ],
    highlight: true,
  },
]
</script>

<template>
  <div class="pricing-page" style="animation: fadeIn 0.3s ease">
    <div class="pricing-header">
      <h1 class="pricing-title">選擇你的方案</h1>
      <p class="pricing-subtitle">解鎖更多 AI 分析能力，讓投資決策更有效率</p>
    </div>

    <div class="pricing-grid">
      <div
        v-for="plan in plans"
        :key="plan.key"
        class="pricing-card"
        :class="{ highlighted: plan.highlight, current: currentTier === plan.key }"
      >
        <!-- Current badge -->
        <div v-if="currentTier === plan.key" class="current-badge">目前方案</div>

        <!-- Recommended badge -->
        <div v-if="plan.highlight && currentTier !== plan.key" class="recommended-badge">推薦</div>

        <div class="plan-name">{{ plan.name }}</div>
        <div class="plan-label">{{ plan.label }}</div>
        <div class="plan-price">{{ plan.price }}</div>
        <div v-if="plan.period" class="plan-period">{{ plan.period }}</div>

        <ul class="plan-features">
          <li v-for="feat in plan.features" :key="feat">
            <span class="check">&#10003;</span>
            {{ feat }}
          </li>
        </ul>

        <button
          v-if="plan.key === 'premium' && currentTier !== 'premium'"
          class="plan-btn premium-btn"
          disabled
        >
          敬請期待
        </button>
        <button v-else-if="currentTier === plan.key" class="plan-btn current-btn" disabled>
          目前使用中
        </button>
      </div>
    </div>

    <p class="pricing-note">
      Premium 方案即將推出，如需提前開通請聯繫管理員。
    </p>
  </div>
</template>

<style scoped>
.pricing-page {
  padding: 40px 24px;
  max-width: 760px;
  margin: 0 auto;
}
.pricing-header {
  text-align: center;
  margin-bottom: 36px;
}
.pricing-title {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--text);
  margin-bottom: 8px;
}
.pricing-subtitle {
  font-size: 0.9rem;
  color: var(--text-muted);
}
.pricing-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
.pricing-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 28px 24px;
  position: relative;
  transition: border-color 0.2s, transform 0.2s;
}
.pricing-card:hover {
  transform: translateY(-3px);
}
.pricing-card.highlighted {
  border-color: rgba(229, 169, 26, 0.4);
  background: linear-gradient(180deg, rgba(229, 169, 26, 0.06), var(--bg-card));
}
.pricing-card.current {
  border-color: rgba(229, 169, 26, 0.5);
}
.current-badge, .recommended-badge {
  position: absolute;
  top: -10px;
  right: 16px;
  font-size: 0.68rem;
  font-weight: 700;
  padding: 3px 12px;
  border-radius: 10px;
}
.current-badge {
  background: #e5a91a;
  color: #080c14;
}
.recommended-badge {
  background: #e5a91a;
  color: #080c14;
}
.plan-name {
  font-size: 1.3rem;
  font-weight: 800;
  color: var(--text);
  font-family: var(--font-mono);
}
.plan-label {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: 2px;
}
.plan-price {
  font-size: 1.8rem;
  font-weight: 800;
  color: #e5a91a;
  margin-top: 16px;
  font-family: var(--font-mono);
}
.plan-period {
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-top: 2px;
}
.plan-features {
  list-style: none;
  padding: 0;
  margin: 20px 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.plan-features li {
  font-size: 0.85rem;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 8px;
}
.check {
  color: var(--up, #22c55e);
  font-weight: 700;
  font-size: 0.9rem;
}
.plan-btn {
  width: 100%;
  padding: 10px;
  border-radius: 8px;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
  border: 1px solid var(--border);
  transition: all 0.2s;
  margin-top: 8px;
}
.premium-btn {
  background: rgba(229, 169, 26, 0.12);
  color: #e5a91a;
  border-color: rgba(229, 169, 26, 0.3);
}
.premium-btn:not(:disabled):hover {
  background: rgba(229, 169, 26, 0.2);
  border-color: #e5a91a;
}
.premium-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.current-btn {
  background: var(--bg-surface);
  color: var(--text-muted);
  cursor: default;
}
.pricing-note {
  text-align: center;
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: 28px;
}
@media (max-width: 600px) {
  .pricing-grid { grid-template-columns: 1fr; }
}
</style>
