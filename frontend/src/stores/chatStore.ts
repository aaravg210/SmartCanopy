import { create } from 'zustand'
import type { ChatMessage, ToolCall, WSMessage } from '@/types'
import { getWebSocketUrl } from '@/lib/api/client'

interface ChatState {
  // Chat state
  messages: ChatMessage[]
  conversationId: string
  isConnected: boolean
  isTyping: boolean
  currentTool: string | null
  error: string | null

  // WebSocket reference
  ws: WebSocket | null

  // Actions
  connect: (conversationId?: string) => void
  disconnect: () => void
  sendMessage: (content: string, siteContext?: Record<string, unknown>) => void
  addMessage: (message: ChatMessage) => void
  updateLastMessage: (content: string) => void
  setTyping: (typing: boolean) => void
  setCurrentTool: (tool: string | null) => void
  clearChat: () => void
  setError: (error: string | null) => void
}

function generateId(): string {
  return Math.random().toString(36).substring(2) + Date.now().toString(36)
}

export const useChatStore = create<ChatState>((set, get) => ({
  // Initial state
  messages: [],
  conversationId: generateId(),
  isConnected: false,
  isTyping: false,
  currentTool: null,
  error: null,
  ws: null,

  // Connect to WebSocket
  connect: (conversationId) => {
    const state = get()

    // Don't reconnect if already connected
    if (state.ws?.readyState === WebSocket.OPEN) {
      return
    }

    const convId = conversationId || state.conversationId
    const wsUrl = getWebSocketUrl(convId)

    try {
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        set({ isConnected: true, error: null, ws })
        console.log('WebSocket connected')
      }

      ws.onclose = () => {
        set({ isConnected: false, ws: null })
        console.log('WebSocket disconnected')
      }

      ws.onerror = (event) => {
        console.error('WebSocket error:', event)
        set({
          error: 'Cannot connect to backend. Start the API server with: uvicorn api.main:app --reload',
          isConnected: false,
          ws: null
        })
      }

      ws.onmessage = (event) => {
        try {
          const data: WSMessage = JSON.parse(event.data)
          const { updateLastMessage, setTyping, setCurrentTool, addMessage } = get()

          switch (data.type) {
            case 'chunk':
              setTyping(true)
              updateLastMessage(data.text)
              break

            case 'tool_use':
              setCurrentTool(data.tool_name)
              break

            case 'tool_result':
              setCurrentTool(null)
              break

            case 'complete':
              setTyping(false)
              setCurrentTool(null)
              // Update the last assistant message with complete response
              set((state) => {
                const messages = [...state.messages]
                const lastIdx = messages.findIndex(
                  (m) => m.role === 'assistant' && m.isPartial
                )
                if (lastIdx >= 0) {
                  messages[lastIdx] = {
                    ...messages[lastIdx],
                    content: data.full_response,
                    isPartial: false,
                    toolCalls: data.tool_calls,
                  }
                }
                return { messages }
              })
              break

            case 'error':
              setTyping(false)
              setCurrentTool(null)
              set({ error: data.message })
              break
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      set({ ws, conversationId: convId })
    } catch (err) {
      console.error('Failed to connect WebSocket:', err)
      set({ error: 'Failed to connect to chat service' })
    }
  },

  // Disconnect WebSocket
  disconnect: () => {
    const { ws } = get()
    if (ws) {
      ws.close()
      set({ ws: null, isConnected: false })
    }
  },

  // Send a message
  sendMessage: (content, siteContext) => {
    const { ws, isConnected, addMessage } = get()

    if (!isConnected || !ws) {
      set({ error: 'Not connected to chat service' })
      return
    }

    // Add user message to state
    addMessage({
      id: generateId(),
      role: 'user',
      content,
      timestamp: new Date(),
    })

    // Create placeholder for assistant response
    addMessage({
      id: generateId(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isPartial: true,
    })

    // Send to server
    ws.send(
      JSON.stringify({
        message: content,
        site_context: siteContext,
      })
    )
  },

  // Add a message
  addMessage: (message) => {
    set((state) => ({
      messages: [...state.messages, message],
    }))
  },

  // Update last assistant message (for streaming)
  updateLastMessage: (content) => {
    set((state) => {
      const messages = [...state.messages]
      const lastIdx = messages.length - 1
      if (lastIdx >= 0 && messages[lastIdx].role === 'assistant') {
        messages[lastIdx] = {
          ...messages[lastIdx],
          content: messages[lastIdx].content + content,
        }
      }
      return { messages }
    })
  },

  // Set typing indicator
  setTyping: (typing) => set({ isTyping: typing }),

  // Set current tool being executed
  setCurrentTool: (tool) => set({ currentTool: tool }),

  // Clear chat
  clearChat: () => {
    const { disconnect } = get()
    disconnect()
    set({
      messages: [],
      conversationId: generateId(),
      isTyping: false,
      currentTool: null,
      error: null,
    })
  },

  // Set error
  setError: (error) => set({ error }),
}))
