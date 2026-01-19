'use client'

import { useEffect, useRef, useCallback, useState } from 'react'
import mapboxgl from 'mapbox-gl'
import { useMapStore } from '@/stores/mapStore'
import { useAnalysisStore } from '@/stores/analysisStore'
import { MAPBOX_CONFIG, getTierFromZoom, EQUITY_COLORS } from '@/lib/mapbox/config'
import { citiesToGeoJSON, getCityById } from '@/data/mock/cities'
import MapControls from './MapControls'
import CityPopup from './CityPopup'
import NeighborhoodLayer from './NeighborhoodLayer'
import StreetLayer from './StreetLayer'
import SidePanel from '../panels/SidePanel'
import Legend from './Legend'

// Set Mapbox token
mapboxgl.accessToken = process.env.NEXT_PUBLIC_MAPBOX_TOKEN || ''

export default function MapContainer() {
  const mapContainer = useRef<HTMLDivElement>(null)
  const map = useRef<mapboxgl.Map | null>(null)
  const popup = useRef<mapboxgl.Popup | null>(null)
  const [mapLoaded, setMapLoaded] = useState(false)

  const {
    setMapInstance,
    setViewState,
    currentTier,
    flyToCity,
    mapInstance,
    selectedCity,
  } = useMapStore()

  const { currentAnalysis, selectedSite } = useAnalysisStore()

  // Handle city click
  const handleCityClick = useCallback((cityId: string) => {
    const city = getCityById(cityId)
    if (city) {
      flyToCity(city)
    }
  }, [flyToCity])

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return

    // Check for Mapbox token
    if (!mapboxgl.accessToken) {
      console.error('Mapbox token not found. Set NEXT_PUBLIC_MAPBOX_TOKEN in .env.local')
      return
    }

    // Create map instance
    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: MAPBOX_CONFIG.style,
      center: MAPBOX_CONFIG.initialView.center,
      zoom: MAPBOX_CONFIG.initialView.zoom,
    })

    const mapInstance = map.current

    // Add navigation controls
    mapInstance.addControl(new mapboxgl.NavigationControl(), 'top-right')

    // Track view state changes
    mapInstance.on('moveend', () => {
      const center = mapInstance.getCenter()
      const zoom = mapInstance.getZoom()
      setViewState({
        center: [center.lng, center.lat],
        zoom,
      })
    })

    // Add city layer on load
    mapInstance.on('load', () => {
      // Add cities source
      mapInstance.addSource('cities', {
        type: 'geojson',
        data: citiesToGeoJSON(),
      })

      // Add city circles layer
      mapInstance.addLayer({
        id: 'cities-circles',
        type: 'circle',
        source: 'cities',
        paint: {
          // Size based on zoom
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['zoom'],
            3, 6,
            6, 12,
            9, 20,
          ],
          // Color based on canopy percentage
          'circle-color': [
            'case',
            ['<', ['get', 'canopyPercentage'], 15],
            EQUITY_COLORS.critical,
            ['<', ['get', 'canopyPercentage'], 25],
            EQUITY_COLORS.low,
            EQUITY_COLORS.healthy,
          ],
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff',
          'circle-opacity': 0.9,
        },
      })

      // Add city labels
      mapInstance.addLayer({
        id: 'cities-labels',
        type: 'symbol',
        source: 'cities',
        layout: {
          'text-field': ['get', 'name'],
          'text-size': [
            'interpolate',
            ['linear'],
            ['zoom'],
            3, 10,
            6, 12,
            9, 14,
          ],
          'text-offset': [0, 1.5],
          'text-anchor': 'top',
        },
        paint: {
          'text-color': '#374151',
          'text-halo-color': '#ffffff',
          'text-halo-width': 1,
        },
      })

      // City click handler
      mapInstance.on('click', 'cities-circles', (e) => {
        if (e.features && e.features[0]) {
          const cityId = e.features[0].properties?.id
          if (cityId) {
            handleCityClick(cityId)
          }
        }
      })

      // City hover - show popup
      mapInstance.on('mouseenter', 'cities-circles', (e) => {
        mapInstance.getCanvas().style.cursor = 'pointer'

        if (e.features && e.features[0]) {
          const props = e.features[0].properties
          const coordinates = (e.features[0].geometry as GeoJSON.Point).coordinates.slice() as [number, number]

          // Create popup content
          const content = CityPopup({
            name: props?.name || '',
            state: props?.state || '',
            canopyPercentage: props?.canopyPercentage || 0,
            treeEquityScore: props?.treeEquityScore || 0,
            population: props?.population || 0,
          })

          // Remove existing popup
          if (popup.current) {
            popup.current.remove()
          }

          // Create new popup
          popup.current = new mapboxgl.Popup({
            closeButton: false,
            closeOnClick: false,
            offset: 15,
          })
            .setLngLat(coordinates)
            .setHTML(content)
            .addTo(mapInstance)
        }
      })

      // City hover out - hide popup
      mapInstance.on('mouseleave', 'cities-circles', () => {
        mapInstance.getCanvas().style.cursor = ''
        if (popup.current) {
          popup.current.remove()
          popup.current = null
        }
      })

      // Update layer visibility based on zoom
      mapInstance.on('zoom', () => {
        const zoom = mapInstance.getZoom()
        const tier = getTierFromZoom(zoom)

        // Show city layer only at city zoom levels
        const cityVisibility = tier === 'city' ? 'visible' : 'none'
        mapInstance.setLayoutProperty('cities-circles', 'visibility', cityVisibility)
        mapInstance.setLayoutProperty('cities-labels', 'visibility', cityVisibility)
      })

      // Store map instance and mark as loaded
      setMapInstance(mapInstance)
      setMapLoaded(true)
    })

    // Cleanup
    return () => {
      if (popup.current) {
        popup.current.remove()
      }
      mapInstance.remove()
      map.current = null
      setMapInstance(null)
    }
  }, [setMapInstance, setViewState, handleCityClick])

  return (
    <div className="relative w-full h-full">
      {/* Map container */}
      <div ref={mapContainer} className="map-container" />

      {/* Neighborhood layer - rendered when map is loaded and city selected */}
      {mapLoaded && mapInstance && selectedCity && (
        <NeighborhoodLayer map={mapInstance} />
      )}

      {/* Street layer - rendered when map is loaded */}
      {mapLoaded && mapInstance && (
        <StreetLayer map={mapInstance} />
      )}

      {/* Map controls overlay */}
      <MapControls />

      {/* Legend */}
      <Legend />

      {/* Side panel for site details */}
      <SidePanel />
    </div>
  )
}
