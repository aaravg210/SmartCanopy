'use client'

import { useEffect, useRef } from 'react'
import mapboxgl from 'mapbox-gl'
import { useMapStore } from '@/stores/mapStore'
import { useAnalysisStore } from '@/stores/analysisStore'
import { SITE_COLORS } from '@/lib/mapbox/config'
import { getPriorityNumber } from '@/types'

interface SitePopupProps {
  siteId: string
  suitabilityScore: number
  ndviCategory: string
  slopeCategory: string
  hasNearbyRoads: boolean
  hasNearbyBuildings: boolean
  isClickPopup?: boolean
}

function createSitePopupHTML(props: SitePopupProps): string {
  const priority = getPriorityNumber(props.suitabilityScore)
  const priorityColor = priority >= 7 ? '#22c55e' : priority >= 4 ? '#f59e0b' : '#6b7280'

  return `
    <div style="padding: 12px; min-width: 180px;">
      <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
        <div style="
          width: 28px;
          height: 28px;
          border-radius: 50%;
          background-color: ${priorityColor};
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
          font-size: 14px;
        ">${priority}</div>
        <div>
          <div style="font-weight: 600; font-size: 14px; color: #1f2937;">
            Priority ${priority >= 7 ? 'High' : priority >= 4 ? 'Medium' : 'Low'}
          </div>
          <div style="font-size: 11px; color: #6b7280;">
            Score: ${(props.suitabilityScore * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      <div style="display: grid; gap: 4px; font-size: 12px; margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between;">
          <span style="color: #9ca3af;">Vegetation</span>
          <span style="color: #374151; text-transform: capitalize;">
            ${props.ndviCategory.replace(/_/g, ' ')}
          </span>
        </div>
        <div style="display: flex; justify-content: space-between;">
          <span style="color: #9ca3af;">Terrain</span>
          <span style="color: #374151; text-transform: capitalize;">${props.slopeCategory}</span>
        </div>
      </div>

      ${(props.hasNearbyRoads || props.hasNearbyBuildings) ? `
        <div style="
          background-color: #fef3c7;
          border-radius: 4px;
          padding: 6px 8px;
          font-size: 11px;
          color: #92400e;
          margin-bottom: 8px;
        ">
          ⚠️ Near ${[
            props.hasNearbyRoads ? 'roads' : '',
            props.hasNearbyBuildings ? 'buildings' : '',
          ].filter(Boolean).join(' & ')}
        </div>
      ` : ''}

      ${props.isClickPopup ? `
        <button
          class="ask-smartcanopy-ai-btn"
          data-site-id="${props.siteId}"
          style="
            width: 100%;
            padding: 10px 12px;
            background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            font-size: 13px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            margin-top: 8px;
            transition: transform 0.1s, box-shadow 0.1s;
          "
          onmouseover="this.style.transform='scale(1.02)'; this.style.boxShadow='0 4px 12px rgba(34,197,94,0.4)';"
          onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='none';"
        >
          <span style="font-size: 16px;">🌳</span>
          Ask SmartCanopy AI
        </button>
      ` : `
        <div style="
          font-size: 11px;
          color: #6b7280;
          padding-top: 8px;
          border-top: 1px solid #e5e7eb;
        ">
          Click for details & recommendations
        </div>
      `}
    </div>
  `
}

interface StreetLayerProps {
  map: mapboxgl.Map
  onAskAI?: (siteId: string) => void
}

export default function StreetLayer({ map, onAskAI }: StreetLayerProps) {
  const hoverPopup = useRef<mapboxgl.Popup | null>(null)
  const clickPopup = useRef<mapboxgl.Popup | null>(null)
  const { currentTier } = useMapStore()
  const { currentAnalysis, selectSite } = useAnalysisStore()

  useEffect(() => {
    if (!map) return

    // Planting sites layer IDs
    const SOURCE_ID = 'planting-sites'
    const SITES_LAYER_ID = 'planting-sites-circles'
    const LABELS_LAYER_ID = 'planting-sites-labels'

    // Existing trees layer IDs
    const TREES_SOURCE_ID = 'existing-trees'
    const TREES_LAYER_ID = 'existing-trees-circles'

    // Create GeoJSON for planting sites (recommended - blue dots)
    const createSitesGeoJSON = (): GeoJSON.FeatureCollection => {
      if (!currentAnalysis?.planting_sites) {
        return { type: 'FeatureCollection', features: [] }
      }

      return {
        type: 'FeatureCollection',
        features: currentAnalysis.planting_sites.map((site) => ({
          type: 'Feature' as const,
          id: site.site_id,
          geometry: {
            type: 'Point' as const,
            coordinates: [site.location_lon, site.location_lat],
          },
          properties: {
            site_id: site.site_id,
            suitability_score: site.suitability_score,
            priority: getPriorityNumber(site.suitability_score),
            avg_ndvi: site.avg_ndvi,
            ndvi_category: site.ndvi_category,
            avg_slope: site.avg_slope,
            slope_category: site.slope_category,
            area_sq_ft: site.area_sq_ft,
            has_nearby_roads: site.has_nearby_roads,
            has_nearby_buildings: site.has_nearby_buildings,
          },
        })),
      }
    }

    // Create GeoJSON for existing trees (green dots)
    const createTreesGeoJSON = (): GeoJSON.FeatureCollection => {
      if (!currentAnalysis?.existing_trees) {
        return { type: 'FeatureCollection', features: [] }
      }

      return {
        type: 'FeatureCollection',
        features: currentAnalysis.existing_trees.map((tree, index) => ({
          type: 'Feature' as const,
          id: `tree-${index}`,
          geometry: {
            type: 'Point' as const,
            coordinates: [tree.lon, tree.lat],
          },
          properties: {
            confidence: tree.confidence,
            bbox_width: tree.bbox_width,
            bbox_height: tree.bbox_height,
          },
        })),
      }
    }

    // Add or update planting sites source
    if (map.getSource(SOURCE_ID)) {
      (map.getSource(SOURCE_ID) as mapboxgl.GeoJSONSource).setData(createSitesGeoJSON())
    } else {
      map.addSource(SOURCE_ID, {
        type: 'geojson',
        data: createSitesGeoJSON(),
      })

      // Add planting sites circles layer (blue dots)
      map.addLayer({
        id: SITES_LAYER_ID,
        type: 'circle',
        source: SOURCE_ID,
        paint: {
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['zoom'],
            15, 8,
            18, 14,
            20, 20,
          ],
          'circle-color': SITE_COLORS.recommended,
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff',
          'circle-opacity': 0.9,
        },
      })

      // Add priority labels
      map.addLayer({
        id: LABELS_LAYER_ID,
        type: 'symbol',
        source: SOURCE_ID,
        layout: {
          'text-field': ['get', 'priority'],
          'text-size': [
            'interpolate',
            ['linear'],
            ['zoom'],
            15, 10,
            18, 14,
          ],
          'text-allow-overlap': true,
        },
        paint: {
          'text-color': '#ffffff',
        },
      })
    }

    // Add or update existing trees source
    if (map.getSource(TREES_SOURCE_ID)) {
      (map.getSource(TREES_SOURCE_ID) as mapboxgl.GeoJSONSource).setData(createTreesGeoJSON())
    } else {
      map.addSource(TREES_SOURCE_ID, {
        type: 'geojson',
        data: createTreesGeoJSON(),
      })

      // Add existing trees circles layer (green dots)
      map.addLayer({
        id: TREES_LAYER_ID,
        type: 'circle',
        source: TREES_SOURCE_ID,
        paint: {
          'circle-radius': [
            'interpolate',
            ['linear'],
            ['zoom'],
            15, 6,
            18, 10,
            20, 14,
          ],
          'circle-color': SITE_COLORS.existing,
          'circle-stroke-width': 1,
          'circle-stroke-color': '#ffffff',
          'circle-opacity': 0.8,
        },
      })
    }

    // Define event handlers (these need to be registered fresh each time)
    const handleTreesMouseEnter = (e: mapboxgl.MapLayerMouseEvent) => {
      map.getCanvas().style.cursor = 'pointer'

      if (e.features && e.features[0]) {
        const props = e.features[0].properties
        const coordinates = (e.features[0].geometry as GeoJSON.Point).coordinates.slice() as [number, number]

        if (hoverPopup.current) {
          hoverPopup.current.remove()
        }

        const confidence = props?.confidence ? (props.confidence * 100).toFixed(0) : 'N/A'
        hoverPopup.current = new mapboxgl.Popup({
          closeButton: false,
          closeOnClick: false,
          offset: 10,
        })
          .setLngLat(coordinates)
          .setHTML(`
            <div style="padding: 8px; min-width: 120px;">
              <div style="font-weight: 600; font-size: 13px; color: #22c55e; margin-bottom: 4px;">
                🌳 Existing Tree
              </div>
              <div style="font-size: 12px; color: #6b7280;">
                Confidence: ${confidence}%
              </div>
            </div>
          `)
          .addTo(map)
      }
    }

    const handleTreesMouseLeave = () => {
      map.getCanvas().style.cursor = ''
      if (hoverPopup.current) {
        hoverPopup.current.remove()
        hoverPopup.current = null
      }
    }

    // Click handler - show popup with "Ask SmartCanopy AI" button
    const handleSitesClick = (e: mapboxgl.MapLayerMouseEvent) => {
      if (e.features && e.features[0]) {
        const props = e.features[0].properties
        const coordinates = (e.features[0].geometry as GeoJSON.Point).coordinates.slice() as [number, number]
        const site = currentAnalysis?.planting_sites.find(
          (s) => s.site_id === props?.site_id
        )

        if (site) {
          // Remove hover popup
          if (hoverPopup.current) {
            hoverPopup.current.remove()
            hoverPopup.current = null
          }

          // Remove existing click popup
          if (clickPopup.current) {
            clickPopup.current.remove()
          }

          // Select the site for context
          selectSite(site)

          // Create click popup with "Ask SmartCanopy AI" button
          clickPopup.current = new mapboxgl.Popup({
            closeButton: true,
            closeOnClick: false,
            offset: 15,
            maxWidth: '280px',
          })
            .setLngLat(coordinates)
            .setHTML(
              createSitePopupHTML({
                siteId: props?.site_id || '',
                suitabilityScore: props?.suitability_score || 0,
                ndviCategory: props?.ndvi_category || '',
                slopeCategory: props?.slope_category || '',
                hasNearbyRoads: props?.has_nearby_roads || false,
                hasNearbyBuildings: props?.has_nearby_buildings || false,
                isClickPopup: true,
              })
            )
            .addTo(map)
        }
      }
    }

    // Hover handler for planting sites
    const handleSitesMouseEnter = (e: mapboxgl.MapLayerMouseEvent) => {
      map.getCanvas().style.cursor = 'pointer'

      // Don't show hover popup if click popup is open
      if (clickPopup.current) return

      if (e.features && e.features[0]) {
        const props = e.features[0].properties
        const coordinates = (e.features[0].geometry as GeoJSON.Point).coordinates.slice() as [number, number]

        // Remove existing hover popup
        if (hoverPopup.current) {
          hoverPopup.current.remove()
        }

        hoverPopup.current = new mapboxgl.Popup({
          closeButton: false,
          closeOnClick: false,
          offset: 15,
        })
          .setLngLat(coordinates)
          .setHTML(
            createSitePopupHTML({
              siteId: props?.site_id || '',
              suitabilityScore: props?.suitability_score || 0,
              ndviCategory: props?.ndvi_category || '',
              slopeCategory: props?.slope_category || '',
              hasNearbyRoads: props?.has_nearby_roads || false,
              hasNearbyBuildings: props?.has_nearby_buildings || false,
              isClickPopup: false,
            })
          )
          .addTo(map)
      }
    }

    const handleSitesMouseLeave = () => {
      map.getCanvas().style.cursor = ''
      if (hoverPopup.current) {
        hoverPopup.current.remove()
        hoverPopup.current = null
      }
    }

    // Register event handlers
    map.on('mouseenter', TREES_LAYER_ID, handleTreesMouseEnter)
    map.on('mouseleave', TREES_LAYER_ID, handleTreesMouseLeave)
    map.on('click', SITES_LAYER_ID, handleSitesClick)
    map.on('mouseenter', SITES_LAYER_ID, handleSitesMouseEnter)
    map.on('mouseleave', SITES_LAYER_ID, handleSitesMouseLeave)

    // Update visibility based on tier and data availability
    const hasSitesData = currentAnalysis?.planting_sites && currentAnalysis.planting_sites.length > 0
    const hasTreesData = currentAnalysis?.existing_trees && currentAnalysis.existing_trees.length > 0
    const isStreetTier = currentTier === 'street'

    // Planting sites visibility (blue dots)
    if (map.getLayer(SITES_LAYER_ID)) {
      map.setLayoutProperty(SITES_LAYER_ID, 'visibility', isStreetTier && hasSitesData ? 'visible' : 'none')
    }
    if (map.getLayer(LABELS_LAYER_ID)) {
      map.setLayoutProperty(LABELS_LAYER_ID, 'visibility', isStreetTier && hasSitesData ? 'visible' : 'none')
    }

    // Existing trees visibility (green dots)
    if (map.getLayer(TREES_LAYER_ID)) {
      map.setLayoutProperty(TREES_LAYER_ID, 'visibility', isStreetTier && hasTreesData ? 'visible' : 'none')
    }

    return () => {
      // Remove event handlers
      map.off('mouseenter', TREES_LAYER_ID, handleTreesMouseEnter)
      map.off('mouseleave', TREES_LAYER_ID, handleTreesMouseLeave)
      map.off('click', SITES_LAYER_ID, handleSitesClick)
      map.off('mouseenter', SITES_LAYER_ID, handleSitesMouseEnter)
      map.off('mouseleave', SITES_LAYER_ID, handleSitesMouseLeave)

      if (hoverPopup.current) {
        hoverPopup.current.remove()
      }
      if (clickPopup.current) {
        clickPopup.current.remove()
      }
    }
  }, [map, currentAnalysis, currentTier, selectSite])

  // Event listener for "Ask SmartCanopy AI" button clicks
  useEffect(() => {
    const handleAskAIClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      if (target.classList.contains('ask-smartcanopy-ai-btn')) {
        const siteId = target.dataset.siteId
        if (siteId && onAskAI) {
          // Close the popup
          if (clickPopup.current) {
            clickPopup.current.remove()
            clickPopup.current = null
          }
          onAskAI(siteId)
        }
      }
    }

    document.addEventListener('click', handleAskAIClick)
    return () => {
      document.removeEventListener('click', handleAskAIClick)
    }
  }, [onAskAI])

  return null
}
