'use client'

import { useAnalysisStore } from '@/stores/analysisStore'
import { useMapStore } from '@/stores/mapStore'
import SiteDetailPanel from './SiteDetailPanel'

export default function SidePanel() {
  const { selectedSite, currentAnalysis, selectSite } = useAnalysisStore()
  const { currentTier } = useMapStore()

  if (!selectedSite || currentTier !== 'street') {
    return null
  }

  return (
    <div className="absolute top-0 right-0 h-full w-96 bg-white shadow-2xl z-20 flex flex-col overflow-hidden">
      {/* Close button */}
      <button
        onClick={() => selectSite(null)}
        className="absolute top-4 right-4 z-10 p-2 rounded-full bg-gray-100 hover:bg-gray-200 transition-colors"
        aria-label="Close panel"
      >
        <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>

      <SiteDetailPanel
        site={selectedSite}
        analysisAddress={currentAnalysis?.address}
      />
    </div>
  )
}
