import type { CityData } from '@/types'

/**
 * Mock city data for Tier 1 visualization
 * Canopy percentages based on approximate real-world data
 * Tree equity scores are illustrative
 */
export const MOCK_CITIES: CityData[] = [
  // Critical need (RED) - <15% canopy
  {
    id: 'phx',
    name: 'Phoenix',
    state: 'AZ',
    coordinates: [-112.074, 33.4484],
    bounds: [[-112.4, 33.2], [-111.7, 33.7]],
    canopyPercentage: 9.4,
    population: 1608139,
    treeEquityScore: 42,
  },
  {
    id: 'lv',
    name: 'Las Vegas',
    state: 'NV',
    coordinates: [-115.1398, 36.1699],
    bounds: [[-115.4, 35.9], [-114.8, 36.4]],
    canopyPercentage: 8.2,
    population: 641903,
    treeEquityScore: 38,
  },
  {
    id: 'la',
    name: 'Los Angeles',
    state: 'CA',
    coordinates: [-118.2437, 34.0522],
    bounds: [[-118.7, 33.7], [-117.8, 34.4]],
    canopyPercentage: 12.1,
    population: 3898747,
    treeEquityScore: 52,
  },
  {
    id: 'mia',
    name: 'Miami',
    state: 'FL',
    coordinates: [-80.1918, 25.7617],
    bounds: [[-80.5, 25.5], [-79.9, 26.0]],
    canopyPercentage: 11.5,
    population: 442241,
    treeEquityScore: 48,
  },

  // Below target (ORANGE) - 15-25% canopy
  {
    id: 'sf',
    name: 'San Francisco',
    state: 'CA',
    coordinates: [-122.4194, 37.7749],
    bounds: [[-122.52, 37.7], [-122.35, 37.82]],
    canopyPercentage: 17.8,
    population: 874961,
    treeEquityScore: 58,
  },
  {
    id: 'sj',
    name: 'San Jose',
    state: 'CA',
    coordinates: [-121.8863, 37.3382],
    bounds: [[-122.05, 37.2], [-121.7, 37.45]],
    canopyPercentage: 15.2,
    population: 1013240,
    treeEquityScore: 56,
  },
  {
    id: 'chi',
    name: 'Chicago',
    state: 'IL',
    coordinates: [-87.6298, 41.8781],
    bounds: [[-87.94, 41.64], [-87.52, 42.02]],
    canopyPercentage: 18.4,
    population: 2746388,
    treeEquityScore: 62,
  },
  {
    id: 'nyc',
    name: 'New York',
    state: 'NY',
    coordinates: [-74.006, 40.7128],
    bounds: [[-74.26, 40.49], [-73.7, 40.92]],
    canopyPercentage: 21.0,
    population: 8336817,
    treeEquityScore: 65,
  },
  {
    id: 'hou',
    name: 'Houston',
    state: 'TX',
    coordinates: [-95.3698, 29.7604],
    bounds: [[-95.8, 29.5], [-95.0, 30.1]],
    canopyPercentage: 22.3,
    population: 2304580,
    treeEquityScore: 60,
  },
  {
    id: 'dal',
    name: 'Dallas',
    state: 'TX',
    coordinates: [-96.797, 32.7767],
    bounds: [[-97.0, 32.6], [-96.5, 33.0]],
    canopyPercentage: 24.5,
    population: 1304379,
    treeEquityScore: 64,
  },

  // Healthy (GREEN) - >25% canopy
  {
    id: 'atl',
    name: 'Atlanta',
    state: 'GA',
    coordinates: [-84.388, 33.749],
    bounds: [[-84.6, 33.6], [-84.2, 33.9]],
    canopyPercentage: 47.9,
    population: 498715,
    treeEquityScore: 78,
  },
  {
    id: 'pdx',
    name: 'Portland',
    state: 'OR',
    coordinates: [-122.6765, 45.5051],
    bounds: [[-122.9, 45.4], [-122.4, 45.65]],
    canopyPercentage: 30.2,
    population: 652503,
    treeEquityScore: 75,
  },
  {
    id: 'sea',
    name: 'Seattle',
    state: 'WA',
    coordinates: [-122.3321, 47.6062],
    bounds: [[-122.5, 47.48], [-122.2, 47.74]],
    canopyPercentage: 28.1,
    population: 749256,
    treeEquityScore: 72,
  },
  {
    id: 'aus',
    name: 'Austin',
    state: 'TX',
    coordinates: [-97.7431, 30.2672],
    bounds: [[-98.0, 30.1], [-97.5, 30.5]],
    canopyPercentage: 31.0,
    population: 978908,
    treeEquityScore: 74,
  },
  {
    id: 'min',
    name: 'Minneapolis',
    state: 'MN',
    coordinates: [-93.265, 44.9778],
    bounds: [[-93.4, 44.88], [-93.1, 45.08]],
    canopyPercentage: 26.4,
    population: 429954,
    treeEquityScore: 70,
  },
]

// Convert cities to GeoJSON for Mapbox
export function citiesToGeoJSON(): GeoJSON.FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: MOCK_CITIES.map((city) => ({
      type: 'Feature' as const,
      id: city.id,
      geometry: {
        type: 'Point' as const,
        coordinates: city.coordinates,
      },
      properties: {
        id: city.id,
        name: city.name,
        state: city.state,
        canopyPercentage: city.canopyPercentage,
        population: city.population,
        treeEquityScore: city.treeEquityScore,
      },
    })),
  }
}

// Get city by ID
export function getCityById(id: string): CityData | undefined {
  return MOCK_CITIES.find((city) => city.id === id)
}
