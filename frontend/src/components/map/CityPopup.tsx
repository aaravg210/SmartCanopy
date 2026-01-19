import { getCanopyCategory } from '@/types'
import { EQUITY_COLORS } from '@/lib/mapbox/config'

interface CityPopupProps {
  name: string
  state: string
  canopyPercentage: number
  treeEquityScore: number
  population: number
}

/**
 * Generates HTML string for city popup
 * Used by Mapbox popup which requires HTML string
 */
export default function CityPopup({
  name,
  state,
  canopyPercentage,
  treeEquityScore,
  population,
}: CityPopupProps): string {
  const category = getCanopyCategory(canopyPercentage)
  const categoryColor = EQUITY_COLORS[category]
  const categoryLabel =
    category === 'critical'
      ? 'Critical Need'
      : category === 'low'
        ? 'Below Target'
        : 'Healthy'

  return `
    <div style="padding: 12px; min-width: 180px;">
      <div style="font-weight: 600; font-size: 14px; color: #1f2937; margin-bottom: 4px;">
        ${name}, ${state}
      </div>
      <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 8px;">
        <div style="
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background-color: ${categoryColor};
        "></div>
        <span style="font-size: 12px; color: #6b7280;">${categoryLabel}</span>
      </div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">
        <div>
          <div style="color: #9ca3af;">Canopy</div>
          <div style="font-weight: 500; color: #374151;">${canopyPercentage.toFixed(1)}%</div>
        </div>
        <div>
          <div style="color: #9ca3af;">Equity Score</div>
          <div style="font-weight: 500; color: #374151;">${treeEquityScore}/100</div>
        </div>
      </div>
      <div style="
        margin-top: 10px;
        padding-top: 8px;
        border-top: 1px solid #e5e7eb;
        font-size: 11px;
        color: #6b7280;
      ">
        Pop. ${(population / 1000000).toFixed(1)}M · Click to explore
      </div>
    </div>
  `
}
