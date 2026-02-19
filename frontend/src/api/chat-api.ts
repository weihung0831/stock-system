import axios from 'axios'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  reply: string
  suggestions: string[]
}

/** Dedicated chat client that doesn't trigger global 401 redirect */
const chatClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 120000,
  headers: { 'Content-Type': 'application/json' },
})

chatClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/** Send chat messages to AI assistant and get reply with follow-up suggestions */
export async function sendChatMessage(
  messages: ChatMessage[],
): Promise<ChatResponse> {
  const { data } = await chatClient.post<ChatResponse>('/chat', { messages })
  return data
}
