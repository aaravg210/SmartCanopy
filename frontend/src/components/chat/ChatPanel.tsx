'use client'

import { useEffect, useState } from 'react'
import { useChatStore } from '@/stores/chatStore'
import { useAnalysisStore } from '@/stores/analysisStore'
import ChatMessages from './ChatMessages'
import ChatInput from './ChatInput'

interface ChatPanelProps {
  isOpen: boolean
  onClose: () => void
  initialMessage?: string
}

export default function ChatPanel({ isOpen, onClose, initialMessage }: ChatPanelProps) {
  const {
    messages,
    isConnected,
    isTyping,
    currentTool,
    error,
    connect,
    disconnect,
    sendMessage,
    clearChat,
  } = useChatStore()

  const { selectedSite, currentAnalysis } = useAnalysisStore()
  const [sentInitial, setSentInitial] = useState(false)

  // Connect when panel opens
  useEffect(() => {
    if (isOpen && !isConnected) {
      connect()
    }

    return () => {
      // Don't disconnect on close - keep connection for follow-up
    }
  }, [isOpen, isConnected, connect])

  // Send initial message if provided
  useEffect(() => {
    if (isOpen && isConnected && initialMessage && !sentInitial) {
      // Build site context if we have a selected site
      const siteContext = selectedSite
        ? {
            site_id: selectedSite.site_id,
            suitability_score: selectedSite.suitability_score,
            ndvi_category: selectedSite.ndvi_category,
            slope_category: selectedSite.slope_category,
            area_sq_ft: selectedSite.area_sq_ft,
            address: currentAnalysis?.address,
          }
        : undefined

      sendMessage(initialMessage, siteContext)
      setSentInitial(true)
    }
  }, [isOpen, isConnected, initialMessage, sentInitial, selectedSite, currentAnalysis, sendMessage])

  // Reset sent flag when closed
  useEffect(() => {
    if (!isOpen) {
      setSentInitial(false)
    }
  }, [isOpen])

  const handleSend = (content: string) => {
    const siteContext = selectedSite
      ? {
          site_id: selectedSite.site_id,
          suitability_score: selectedSite.suitability_score,
          ndvi_category: selectedSite.ndvi_category,
          slope_category: selectedSite.slope_category,
          area_sq_ft: selectedSite.area_sq_ft,
          address: currentAnalysis?.address,
        }
      : undefined

    sendMessage(content, siteContext)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-y-0 right-0 w-full sm:w-[420px] bg-white shadow-2xl z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b bg-canopy-500 text-white">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
          </div>
          <div>
            <h2 className="font-semibold">SmartCanopy AI</h2>
            <div className="flex items-center gap-2 text-xs text-white/80">
              <span
                className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-green-400' : 'bg-red-400'
                }`}
              />
              {isConnected ? 'Connected' : 'Disconnected'}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={clearChat}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
            title="Clear chat"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
          </button>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
            title="Close chat"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Tool indicator */}
      {currentTool && (
        <div className="px-4 py-2 bg-amber-50 border-b border-amber-200 flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-amber-500 border-t-transparent rounded-full spinner" />
          <span className="text-sm text-amber-700">
            Using {currentTool.replace(/_/g, ' ')}...
          </span>
        </div>
      )}

      {/* Error banner */}
      {error && (
        <div className="px-4 py-3 bg-red-50 border-b border-red-200">
          <div className="flex items-start gap-2">
            <svg
              className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <div className="flex-1">
              <span className="text-sm text-red-700">{error}</span>
              <button
                onClick={() => {
                  useChatStore.getState().setError(null)
                  connect()
                }}
                className="block mt-2 text-xs text-red-600 hover:text-red-800 underline"
              >
                Retry connection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <ChatMessages messages={messages} isTyping={isTyping} />

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        disabled={!isConnected || isTyping}
        placeholder={
          isConnected
            ? 'Ask about trees, planting sites, or get recommendations...'
            : error
              ? 'Backend not connected - click retry above'
              : 'Connecting to backend...'
        }
      />

      {/* Context indicator */}
      {selectedSite && (
        <div className="px-4 py-2 bg-gray-50 border-t text-xs text-gray-500">
          Chatting about site at {currentAnalysis?.address || 'selected location'}
        </div>
      )}
    </div>
  )
}
