'use client'

import { useMapStore } from '@/stores/mapStore'
import { EQUITY_COLORS, SITE_COLORS } from '@/lib/mapbox/config'
import { NEED_COLORS } from '@/data/mock/neighborhoods'

export default function Legend() {
  const { currentTier } = useMapStore()

  return (
    <div className="absolute bottom-8 left-4 bg-white rounded-lg shadow-lg p-4 z-10 max-w-xs">
      {/* City Level Legend */}
      {currentTier === 'city' && (
        <>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Tree Canopy Coverage</h3>
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: EQUITY_COLORS.critical }}
              />
              <span className="text-xs text-gray-600">&lt; 15% (Critical)</span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: EQUITY_COLORS.low }}
              />
              <span className="text-xs text-gray-600">15-25% (Below Target)</span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: EQUITY_COLORS.healthy }}
              />
              <span className="text-xs text-gray-600">&gt; 25% (Healthy)</span>
            </div>
          </div>
        </>
      )}

      {/* Neighborhood Level Legend */}
      {currentTier === 'neighborhood' && (
        <>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Planting Need</h3>
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded"
                style={{ backgroundColor: NEED_COLORS.high, opacity: 0.7 }}
              />
              <span className="text-xs text-gray-600">High Need (Low canopy + Heat)</span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded"
                style={{ backgroundColor: NEED_COLORS.medium, opacity: 0.7 }}
              />
              <span className="text-xs text-gray-600">Moderate Need</span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded"
                style={{ backgroundColor: NEED_COLORS.low, opacity: 0.7 }}
              />
              <span className="text-xs text-gray-600">Good Coverage</span>
            </div>
          </div>
        </>
      )}

      {/* Street Level Legend */}
      {currentTier === 'street' && (
        <>
          <h3 className="text-sm font-semibold text-gray-700 mb-2">Planting Sites</h3>
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: SITE_COLORS.recommended }}
              />
              <span className="text-xs text-gray-600">Recommended Site</span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: SITE_COLORS.existing }}
              />
              <span className="text-xs text-gray-600">Existing Tree</span>
            </div>
          </div>
          <div className="mt-2 pt-2 border-t">
            <p className="text-xs text-gray-600">
              <span className="font-medium">Priority:</span> Higher number = better site
            </p>
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Click a site to view details & recommendations
          </p>
        </>
      )}
    </div>
  )
}
