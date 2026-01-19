import { create } from 'zustand'
import type { MapTier, CityData, NeighborhoodCell, ViewState } from '@/types'
import { MAPBOX_CONFIG, getTierFromZoom } from '@/lib/mapbox/config'

interface MapState {
  // Current map state
  currentTier: MapTier
  viewState: ViewState

  // Selected items
  selectedCity: CityData | null
  selectedNeighborhood: NeighborhoodCell | null

  // Map instance reference (set by MapContainer)
  mapInstance: mapboxgl.Map | null

  // Actions
  setMapInstance: (map: mapboxgl.Map | null) => void
  setViewState: (viewState: ViewState) => void
  setTier: (tier: MapTier) => void
  selectCity: (city: CityData | null) => void
  selectNeighborhood: (neighborhood: NeighborhoodCell | null) => void

  // Navigation
  flyToCity: (city: CityData) => void
  flyToNeighborhood: (neighborhood: NeighborhoodCell) => void
  flyToCoordinates: (center: [number, number], zoom: number) => void
  resetView: () => void
}

export const useMapStore = create<MapState>((set, get) => ({
  // Initial state
  currentTier: 'city',
  viewState: {
    center: MAPBOX_CONFIG.initialView.center,
    zoom: MAPBOX_CONFIG.initialView.zoom,
  },
  selectedCity: null,
  selectedNeighborhood: null,
  mapInstance: null,

  // Actions
  setMapInstance: (map) => set({ mapInstance: map }),

  setViewState: (viewState) => {
    const tier = getTierFromZoom(viewState.zoom)
    set({ viewState, currentTier: tier })
  },

  setTier: (tier) => set({ currentTier: tier }),

  selectCity: (city) => set({ selectedCity: city }),

  selectNeighborhood: (neighborhood) => set({ selectedNeighborhood: neighborhood }),

  // Navigation
  flyToCity: (city) => {
    const { mapInstance } = get()
    if (!mapInstance) return

    set({ selectedCity: city, selectedNeighborhood: null })

    mapInstance.flyTo({
      center: city.coordinates,
      zoom: 11, // Neighborhood level
      duration: MAPBOX_CONFIG.flyTo.duration,
      essential: MAPBOX_CONFIG.flyTo.essential,
    })
  },

  flyToNeighborhood: (neighborhood) => {
    const { mapInstance } = get()
    if (!mapInstance) return

    set({ selectedNeighborhood: neighborhood })

    mapInstance.flyTo({
      center: neighborhood.center,
      zoom: 16, // Street level
      duration: MAPBOX_CONFIG.flyTo.duration,
      essential: MAPBOX_CONFIG.flyTo.essential,
    })
  },

  flyToCoordinates: (center, zoom) => {
    const { mapInstance } = get()
    if (!mapInstance) return

    mapInstance.flyTo({
      center,
      zoom,
      duration: MAPBOX_CONFIG.flyTo.duration,
      essential: MAPBOX_CONFIG.flyTo.essential,
    })
  },

  resetView: () => {
    const { mapInstance } = get()
    if (!mapInstance) return

    set({
      selectedCity: null,
      selectedNeighborhood: null,
    })

    mapInstance.flyTo({
      center: MAPBOX_CONFIG.initialView.center,
      zoom: MAPBOX_CONFIG.initialView.zoom,
      duration: MAPBOX_CONFIG.flyTo.duration,
      essential: MAPBOX_CONFIG.flyTo.essential,
    })
  },
}))
