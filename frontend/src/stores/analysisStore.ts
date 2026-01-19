import { create } from 'zustand'
import type { AnalysisResponse, PlantingSiteResponse, AnalysisRequest } from '@/types'
import { apiClient } from '@/lib/api/client'

interface AnalysisState {
  // Analysis data
  currentAnalysis: AnalysisResponse | null
  selectedSite: PlantingSiteResponse | null

  // Loading states
  isAnalyzing: boolean
  error: string | null

  // Actions
  analyzeAddress: (request: AnalysisRequest) => Promise<void>
  selectSite: (site: PlantingSiteResponse | null) => void
  clearAnalysis: () => void
  setError: (error: string | null) => void
}

export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  // Initial state
  currentAnalysis: null,
  selectedSite: null,
  isAnalyzing: false,
  error: null,

  // Analyze an address using the CV API
  analyzeAddress: async (request: AnalysisRequest) => {
    set({ isAnalyzing: true, error: null })

    try {
      const response = await apiClient<AnalysisResponse>('/api/cv/analyze', {
        method: 'POST',
        body: JSON.stringify({
          address: request.address,
          buffer_m: request.buffer_m || 100,
          save_images: request.save_images !== false,
        }),
      })

      set({
        currentAnalysis: response,
        isAnalyzing: false,
        selectedSite: null,
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Analysis failed'
      set({
        isAnalyzing: false,
        error: message,
      })
      throw error
    }
  },

  // Select a planting site
  selectSite: (site) => set({ selectedSite: site }),

  // Clear current analysis
  clearAnalysis: () =>
    set({
      currentAnalysis: null,
      selectedSite: null,
      error: null,
    }),

  // Set error message
  setError: (error) => set({ error }),
}))
