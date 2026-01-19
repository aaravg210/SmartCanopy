'use client'

import type { PlantingSiteResponse } from '@/types'
import { getPriorityNumber, getPriorityLevel } from '@/types'

interface SiteDetailPanelProps {
  site: PlantingSiteResponse
  analysisAddress?: string
  onOpenChat?: (initialMessage?: string) => void
}

export default function SiteDetailPanel({ site, analysisAddress, onOpenChat }: SiteDetailPanelProps) {

  const priority = getPriorityNumber(site.suitability_score)
  const priorityLevel = getPriorityLevel(site.suitability_score)

  const priorityColors = {
    high: { bg: 'bg-green-100', text: 'text-green-800', ring: 'ring-green-500' },
    medium: { bg: 'bg-amber-100', text: 'text-amber-800', ring: 'ring-amber-500' },
    low: { bg: 'bg-gray-100', text: 'text-gray-800', ring: 'ring-gray-500' },
  }

  const colors = priorityColors[priorityLevel]

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-start gap-4">
          <div
            className={`w-14 h-14 rounded-full ${colors.bg} ${colors.text} flex items-center justify-center font-bold text-xl ring-2 ${colors.ring}`}
          >
            {priority}
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Planting Site
            </h2>
            <p className="text-sm text-gray-500">
              Priority: {priorityLevel.charAt(0).toUpperCase() + priorityLevel.slice(1)}
            </p>
            {analysisAddress && (
              <p className="text-xs text-gray-400 mt-1">{analysisAddress}</p>
            )}
          </div>
        </div>
      </div>

      {/* Suitability Score Bar */}
      <div className="mb-6">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-600">Suitability Score</span>
          <span className="font-medium text-gray-900">
            {(site.suitability_score * 100).toFixed(0)}%
          </span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              priorityLevel === 'high'
                ? 'bg-green-500'
                : priorityLevel === 'medium'
                  ? 'bg-amber-500'
                  : 'bg-gray-500'
            }`}
            style={{ width: `${site.suitability_score * 100}%` }}
          />
        </div>
      </div>

      {/* Site Characteristics */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Site Characteristics
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs text-gray-500 mb-1">Vegetation</div>
            <div className="font-medium text-gray-900 text-sm capitalize">
              {site.ndvi_category.replace(/_/g, ' ')}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              NDVI: {site.avg_ndvi.toFixed(2)}
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs text-gray-500 mb-1">Terrain</div>
            <div className="font-medium text-gray-900 text-sm capitalize">
              {site.slope_category}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Slope: {site.avg_slope.toFixed(1)}°
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs text-gray-500 mb-1">Available Area</div>
            <div className="font-medium text-gray-900 text-sm">
              {site.area_sq_ft.toLocaleString()} sq ft
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-3">
            <div className="text-xs text-gray-500 mb-1">Location</div>
            <div className="font-medium text-gray-900 text-xs">
              {site.location_lat.toFixed(5)},
              <br />
              {site.location_lon.toFixed(5)}
            </div>
          </div>
        </div>
      </div>

      {/* Infrastructure Warnings */}
      {(site.has_nearby_roads || site.has_nearby_buildings) && (
        <div className="mb-6">
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <svg
                className="w-5 h-5 text-amber-500 mt-0.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
              <div>
                <h4 className="text-sm font-medium text-amber-800">
                  Infrastructure Notice
                </h4>
                <p className="text-sm text-amber-700 mt-1">
                  This site is near{' '}
                  {[
                    site.has_nearby_roads && 'roads',
                    site.has_nearby_buildings && 'buildings',
                  ]
                    .filter(Boolean)
                    .join(' and ')}
                  . Check for utilities and permits before planting.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Species Recommendations Placeholder */}
      <div className="mb-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Recommended Species
        </h3>
        <div className="border border-dashed border-gray-300 rounded-lg p-6 text-center">
          <svg
            className="w-10 h-10 text-gray-300 mx-auto mb-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
            />
          </svg>
          <p className="text-sm text-gray-500">
            Ask the AI agent for personalized tree recommendations
          </p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="space-y-3">
        <button
          onClick={() => onOpenChat?.(`What tree species would you recommend for this planting site? It has ${site.ndvi_category.replace(/_/g, ' ')} vegetation, ${site.slope_category} terrain, and ${site.area_sq_ft} square feet of space.`)}
          className="w-full bg-canopy-500 hover:bg-canopy-600 text-white font-medium py-3 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
          Get Tree Recommendations
        </button>

        <button
          onClick={() => onOpenChat?.(`I want to plant a tree at this site! Can you help me with: 1) The best tree species for this location 2) Cost estimates 3) Planting instructions`)}
          className="w-full bg-canopy-50 hover:bg-canopy-100 text-canopy-700 font-medium py-3 px-4 rounded-lg transition-colors border border-canopy-200 flex items-center justify-center gap-2"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
            />
          </svg>
          I'll Plant Here!
        </button>
      </div>

      {/* Site ID for reference */}
      <div className="mt-6 pt-4 border-t">
        <p className="text-xs text-gray-400">
          Site ID: {site.site_id}
        </p>
      </div>
    </div>
  )
}
