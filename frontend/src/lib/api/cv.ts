import { apiClient } from './client'
import type { AnalysisResponse, AnalysisRequest } from '@/types'

/**
 * Run CV analysis on an address
 */
export async function analyzeAddress(request: AnalysisRequest): Promise<AnalysisResponse> {
  return apiClient<AnalysisResponse>('/api/cv/analyze', {
    method: 'POST',
    body: JSON.stringify({
      address: request.address,
      buffer_m: request.buffer_m || 100,
      save_images: request.save_images !== false,
    }),
  })
}

/**
 * Get analysis results by ID
 */
export async function getAnalysis(analysisId: string): Promise<AnalysisResponse> {
  return apiClient<AnalysisResponse>(`/api/cv/analysis/${analysisId}`)
}
