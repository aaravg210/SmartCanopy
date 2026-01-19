'use client'

import { useEffect, useRef } from 'react'
import type { ChatMessage } from '@/types'

interface ChatMessagesProps {
  messages: ChatMessage[]
  isTyping: boolean
}

export default function ChatMessages({ messages, isTyping }: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="text-center">
          <div className="w-16 h-16 bg-canopy-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-8 h-8 text-canopy-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
              />
            </svg>
          </div>
          <h3 className="font-medium text-gray-900 mb-1">
            SmartCanopy AI Assistant
          </h3>
          <p className="text-sm text-gray-500 max-w-xs">
            I can help you find the best trees for your planting site,
            calculate environmental benefits, and provide planting guidance.
          </p>
          <div className="mt-4 space-y-2">
            <p className="text-xs text-gray-400">Try asking:</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {[
                'What trees grow well here?',
                'Estimate planting costs',
                'CO2 benefits of oak trees',
              ].map((suggestion) => (
                <span
                  key={suggestion}
                  className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full"
                >
                  {suggestion}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} />
      ))}

      {/* Typing indicator */}
      {isTyping && messages[messages.length - 1]?.content === '' && (
        <div className="flex items-center gap-2 text-gray-400">
          <div className="flex gap-1">
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
          <span className="text-sm">Thinking...</span>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  )
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'
  const isSystem = message.role === 'system'

  if (isSystem) {
    return (
      <div className="text-center py-2">
        <span className="text-xs text-gray-400 bg-gray-100 px-3 py-1 rounded-full">
          {message.content}
        </span>
      </div>
    )
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
          isUser
            ? 'bg-canopy-500 text-white rounded-br-md'
            : 'bg-gray-100 text-gray-800 rounded-bl-md'
        }`}
      >
        {/* Message content */}
        <div className="text-sm whitespace-pre-wrap">{message.content}</div>

        {/* Tool calls indicator */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-200/20">
            <div className="flex flex-wrap gap-1">
              {message.toolCalls.map((tool, idx) => (
                <span
                  key={idx}
                  className={`text-xs px-2 py-0.5 rounded ${
                    isUser
                      ? 'bg-white/20 text-white'
                      : 'bg-gray-200 text-gray-600'
                  }`}
                >
                  {tool.tool.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Timestamp */}
        <div
          className={`text-xs mt-1 ${
            isUser ? 'text-white/60' : 'text-gray-400'
          }`}
        >
          {message.timestamp.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </div>
      </div>
    </div>
  )
}
