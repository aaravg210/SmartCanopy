'use client'

import { useEffect, useRef } from 'react'
import mapboxgl from 'mapbox-gl'
import { useMapStore } from '@/stores/mapStore'
import { getNeighborhoodsForCity, neighborhoodsToGeoJSON, NEED_COLORS } from '@/data/mock/neighborhoods'
import type { NeighborhoodCell } from '@/types'

interface NeighborhoodPopupProps {
  name: string
  canopyPercentage: number
  heatIslandIndex: number
  needScore: number
}

function createNeighborhoodPopupHTML({
  name,
  canopyPercentage,
  heatIslandIndex,
  needScore,
}: NeighborhoodPopupProps): string {
  const needCategory = needScore >= 60 ? 'High Need' : needScore >= 40 ? 'Moderate' : 'Good'
  const needColor = needScore >= 60 ? NEED_COLORS.high : needScore >= 40 ? NEED_COLORS.medium : NEED_COLORS.low

  return `
    <div style="padding: 12px; min-width: 160px;">
      <div style="font-weight: 600; font-size: 14px; color: #1f2937; margin-bottom: 8px;">
        ${name}
      </div>
      <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 8px;">
        <div style="
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background-color: ${needColor};
        "></div>
        <span style="font-size: 12px; color: #6b7280;">${needCategory}</span>
      </div>
      <div style="display: grid; gap: 6px; font-size: 12px;">
        <div style="display: flex; justify-content: space-between;">
          <span style="color: #9ca3af;">Canopy</span>
          <span style="font-weight: 500; color: #374151;">${canopyPercentage.toFixed(1)}%</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
          <span style="color: #9ca3af;">Heat Index</span>
          <span style="font-weight: 500; color: #374151;">${heatIslandIndex.toFixed(0)}</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
          <span style="color: #9ca3af;">Need Score</span>
          <span style="font-weight: 500; color: #374151;">${needScore.toFixed(0)}/100</span>
        </div>
      </div>
    </div>
  `
}

interface NeighborhoodLayerProps {
  map: mapboxgl.Map
}

export default function NeighborhoodLayer({ map }: NeighborhoodLayerProps) {
  const popup = useRef<mapboxgl.Popup | null>(null)
  const hoveredCellId = useRef<string | null>(null)
  const {
    selectedCity,
    currentTier,
    selectNeighborhood,
    flyToNeighborhood,
  } = useMapStore()

  useEffect(() => {
    if (!map || !selectedCity) return

    const SOURCE_ID = 'neighborhoods'
    const FILL_LAYER_ID = 'neighborhoods-fill'
    const OUTLINE_LAYER_ID = 'neighborhoods-outline'
    const LABEL_LAYER_ID = 'neighborhoods-labels'

    // Get neighborhoods for selected city
    const neighborhoods = getNeighborhoodsForCity(selectedCity.id)
    const geojson = neighborhoodsToGeoJSON(neighborhoods)

    // Add or update source
    if (map.getSource(SOURCE_ID)) {
      (map.getSource(SOURCE_ID) as mapboxgl.GeoJSONSource).setData(geojson)
    } else {
      map.addSource(SOURCE_ID, {
        type: 'geojson',
        data: geojson,
      })

      // Add fill layer with color based on need score
      map.addLayer({
        id: FILL_LAYER_ID,
        type: 'fill',
        source: SOURCE_ID,
        paint: {
          'fill-color': [
            'case',
            ['>=', ['get', 'needScore'], 60],
            NEED_COLORS.high,
            ['>=', ['get', 'needScore'], 40],
            NEED_COLORS.medium,
            NEED_COLORS.low,
          ],
          'fill-opacity': [
            'interpolate',
            ['linear'],
            ['zoom'],
            10, 0.5,
            14, 0.3,
          ],
        },
      })

      // Add outline layer
      map.addLayer({
        id: OUTLINE_LAYER_ID,
        type: 'line',
        source: SOURCE_ID,
        paint: {
          'line-color': '#374151',
          'line-width': 1,
          'line-opacity': 0.5,
        },
      })

      // Add labels
      map.addLayer({
        id: LABEL_LAYER_ID,
        type: 'symbol',
        source: SOURCE_ID,
        layout: {
          'text-field': ['get', 'name'],
          'text-size': [
            'interpolate',
            ['linear'],
            ['zoom'],
            10, 10,
            13, 12,
          ],
        },
        paint: {
          'text-color': '#1f2937',
          'text-halo-color': '#ffffff',
          'text-halo-width': 1.5,
        },
      })
    }

    // Define event handlers outside the else block so they register every time
    const handleClick = (e: mapboxgl.MapLayerMouseEvent) => {
      if (e.features && e.features[0]) {
        const props = e.features[0].properties
        const neighborhood: NeighborhoodCell = {
          id: props?.id || '',
          cityId: props?.cityId || '',
          name: props?.name || '',
          geometry: (e.features[0].geometry as GeoJSON.Polygon),
          canopyPercentage: props?.canopyPercentage || 0,
          heatIslandIndex: props?.heatIslandIndex || 0,
          needScore: props?.needScore || 0,
          center: [props?.centerLng || 0, props?.centerLat || 0],
        }

        selectNeighborhood(neighborhood)
        flyToNeighborhood(neighborhood)
      }
    }

    // Use map-level mousemove with queryRenderedFeatures so that
    // label layers and popups can't interfere with hover detection
    const handleMouseMove = (e: mapboxgl.MapMouseEvent) => {
      const features = map.queryRenderedFeatures(e.point, { layers: [FILL_LAYER_ID] })

      if (features.length === 0) {
        // Cursor is not over any cell
        map.getCanvas().style.cursor = ''
        hoveredCellId.current = null
        if (popup.current) {
          popup.current.remove()
          popup.current = null
        }
        return
      }

      map.getCanvas().style.cursor = 'pointer'
      const props = features[0].properties
      const cellId = props?.id || ''

      // Skip if still hovering the same cell
      if (cellId === hoveredCellId.current) return

      hoveredCellId.current = cellId

      // Reuse existing popup to avoid remove/recreate flicker
      if (!popup.current) {
        popup.current = new mapboxgl.Popup({
          closeButton: false,
          closeOnClick: false,
          offset: 15,
          className: 'no-pointer-events',
        })
          .addTo(map)
      }

      // Update position and content in place
      popup.current
        .setLngLat([props?.centerLng || 0, props?.centerLat || 0])
        .setHTML(
          createNeighborhoodPopupHTML({
            name: props?.name || '',
            canopyPercentage: props?.canopyPercentage || 0,
            heatIslandIndex: props?.heatIslandIndex || 0,
            needScore: props?.needScore || 0,
          })
        )
    }

    // Register event handlers
    map.on('click', FILL_LAYER_ID, handleClick)
    map.on('mousemove', handleMouseMove)

    // Update visibility based on tier
    const isVisible = currentTier === 'neighborhood'
    map.setLayoutProperty(FILL_LAYER_ID, 'visibility', isVisible ? 'visible' : 'none')
    map.setLayoutProperty(OUTLINE_LAYER_ID, 'visibility', isVisible ? 'visible' : 'none')
    map.setLayoutProperty(LABEL_LAYER_ID, 'visibility', isVisible ? 'visible' : 'none')

    return () => {
      // Remove event handlers
      map.off('click', FILL_LAYER_ID, handleClick)
      map.off('mousemove', handleMouseMove)

      if (popup.current) {
        popup.current.remove()
      }
    }
  }, [map, selectedCity, currentTier, selectNeighborhood, flyToNeighborhood])

  return null
}
