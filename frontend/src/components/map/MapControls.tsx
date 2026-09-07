'use client'

import { useState, useRef, useEffect } from 'react'
import { useMapStore } from '@/stores/mapStore'
import { useAnalysisStore } from '@/stores/analysisStore'

const BAY_AREA_BBOX = '-122.5,37.0,-121.2,37.7'
const SAN_JOSE_PROXIMITY = '-121.89,37.33'

interface Suggestion {
  place_name: string
  center: [number, number] // [lon, lat]
}

export default function MapControls() {
  const { currentTier, selectedCity, resetView, flyToCoordinates } = useMapStore()
  const { analyzeAddress, isAnalyzing, analysisProgress, error, currentAnalysis, clearAnalysis, selectedSite } = useAnalysisStore()

  const [searchAddress, setSearchAddress] = useState('')
  const [showSearch, setShowSearch] = useState(false)
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [hintDismissed, setHintDismissed] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Dismiss hint when user clicks a planting site
  useEffect(() => {
    if (selectedSite) setHintDismissed(true)
  }, [selectedSite])

  // Reset hint when a new analysis starts
  useEffect(() => {
    if (!currentAnalysis) setHintDismissed(false)
  }, [currentAnalysis])

  const fetchSuggestions = (value: string) => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    if (value.length < 3) { setSuggestions([]); setShowSuggestions(false); return }

    debounceRef.current = setTimeout(async () => {
      const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN
      if (!token) return
      try {
        const encoded = encodeURIComponent(value)
        const res = await fetch(
          `https://api.mapbox.com/geocoding/v5/mapbox.places/${encoded}.json` +
          `?access_token=${token}&proximity=${SAN_JOSE_PROXIMITY}&bbox=${BAY_AREA_BBOX}&country=US&types=address&limit=5`
        )
        if (!res.ok) return
        const data = await res.json()
        const feats: Suggestion[] = (data.features ?? []).map((f: { place_name: string; center: [number, number] }) => ({
          place_name: f.place_name,
          center: f.center,
        }))
        setSuggestions(feats)
        setShowSuggestions(feats.length > 0)
      } catch { /* ignore network errors */ }
    }, 300)
  }

  const runAnalysis = async (address: string) => {
    try {
      await analyzeAddress({ address })
      const store = useAnalysisStore.getState()
      if (store.currentAnalysis) {
        flyToCoordinates([store.currentAnalysis.longitude, store.currentAnalysis.latitude], 17)
      }
    } catch (err) {
      console.error('Analysis failed:', err)
    }
  }

  const handleAnalyze = () => {
    if (!searchAddress.trim()) return
    setSuggestions([])
    setShowSuggestions(false)
    runAnalysis(searchAddress)
  }

  const handleSuggestionClick = (s: Suggestion) => {
    setSearchAddress(s.place_name)
    setSuggestions([])
    setShowSuggestions(false)
    runAnalysis(s.place_name)
  }

  const showClickHint =
    currentAnalysis && currentTier === 'street' && !selectedSite && !hintDismissed

  return (
    <>
      {/* Header with branding */}
      <div className="absolute top-4 left-4 z-10">
        <div className="bg-white rounded-lg shadow-lg px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-canopy-500 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 3L5 10h3l-3 5h3l-4 6h16l-4-6h3l-3-5h3L12 3z" />
                <rect x="10.5" y="21" width="3" height="3" rx="0.5" />
              </svg>
            </div>
            <h1 className="font-semibold text-gray-900">SmartCanopy</h1>
          </div>
        </div>
      </div>

      {/* Tier indicator and breadcrumb */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10">
        <div className="bg-white rounded-full shadow-lg px-4 py-2 flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <div className={`w-2.5 h-2.5 rounded-full transition-colors ${currentTier === 'city' ? 'bg-canopy-500' : 'bg-gray-300'}`} />
            <div className={`w-2.5 h-2.5 rounded-full transition-colors ${currentTier === 'neighborhood' ? 'bg-canopy-500' : 'bg-gray-300'}`} />
            <div className={`w-2.5 h-2.5 rounded-full transition-colors ${currentTier === 'street' ? 'bg-canopy-500' : 'bg-gray-300'}`} />
          </div>
          <div className="w-px h-4 bg-gray-300" />
          <span className="text-sm text-gray-600">
            {currentTier === 'city' && 'City Overview'}
            {currentTier === 'neighborhood' && (
              <>
                <button onClick={resetView} className="text-canopy-600 hover:text-canopy-700">US</button>
                <span className="mx-1">/</span>
                {selectedCity?.name || 'Neighborhood'}
              </>
            )}
            {currentTier === 'street' && (
              <>
                <button onClick={resetView} className="text-canopy-600 hover:text-canopy-700">US</button>
                <span className="mx-1">/</span>
                <span className="text-gray-600">{selectedCity?.name || 'Location'}</span>
                <span className="mx-1">/</span>
                Street View
              </>
            )}
          </span>
        </div>

        {/* Click-hint pill — shown after analysis until user clicks a site */}
        {showClickHint && (
          <div className="mt-2 flex justify-center">
            <span className="bg-blue-600 text-white text-xs font-medium px-4 py-1.5 rounded-full shadow-md">
              Click a blue planting site to see species &amp; benefits
            </span>
          </div>
        )}
      </div>

      {/* Search / Analyze Address */}
      <div className="absolute top-[5.5rem] left-4 z-10">
        {!showSearch ? (
          <button
            onClick={() => setShowSearch(true)}
            className="bg-white rounded-lg shadow-lg px-4 py-2.5 flex items-center gap-2 hover:bg-gray-50 transition-colors"
          >
            <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <span className="text-sm text-gray-600">Analyze an address...</span>
          </button>
        ) : (
          <div className="bg-white rounded-lg shadow-lg p-4 w-80">
            <div className="flex items-center gap-2 mb-3">
              <svg className="w-5 h-5 text-canopy-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <span className="text-sm font-medium text-gray-700">Find Planting Sites</span>
              <button
                onClick={() => { setShowSearch(false); setSearchAddress(''); setSuggestions([]); setShowSuggestions(false) }}
                className="ml-auto text-gray-400 hover:text-gray-600"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>

            <div className="relative">
              <input
                type="text"
                placeholder="Enter a Bay Area address (e.g., 123 Main St, San Jose, CA)"
                value={searchAddress}
                onChange={(e) => { setSearchAddress(e.target.value); fetchSuggestions(e.target.value) }}
                onKeyDown={(e) => { if (e.key === 'Enter') handleAnalyze(); if (e.key === 'Escape') { setSuggestions([]); setShowSuggestions(false) } }}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
                onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-canopy-500 focus:border-transparent"
                disabled={isAnalyzing}
              />
              {showSuggestions && suggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-lg shadow-xl border border-gray-200 overflow-hidden z-20">
                  {suggestions.map((s, i) => (
                    <button
                      key={i}
                      onMouseDown={() => handleSuggestionClick(s)}
                      className="w-full text-left px-3 py-2.5 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-700 border-b border-gray-100 last:border-0 transition-colors"
                    >
                      {s.place_name}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {error && <p className="text-xs text-red-500 mt-2">{error}</p>}

            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing || !searchAddress.trim()}
              className="w-full mt-3 bg-canopy-500 hover:bg-canopy-600 disabled:bg-gray-300 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {isAnalyzing ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full spinner" />
                  {analysisProgress || 'Starting analysis…'}
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
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
        <div className="absolute top-2.5 right-16 z-10">
          <div className="bg-white rounded-lg shadow-lg p-4 w-64">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Analysis Results</span>
              <button onClick={clearAnalysis} className="text-xs text-gray-400 hover:text-gray-600">Clear</button>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Planting Sites</span>
                <span className="font-medium text-canopy-600">{currentAnalysis.planting_sites.length}</span>
              </div>
            </div>
            <p className="text-xs text-gray-400 mt-2 pt-2 border-t truncate">{currentAnalysis.address}</p>
          </div>
        </div>
      )}
    </>
  )
}
