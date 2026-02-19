<script setup lang="ts">
export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

defineProps<{
  message: ChatMessage
}>()
</script>

<template>
  <div :class="['chat-msg', message.role]">
    <!-- Avatar -->
    <div v-if="message.role === 'assistant'" class="msg-avatar">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2a4 4 0 014 4v2a4 4 0 01-8 0V6a4 4 0 014-4z" />
        <path d="M9 14h6" /><path d="M12 14v4" />
        <circle cx="8" cy="20" r="2" /><circle cx="16" cy="20" r="2" />
      </svg>
    </div>
    <!-- Bubble -->
    <div class="msg-bubble">
      <p class="msg-text">{{ message.content }}</p>
      <span class="msg-time">{{ message.timestamp }}</span>
    </div>
  </div>
</template>

<style scoped>
.chat-msg {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
  align-items: flex-end;
}
.chat-msg.user {
  flex-direction: row-reverse;
}
.msg-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--amber-dim), var(--amber));
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--bg-dark);
}
.msg-bubble {
  max-width: 78%;
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 0.85rem;
  line-height: 1.55;
}
.chat-msg.assistant .msg-bubble {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  border-bottom-left-radius: 4px;
}
.chat-msg.user .msg-bubble {
  background: linear-gradient(135deg, var(--amber-dim), var(--amber));
  color: var(--bg-dark);
  border-bottom-right-radius: 4px;
}
.msg-text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}
.msg-time {
  display: block;
  font-size: 0.65rem;
  margin-top: 4px;
  opacity: 0.5;
  font-family: var(--font-mono);
}
.chat-msg.user .msg-time {
  text-align: right;
}
</style>
