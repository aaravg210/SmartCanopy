/**
 * Mapbox configuration
 */

export const MAPBOX_CONFIG = {
  // Map style - using streets for good city/neighborhood context
  style: 'mapbox://styles/mapbox/streets-v12',

  // Initial view centered on San Jose / Bay Area (OCF service area)
  initialView: {
    center: [-121.89, 37.33] as [number, number],
    zoom: 12,
  },

  // Zoom level thresholds for tier transitions
  zoomLevels: {
    city: { min: 3, max: 9 },        // Tier 1: City level
    neighborhood: { min: 10, max: 14 }, // Tier 2: Neighborhood level
    street: { min: 15, max: 20 },    // Tier 3: Street level
  },

  // Transition settings
  flyTo: {
    duration: 1500, // ms
    essential: true,
  },
}

// Color scales for tree equity
export const EQUITY_COLORS = {
  critical: '#ef4444', // RED - <15% canopy
  low: '#f97316',      // ORANGE - 15-25% canopy
  healthy: '#22c55e',  // GREEN - >25% canopy
}

// Colors for planting sites
export const SITE_COLORS = {
  recommended: '#3b82f6', // Blue
  existing: '#22c55e',    // Green
  selected: '#8b5cf6',    // Purple
}

// Priority colors
export const PRIORITY_COLORS = {
  high: '#22c55e',   // Green - high suitability
  medium: '#f59e0b', // Amber - medium
  low: '#6b7280',    // Gray - low
}

// Get tier from zoom level
export function getTierFromZoom(zoom: number): 'city' | 'neighborhood' | 'street' {
  const { zoomLevels } = MAPBOX_CONFIG

  if (zoom < zoomLevels.neighborhood.min) {
    return 'city'
  } else if (zoom < zoomLevels.street.min) {
    return 'neighborhood'
  }
  return 'street'
}
