'use client'

import { useState } from 'react'
import { useMapStore } from '@/stores/mapStore'
import { useAnalysisStore } from '@/stores/analysisStore'

export default function MapControls() {
  const { currentTier, selectedCity, resetView, flyToCoordinates } = useMapStore()
  const { analyzeAddress, isAnalyzing, error, currentAnalysis, clearAnalysis } = useAnalysisStore()

  const [searchAddress, setSearchAddress] = useState('')
  const [showSearch, setShowSearch] = useState(false)

  const handleAnalyze = async () => {
    if (!searchAddress.trim()) return

    try {
      await analyzeAddress({ address: searchAddress })

      // After analysis, fly to the location
      // The coordinates come from the analysis response
      const store = useAnalysisStore.getState()
      if (store.currentAnalysis) {
        flyToCoordinates(
          [store.currentAnalysis.longitude, store.currentAnalysis.latitude],
          17
        )
      }
    } catch (err) {
      console.error('Analysis failed:', err)
    }
  }

  return (
    <>
      {/* Header with branding */}
      <div className="absolute top-4 left-4 z-10">
        <div className="bg-white rounded-lg shadow-lg px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-canopy-500 rounded-lg flex items-center justify-center">
              <svg
                className="w-5 h-5 text-white"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.715-5.349L11 6.477V16h2a1 1 0 110 2H7a1 1 0 110-2h2V6.477L6.237 7.582l1.715 5.349a1 1 0 01-.285 1.05A3.989 3.989 0 015 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L9 4.323V3a1 1 0 011-1z" />
              </svg>
            </div>
            <div>
              <h1 className="font-semibold text-gray-900">SmartCanopy</h1>
              <p className="text-xs text-gray-500">Urban Tree AI</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tier indicator and breadcrumb */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10">
        <div className="bg-white rounded-full shadow-lg px-4 py-2 flex items-center gap-2">
          {/* Tier indicator dots */}
          <div className="flex items-center gap-1.5">
            <div
              className={`w-2.5 h-2.5 rounded-full transition-colors ${
                currentTier === 'city'
                  ? 'bg-canopy-500'
                  : 'bg-gray-300'
              }`}
            />
            <div
              className={`w-2.5 h-2.5 rounded-full transition-colors ${
                currentTier === 'neighborhood'
                  ? 'bg-canopy-500'
                  : 'bg-gray-300'
              }`}
            />
            <div
              className={`w-2.5 h-2.5 rounded-full transition-colors ${
                currentTier === 'street'
                  ? 'bg-canopy-500'
                  : 'bg-gray-300'
              }`}
            />
          </div>

          {/* Divider */}
          <div className="w-px h-4 bg-gray-300" />

          {/* Current view label */}
          <span className="text-sm text-gray-600">
            {currentTier === 'city' && 'City Overview'}
            {currentTier === 'neighborhood' && (
              <>
                <button
                  onClick={resetView}
                  className="text-canopy-600 hover:text-canopy-700"
                >
                  US
                </button>
                <span className="mx-1">/</span>
                {selectedCity?.name || 'Neighborhood'}
              </>
            )}
            {currentTier === 'street' && (
              <>
                <button
                  onClick={resetView}
                  className="text-canopy-600 hover:text-canopy-700"
                >
                  US
                </button>
                <span className="mx-1">/</span>
                <span className="text-gray-600">{selectedCity?.name || 'Location'}</span>
                <span className="mx-1">/</span>
                Street View
              </>
            )}
          </span>
        </div>
      </div>

      {/* Search / Analyze Address */}
      <div className="absolute top-20 left-4 z-10">
        {!showSearch ? (
          <button
            onClick={() => setShowSearch(true)}
            className="bg-white rounded-lg shadow-lg px-4 py-2.5 flex items-center gap-2 hover:bg-gray-50 transition-colors"
          >
            <svg
              className="w-5 h-5 text-gray-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <span className="text-sm text-gray-600">Analyze an address...</span>
          </button>
        ) : (
          <div className="bg-white rounded-lg shadow-lg p-4 w-80">
            <div className="flex items-center gap-2 mb-3">
              <svg
                className="w-5 h-5 text-canopy-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              <span className="text-sm font-medium text-gray-700">
                Find Planting Sites
              </span>
              <button
                onClick={() => {
                  setShowSearch(false)
                  setSearchAddress('')
                }}
                className="ml-auto text-gray-400 hover:text-gray-600"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>

            <input
              type="text"
              placeholder="Enter address (e.g., 123 Main St, San Jose, CA)"
              value={searchAddress}
              onChange={(e) => setSearchAddress(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-canopy-500 focus:border-transparent"
              disabled={isAnalyzing}
            />

            {error && (
              <p className="text-xs text-red-500 mt-2">{error}</p>
            )}

            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing || !searchAddress.trim()}
              className="w-full mt-3 bg-canopy-500 hover:bg-canopy-600 disabled:bg-gray-300 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {isAnalyzing ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full spinner" />
                  Analyzing... (30-60s)
                </>
              ) : (
                <>
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
                    />
                  </svg>
                  Run CV Analysis
                </>
              )}
            </button>

            <p className="text-xs text-gray-500 mt-2">
              Uses satellite imagery and AI to identify optimal planting locations
            </p>
          </div>
        )}
      </div>

      {/* Analysis Results Summary */}
      {currentAnalysis && currentTier === 'street' && (
        <div className="absolute top-20 right-4 z-10">
          <div className="bg-white rounded-lg shadow-lg p-4 w-64">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Analysis Results</span>
              <button
                onClick={clearAnalysis}
                className="text-xs text-gray-400 hover:text-gray-600"
              >
                Clear
              </button>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Planting Sites</span>
                <span className="font-medium text-canopy-600">
                  {currentAnalysis.planting_sites.length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Existing Trees</span>
                <span className="font-medium text-gray-700">
                  {currentAnalysis.existing_trees_count}
                </span>
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-2 pt-2 border-t truncate">
              {currentAnalysis.address}
            </p>
          </div>
        </div>
      )}

      {/* Instructions hint */}
      {currentTier === 'city' && !showSearch && (
        <div className="absolute bottom-8 right-4 z-10">
          <div className="bg-white/90 backdrop-blur-sm rounded-lg shadow-lg px-4 py-3 max-w-xs">
            <p className="text-sm text-gray-600">
              <span className="font-medium text-gray-900">Click a city</span> to explore
              neighborhoods, or <span className="font-medium text-gray-900">search an address</span> to
              find planting sites
            </p>
          </div>
        </div>
      )}
    </>
  )
}
