<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import AiChatMessage from './ai-chat-message.vue'
import type { ChatMessage } from './ai-chat-message.vue'
import { sendChatMessage, getChatQuota, type ChatQuota } from '@/api/chat-api'

const isOpen = ref(false)
const inputText = ref('')
const isTyping = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const MAX_INPUT_LENGTH = 500
const followUpSuggestions = ref<string[]>([])
const suggestionsExpanded = ref(true)
const quota = ref<ChatQuota | null>(null)
const showUpgradeDialog = ref(false)
let nextId = 1

const messages = ref<ChatMessage[]>([
  {
    id: nextId++,
    role: 'assistant',
    content: '你好！我是你的 AI 投資小幫手，可以幫你分析股票、解讀技術指標、查看篩選結果。請問有什麼想了解的？',
    timestamp: formatTime(),
  },
])

function formatTime(): string {
  const now = new Date()
  return `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const ERROR_AUTH = '請先登入後再使用 AI 小幫手。'
const ERROR_RATE_LIMIT_FALLBACK = '發送太頻繁，請稍後再試。'
const ERROR_DEFAULT = '抱歉，AI 服務暫時無法回應，請稍後再試。'

async function sendMessage() {
  const text = inputText.value.trim().slice(0, MAX_INPUT_LENGTH)
  if (!text || isTyping.value) return

  // Add user message
  messages.value.push({
    id: nextId++,
    role: 'user',
    content: text,
    timestamp: formatTime(),
  })
  inputText.value = ''
  scrollToBottom()

  isTyping.value = true
  followUpSuggestions.value = []

  try {
    // Build conversation history for API (exclude welcome message, limit to last 10)
    const history = messages.value
      .filter((m) => m.id > 1)
      .slice(-10)
      .map((m) => ({ role: m.role, content: m.content }))

    const { reply, suggestions } = await sendChatMessage(history)

    messages.value.push({
      id: nextId++,
      role: 'assistant',
      content: reply,
      timestamp: formatTime(),
    })
    followUpSuggestions.value = suggestions
    if (suggestions.length) suggestionsExpanded.value = true
  } catch (err: unknown) {
    const resp = (err as { response?: { status?: number; data?: { detail?: string } } })?.response
    const status = resp?.status
    let errorMsg = ERROR_DEFAULT
    if (status === 401 || status === 403) {
      errorMsg = ERROR_AUTH
    } else if (status === 429) {
      errorMsg = resp?.data?.detail || ERROR_RATE_LIMIT_FALLBACK
      showUpgradeDialog.value = true
    }
    messages.value.push({
      id: nextId++,
      role: 'assistant',
      content: errorMsg,
      timestamp: formatTime(),
    })
    followUpSuggestions.value = []
  } finally {
    isTyping.value = false
    scrollToBottom()
    refreshQuota()
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function refreshQuota() {
  getChatQuota().then(q => {
    quota.value = q
    if (q.daily_remaining <= 0) showUpgradeDialog.value = true
  }).catch(() => {})
}

function togglePanel() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    scrollToBottom()
    refreshQuota()
    nextTick(() => inputRef.value?.focus())
  }
}

// Quick suggestion chips — initial or follow-up from AI
const initialSuggestions = ['推薦哪些股票？', '技術指標怎麼看？', '最新 AI 報告']
const activeSuggestions = computed(() =>
  followUpSuggestions.value.length > 0
    ? followUpSuggestions.value
    : messages.value.length <= 1
      ? initialSuggestions
      : [],
)

function applySuggestion(text: string) {
  inputText.value = text
  sendMessage()
}

watch(isOpen, (val) => {
  if (val) scrollToBottom()
})
</script>

<template>
  <!-- Chat Panel -->
  <Transition name="panel">
    <div v-if="isOpen" class="ai-panel" role="dialog" aria-label="AI 小幫手對話視窗">
      <!-- Header -->
      <div class="panel-header">
        <div class="panel-title">
          <div class="title-dot" />
          <span>AI 小幫手</span>
          <span v-if="quota" class="quota-text">{{ Math.max(0, quota.daily_remaining) }}/{{ quota.daily_limit }}</span>
        </div>
        <button class="btn-close" @click="isOpen = false" aria-label="關閉">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <!-- Messages -->
      <div ref="messagesContainer" class="panel-messages" aria-live="polite">
        <AiChatMessage v-for="msg in messages" :key="msg.id" :message="msg" />

        <!-- Typing indicator -->
        <div v-if="isTyping" class="typing-indicator" role="status" aria-label="AI 正在輸入中">
          <div class="typing-dot" /><div class="typing-dot" /><div class="typing-dot" />
        </div>
      </div>

      <!-- Suggestions: initial or follow-up from AI -->
      <div v-if="activeSuggestions.length && !isTyping" class="panel-suggestions">
        <button
          class="suggestions-toggle"
          @click="suggestionsExpanded = !suggestionsExpanded"
          aria-label="展開或收合推薦問題"
        >
          <span>推薦問題</span>
          <svg
            :class="['toggle-arrow', { expanded: suggestionsExpanded }]"
            width="12" height="12" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" stroke-width="2.5"
            stroke-linecap="round" stroke-linejoin="round"
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </button>
        <div v-show="suggestionsExpanded" class="suggestions-list">
          <button
            v-for="s in activeSuggestions"
            :key="s"
            class="suggestion-chip"
            @click="applySuggestion(s)"
          >{{ s }}</button>
        </div>
      </div>

      <!-- Input -->
      <div class="panel-input">
        <input
          ref="inputRef"
          v-model="inputText"
          type="text"
          placeholder="輸入問題..."
          :maxlength="MAX_INPUT_LENGTH"
          aria-label="輸入問題給 AI 小幫手"
          @keydown="handleKeydown"
          :disabled="isTyping"
        />
        <button class="btn-send" :disabled="!inputText.trim() || isTyping" @click="sendMessage">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  </Transition>

  <!-- Floating Bubble -->
  <button :class="['ai-bubble', { active: isOpen }]" @click="togglePanel" aria-label="AI 小幫手">
    <!-- Bot icon when closed -->
    <svg v-if="!isOpen" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="11" width="18" height="10" rx="3" />
      <circle cx="9" cy="16" r="1.5" fill="currentColor" stroke="none" />
      <circle cx="15" cy="16" r="1.5" fill="currentColor" stroke="none" />
      <path d="M8.5 3.5a3.5 3.5 0 017 0V11h-7V3.5z" />
      <line x1="12" y1="1" x2="12" y2="3" />
    </svg>
    <!-- Close icon when open -->
    <svg v-else width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  </button>

  <!-- Upgrade dialog -->
  <el-dialog v-model="showUpgradeDialog" title="功能限制" width="360px" append-to-body>
    <p style="margin: 0 0 8px; color: var(--text-secondary, #8c9ab5);">您已達到 Free 會員每日使用上限。</p>
    <p style="margin: 0; color: var(--text-secondary, #8c9ab5);">升級 Premium 解鎖更多配額。</p>
    <template #footer>
      <el-button @click="showUpgradeDialog = false">關閉</el-button>
      <el-button type="warning" @click="showUpgradeDialog = false; $router.push('/pricing')">查看方案</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
/* ===== Floating Bubble ===== */
.ai-bubble {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 54px;
  height: 54px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.4);
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  z-index: 1100;
}
.ai-bubble:hover {
  transform: scale(1.08);
  box-shadow: 0 6px 24px rgba(99, 102, 241, 0.5);
}
.ai-bubble.active {
  background: var(--bg-surface);
  border: 1px solid var(--border-light);
  color: var(--text-secondary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

/* ===== Panel ===== */
.ai-panel {
  position: fixed;
  bottom: 90px;
  right: 24px;
  width: 380px;
  max-height: 520px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 1099;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5), 0 0 0 1px var(--border);
}

/* Header */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-dark);
}
.panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text);
}
.quota-text {
  font-size: 0.7rem;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-weight: 500;
  margin-left: auto;
}
.title-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  animation: blink 2s infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
.btn-close {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  transition: all 0.15s;
}
.btn-close:hover {
  background: var(--bg-surface);
  color: var(--text);
}

/* Messages */
.panel-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  min-height: 200px;
  max-height: 340px;
}

/* Typing indicator */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 10px 14px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  width: fit-content;
  margin-left: 36px;
}
.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-muted);
  animation: typingBounce 1.2s infinite;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-4px); opacity: 1; }
}

/* Suggestions */
.panel-suggestions {
  padding: 0 16px 10px;
}
.suggestions-toggle {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 0.7rem;
  font-family: var(--font-sans);
  cursor: pointer;
  padding: 2px 0 6px;
  transition: color 0.15s;
}
.suggestions-toggle:hover {
  color: var(--text-secondary);
}
.toggle-arrow {
  transition: transform 0.2s ease;
}
.toggle-arrow.expanded {
  transform: rotate(180deg);
}
.suggestions-list {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.suggestion-chip {
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 0.75rem;
  font-weight: 500;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
  font-family: var(--font-sans);
}
.suggestion-chip:hover {
  border-color: #8b5cf6;
  color: #c4b5fd;
  background: rgba(139, 92, 246, 0.08);
}

/* Input */
.panel-input {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid var(--border);
  background: var(--bg-dark);
}
.panel-input input {
  flex: 1;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 9px 16px;
  color: var(--text);
  font-size: 0.85rem;
  outline: none;
  transition: border-color 0.2s;
}
.panel-input input::placeholder {
  color: var(--text-muted);
}
.panel-input input:focus {
  border-color: #8b5cf6;
}
.btn-send {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}
.btn-send:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.4);
}
.btn-send:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ===== Transitions ===== */
.panel-enter-active {
  animation: panelIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.panel-leave-active {
  animation: panelIn 0.2s ease reverse;
}
@keyframes panelIn {
  from {
    opacity: 0;
    transform: translateY(12px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* ===== Mobile ===== */
@media (max-width: 768px) {
  .ai-bubble {
    bottom: 16px;
    right: 16px;
    width: 50px;
    height: 50px;
  }
  .ai-panel {
    bottom: 78px;
    right: 12px;
    left: 12px;
    width: auto;
    max-height: 65vh;
  }
}
</style>
