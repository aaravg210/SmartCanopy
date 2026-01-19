'use client'

import { useState, useEffect } from 'react'
import { useAnalysisStore } from '@/stores/analysisStore'
import { useMapStore } from '@/stores/mapStore'
import SiteDetailPanel from './SiteDetailPanel'
import ChatPanel from '../chat/ChatPanel'

interface SidePanelProps {
  askAITrigger?: number
}

export default function SidePanel({ askAITrigger = 0 }: SidePanelProps) {
  const { selectedSite, currentAnalysis, selectSite } = useAnalysisStore()
  const { currentTier } = useMapStore()
  const [chatOpen, setChatOpen] = useState(false)
  const [chatInitialMessage, setChatInitialMessage] = useState<string | undefined>()

  // Open chat when askAITrigger changes (triggered by "Ask SmartCanopy AI" button)
  useEffect(() => {
    if (askAITrigger > 0 && selectedSite) {
      // Create a contextual initial message based on the selected site
      const initialMsg = `I'm looking at planting site #${selectedSite.site_id.slice(0, 8)} at ${currentAnalysis?.address || 'this location'}. It has ${selectedSite.ndvi_category.replace(/_/g, ' ')} vegetation, ${selectedSite.slope_category} terrain, and about ${selectedSite.area_sq_ft.toLocaleString()} square feet of space. What tree species would you recommend for this site?`
      setChatInitialMessage(initialMsg)
      setChatOpen(true)
    }
  }, [askAITrigger, selectedSite, currentAnalysis])

  const handleOpenChat = (initialMessage?: string) => {
    setChatInitialMessage(initialMessage)
    setChatOpen(true)
  }

  // Only show panel when we have a selected site at street level
  if (!selectedSite || currentTier !== 'street') {
    return (
      <>
        {/* Chat panel can still be opened via FAB */}
        <ChatFAB onClick={() => handleOpenChat()} />
        <ChatPanel
          isOpen={chatOpen}
          onClose={() => {
            setChatOpen(false)
            setChatInitialMessage(undefined)
          }}
          initialMessage={chatInitialMessage}
        />
      </>
    )
  }

  return (
    <>
      <div className="absolute top-0 right-0 h-full w-96 bg-white shadow-2xl z-20 overflow-hidden">
        {/* Close button */}
        <button
          onClick={() => selectSite(null)}
          className="absolute top-4 right-4 z-10 p-2 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
          aria-label="Close panel"
        >
          <svg
            className="w-5 h-5 text-gray-600"
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

        {/* Scrollable content */}
        <div className="h-full overflow-y-auto custom-scrollbar">
          <SiteDetailPanel
            site={selectedSite}
            analysisAddress={currentAnalysis?.address}
            onOpenChat={handleOpenChat}
          />
        </div>
      </div>

      {/* Chat panel */}
      <ChatPanel
        isOpen={chatOpen}
        onClose={() => {
          setChatOpen(false)
          setChatInitialMessage(undefined)
        }}
        initialMessage={chatInitialMessage}
      />
    </>
  )
}

// Floating action button for chat when no site is selected
function ChatFAB({ onClick }: { onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="fixed bottom-6 right-6 w-14 h-14 bg-canopy-500 hover:bg-canopy-600 text-white rounded-full shadow-lg z-30 flex items-center justify-center transition-all hover:scale-105"
      aria-label="Open chat"
    >
      <svg
        className="w-6 h-6"
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
    </button>
  )
}
