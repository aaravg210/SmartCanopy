import { apiClient } from './client'
import type { AnalysisResponse, AnalysisRequest, JobSubmitResponse, JobStatusResponse, SpeciesData } from '@/types'

// Bay Area bounding box and proximity bias for Mapbox geocoding
const BAY_AREA_BBOX = '-122.5,37.0,-121.2,37.7'
const SAN_JOSE_PROXIMITY = '-121.89,37.33'

/**
 * Geocode an address using Mapbox with Bay Area proximity bias.
 * Returns {lat, lon} or null if geocoding fails or is outside the Bay Area.
 */
export async function geocodeAddress(address: string): Promise<{ lat: number; lon: number } | null> {
  const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN
  if (!token) {
    console.warn('No Mapbox token — backend will use Nominatim fallback')
    return null
  }

  const encoded = encodeURIComponent(address)
  const url =
    `https://api.mapbox.com/geocoding/v5/mapbox.places/${encoded}.json` +
    `?access_token=${token}` +
    `&proximity=${SAN_JOSE_PROXIMITY}` +
    `&bbox=${BAY_AREA_BBOX}` +
    `&country=US` +
    `&limit=1`

  try {
    const res = await fetch(url)
    if (!res.ok) return null
    const data = await res.json()
    const feature = data.features?.[0]
    if (!feature) return null
    const [lon, lat] = feature.center
    return { lat, lon }
  } catch {
    return null
  }
}

/**
 * Check whether coordinates fall within the OCF Bay Area service area.
 */
export function isInBayArea(lat: number, lon: number): boolean {
  return lat >= 37.0 && lat <= 37.7 && lon >= -122.5 && lon <= -121.2
}

/**
 * Submit an address for CV analysis. Returns a job_id immediately.
 */
export async function submitAnalysis(request: AnalysisRequest): Promise<JobSubmitResponse> {
  return apiClient<JobSubmitResponse>('/api/cv/analyze', {
    method: 'POST',
    body: JSON.stringify({
      address: request.address,
      latitude: request.latitude,
      longitude: request.longitude,
      buffer_m: request.buffer_m ?? 100,
      save_images: request.save_images !== false,
    }),
  })
}

/**
 * Poll the status of a submitted CV analysis job.
 */
export async function pollJob(jobId: string): Promise<JobStatusResponse> {
  return apiClient<JobStatusResponse>(`/api/cv/jobs/${jobId}`)
}

/**
 * Submit analysis + poll until complete. Calls onProgress on each poll tick.
 * Resolves to the final AnalysisResponse. Rejects on error or timeout.
 */
export async function analyzeAddressWithPolling(
  request: AnalysisRequest,
  options: {
    intervalMs?: number
    timeoutMs?: number
    onProgress?: (message: string) => void
  } = {}
): Promise<AnalysisResponse> {
  const { intervalMs = 3000, timeoutMs = 180_000, onProgress } = options

  // Geocode first for accuracy
  const coords = await geocodeAddress(request.address)

  // Validate Bay Area address
  if (coords && !isInBayArea(coords.lat, coords.lon)) {
    throw new Error(
      'This address appears to be outside the Bay Area. SmartCanopy currently supports San Jose and surrounding cities served by Our City Forest.'
    )
  }

  const submission = await submitAnalysis({
    ...request,
    latitude: coords?.lat,
    longitude: coords?.lon,
  })

  const jobId = submission.job_id
  const deadline = Date.now() + timeoutMs

  while (Date.now() < deadline) {
    await new Promise((r) => setTimeout(r, intervalMs))
    const status = await pollJob(jobId)
    onProgress?.(status.message ?? `Status: ${status.status}`)

    if (status.status === 'complete') {
      if (!status.result) throw new Error('Job complete but result is missing')
      return status.result
    }
    if (status.status === 'error') {
      throw new Error(status.message ?? 'Analysis failed')
    }
  }

  throw new Error('Analysis timed out after 3 minutes — please try again')
}

/**
 * Get stored analysis results by analysis ID.
 */
export async function getAnalysis(analysisId: string): Promise<AnalysisResponse> {
  return apiClient<AnalysisResponse>(`/api/cv/analysis/${analysisId}`)
}

/**
 * Fetch recommended species for the Bay Area (default: hardiness zone 10).
 */
export async function fetchSpecies(params: {
  hardiness_zone?: number
  native_only?: boolean
  drought_tolerant?: boolean
  limit?: number
} = {}): Promise<SpeciesData[]> {
  const qs = new URLSearchParams()
  qs.set('hardiness_zone', String(params.hardiness_zone ?? 10))
  qs.set('limit', String(params.limit ?? 30))
  if (params.native_only) qs.set('native_only', 'true')
  if (params.drought_tolerant !== undefined) qs.set('drought_tolerant', String(params.drought_tolerant))
  return apiClient<SpeciesData[]>(`/api/species/search?${qs.toString()}`)
}
