import type { NeighborhoodCell, CityData } from '@/types'
import { MOCK_CITIES } from './cities'

/**
 * Generate mock neighborhood grid for a city
 * Creates a 5x5 grid of cells with varying coverage and heat data
 */
function generateNeighborhoodGrid(city: CityData): NeighborhoodCell[] {
  const cells: NeighborhoodCell[] = []
  const gridSize = 5

  const [sw_lng, sw_lat] = city.bounds[0]
  const [ne_lng, ne_lat] = city.bounds[1]

  const lngStep = (ne_lng - sw_lng) / gridSize
  const latStep = (ne_lat - sw_lat) / gridSize

  // Neighborhood names for variety
  const neighborhoodNames = [
    'Downtown', 'Midtown', 'Uptown', 'Westside', 'Eastside',
    'North End', 'South End', 'Central', 'Heights', 'Gardens',
    'Park District', 'River District', 'Old Town', 'Tech Hub', 'Arts District',
    'University Area', 'Financial District', 'Historic Quarter', 'Marina', 'Suburbs',
    'Industrial Zone', 'Commercial Center', 'Residential Area', 'Green Belt', 'Transit Hub',
  ]

  // Seed random based on city for consistent results
  const seed = city.id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  const seededRandom = (index: number) => {
    const x = Math.sin(seed + index) * 10000
    return x - Math.floor(x)
  }

  let cellIndex = 0
  for (let i = 0; i < gridSize; i++) {
    for (let j = 0; j < gridSize; j++) {
      const cellLng = sw_lng + lngStep * i
      const cellLat = sw_lat + latStep * j

      // Generate pseudo-random but consistent values
      const rand1 = seededRandom(cellIndex)
      const rand2 = seededRandom(cellIndex + 100)

      // Canopy percentage varies around city average
      const canopyVariance = (rand1 - 0.5) * 30
      const canopy = Math.max(5, Math.min(60, city.canopyPercentage + canopyVariance))

      // Heat island index - inversely related to canopy, with some noise
      const baseHeat = 100 - canopy * 1.5
      const heatVariance = (rand2 - 0.5) * 20
      const heat = Math.max(10, Math.min(90, baseHeat + heatVariance))

      // Need score: combination of low canopy and high heat
      const needScore = ((100 - canopy) * 0.6 + heat * 0.4)

      cells.push({
        id: `${city.id}-${i}-${j}`,
        cityId: city.id,
        name: neighborhoodNames[cellIndex % neighborhoodNames.length],
        geometry: {
          type: 'Polygon',
          coordinates: [[
            [cellLng, cellLat],
            [cellLng + lngStep, cellLat],
            [cellLng + lngStep, cellLat + latStep],
            [cellLng, cellLat + latStep],
            [cellLng, cellLat], // Close the polygon
          ]],
        },
        canopyPercentage: Math.round(canopy * 10) / 10,
        heatIslandIndex: Math.round(heat * 10) / 10,
        needScore: Math.round(needScore * 10) / 10,
        center: [cellLng + lngStep / 2, cellLat + latStep / 2],
      })

      cellIndex++
    }
  }

  return cells
}

// Cache generated neighborhoods
const neighborhoodCache: Map<string, NeighborhoodCell[]> = new Map()

/**
 * Get neighborhoods for a city (generated on demand and cached)
 */
export function getNeighborhoodsForCity(cityId: string): NeighborhoodCell[] {
  // Check cache first
  if (neighborhoodCache.has(cityId)) {
    return neighborhoodCache.get(cityId)!
  }

  // Find city
  const city = MOCK_CITIES.find((c) => c.id === cityId)
  if (!city) {
    return []
  }

  // Generate and cache
  const neighborhoods = generateNeighborhoodGrid(city)
  neighborhoodCache.set(cityId, neighborhoods)

  return neighborhoods
}

/**
 * Convert neighborhoods to GeoJSON for Mapbox
 */
export function neighborhoodsToGeoJSON(neighborhoods: NeighborhoodCell[]): GeoJSON.FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: neighborhoods.map((n) => ({
      type: 'Feature' as const,
      id: n.id,
      geometry: n.geometry,
      properties: {
        id: n.id,
        cityId: n.cityId,
        name: n.name,
        canopyPercentage: n.canopyPercentage,
        heatIslandIndex: n.heatIslandIndex,
        needScore: n.needScore,
        centerLng: n.center[0],
        centerLat: n.center[1],
      },
    })),
  }
}

/**
 * Get need category for coloring
 */
export function getNeedCategory(needScore: number): 'high' | 'medium' | 'low' {
  if (needScore >= 60) return 'high'
  if (needScore >= 40) return 'medium'
  return 'low'
}

// Colors for need levels
export const NEED_COLORS = {
  high: '#ef4444',   // Red - high need
  medium: '#f59e0b', // Amber - medium need
  low: '#22c55e',    // Green - low need
}
