import { create } from 'zustand'
import type { AnalysisResponse, PlantingSiteResponse, AnalysisRequest } from '@/types'
import { analyzeAddressWithPolling } from '@/lib/api/cv'

interface AnalysisState {
  currentAnalysis: AnalysisResponse | null
  selectedSite: PlantingSiteResponse | null
  isAnalyzing: boolean
  analysisProgress: string
  error: string | null

  analyzeAddress: (request: AnalysisRequest) => Promise<void>
  selectSite: (site: PlantingSiteResponse | null) => void
  clearAnalysis: () => void
  setError: (error: string | null) => void
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
  currentAnalysis: null,
  selectedSite: null,
  isAnalyzing: false,
  analysisProgress: '',
  error: null,

  analyzeAddress: async (request) => {
    set({ isAnalyzing: true, error: null, analysisProgress: 'Geocoding address…' })

    try {
      const response = await analyzeAddressWithPolling(request, {
        intervalMs: 3000,
        timeoutMs: 180_000,
        onProgress: (msg) => set({ analysisProgress: msg }),
      })

      set({
        currentAnalysis: response,
        isAnalyzing: false,
        analysisProgress: '',
        selectedSite: null,
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Analysis failed'
      set({ isAnalyzing: false, analysisProgress: '', error: message })
      throw error
    }
  },

  selectSite: (site) => set({ selectedSite: site }),

  clearAnalysis: () => set({ currentAnalysis: null, selectedSite: null, error: null }),

  setError: (error) => set({ error }),
}))
