'use client'

import { useEffect, useState } from 'react'
import type { PlantingSiteResponse, SpeciesData } from '@/types'
import { getPriorityNumber, getPriorityLevel } from '@/types'
import { fetchSpecies } from '@/lib/api/cv'

const OCF_FREE_TREES_URL = 'https://www.ourcityforest.org/free-trees'
const OCF_GRANT_ZONE_URL = 'https://www.ourcityforest.org'

type Tab = 'species' | 'benefits' | 'get-tree'

interface SiteDetailPanelProps {
  site: PlantingSiteResponse
  analysisAddress?: string
}

export default function SiteDetailPanel({ site, analysisAddress }: SiteDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>('species')
  const [species, setSpecies] = useState<SpeciesData[]>([])
  const [speciesLoading, setSpeciesLoading] = useState(true)
  const [speciesError, setSpeciesError] = useState<string | null>(null)
  const [nativeOnly, setNativeOnly] = useState(false)
  const [droughtOnly, setDroughtOnly] = useState(false)
  const [selectedSpecies, setSelectedSpecies] = useState<SpeciesData | null>(null)
  const [projectionYears, setProjectionYears] = useState(10)
  const [diyOpen, setDiyOpen] = useState(false)

  const priority = getPriorityNumber(site.suitability_score)
  const priorityLevel = getPriorityLevel(site.suitability_score)

  const priorityColors = {
    high: { bg: 'bg-green-100', text: 'text-green-800', ring: 'ring-green-500' },
    medium: { bg: 'bg-amber-100', text: 'text-amber-800', ring: 'ring-amber-500' },
    low: { bg: 'bg-gray-100', text: 'text-gray-800', ring: 'ring-gray-500' },
  }
  const colors = priorityColors[priorityLevel]

  useEffect(() => {
    let cancelled = false
    setSpeciesLoading(true)
    setSpeciesError(null)

    fetchSpecies({
      hardiness_zone: 10,
      native_only: nativeOnly,
      drought_tolerant: droughtOnly || undefined,
      limit: 20,
    })
      .then((data) => {
        if (cancelled) return
        setSpecies(data)
        if (!selectedSpecies && data.length > 0) setSelectedSpecies(data[0])
      })
      .catch(() => {
        if (!cancelled) setSpeciesError('Could not load species — is the API running?')
      })
      .finally(() => {
        if (!cancelled) setSpeciesLoading(false)
      })

    return () => { cancelled = true }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nativeOnly, droughtOnly])

  const tabs: { id: Tab; label: string }[] = [
    { id: 'species', label: 'Recommended Species' },
    { id: 'benefits', label: 'Environmental Benefits' },
    { id: 'get-tree', label: 'Get Your Tree' },
  ]

  return (
    <div className="flex flex-col h-full">
      {/* Site header */}
      <div className="p-5 border-b">
        <div className="flex items-start gap-4 mb-4">
          <div className={`w-12 h-12 rounded-full ${colors.bg} ${colors.text} flex items-center justify-center font-bold text-lg ring-2 ${colors.ring} shrink-0`}>
            {priority}
          </div>
          <div className="min-w-0">
            <h2 className="text-base font-semibold text-gray-900">Planting Site</h2>
            <p className="text-sm text-gray-500">Priority: {priorityLevel.charAt(0).toUpperCase() + priorityLevel.slice(1)}</p>
            {analysisAddress && <p className="text-xs text-gray-400 mt-0.5 truncate">{analysisAddress}</p>}
          </div>
        </div>

        <div>
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-500">Suitability</span>
            <span className="font-medium text-gray-800">{(site.suitability_score * 100).toFixed(0)}%</span>
          </div>
          <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${priorityLevel === 'high' ? 'bg-green-500' : priorityLevel === 'medium' ? 'bg-amber-500' : 'bg-gray-400'}`}
              style={{ width: `${site.suitability_score * 100}%` }}
            />
          </div>
        </div>

        <div className="flex gap-3 mt-3 text-xs text-gray-500">
          <span>NDVI {site.avg_ndvi.toFixed(2)}</span>
          <span>·</span>
          <span>Slope {site.avg_slope.toFixed(1)}°</span>
          <span>·</span>
          <span>{site.area_sq_ft.toLocaleString()} sq ft</span>
        </div>

        {(site.has_nearby_roads || site.has_nearby_buildings) && (
          <div className="mt-3 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 text-xs text-amber-700 flex gap-2 items-start">
            <span className="mt-0.5">⚠️</span>
            <span>
              Near {[site.has_nearby_roads && 'roads', site.has_nearby_buildings && 'buildings'].filter(Boolean).join(' & ')}
              {' '}— confirm clearances before planting.
            </span>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b text-sm shrink-0">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 py-2.5 px-1 font-medium transition-colors text-center leading-tight text-xs ${
              activeTab === tab.id
                ? 'text-green-700 border-b-2 border-green-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'species' && (
          <SpeciesTab
            species={species}
            loading={speciesLoading}
            error={speciesError}
            nativeOnly={nativeOnly}
            droughtOnly={droughtOnly}
            selectedSpecies={selectedSpecies}
            onToggleNative={() => setNativeOnly((v) => !v)}
            onToggleDrought={() => setDroughtOnly((v) => !v)}
            onSelectSpecies={setSelectedSpecies}
          />
        )}
        {activeTab === 'benefits' && (
          <BenefitsTab
            species={species}
            selectedSpecies={selectedSpecies}
            projectionYears={projectionYears}
            onSelectSpecies={setSelectedSpecies}
            onChangeYears={setProjectionYears}
          />
        )}
        {activeTab === 'get-tree' && (
          <GetTreeTab
            diyOpen={diyOpen}
            onToggleDiy={() => setDiyOpen((v) => !v)}
          />
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Tab 1: Recommended Species
// ---------------------------------------------------------------------------

function SpeciesTab({
  species, loading, error, nativeOnly, droughtOnly, selectedSpecies,
  onToggleNative, onToggleDrought, onSelectSpecies,
}: {
  species: SpeciesData[]
  loading: boolean
  error: string | null
  nativeOnly: boolean
  droughtOnly: boolean
  selectedSpecies: SpeciesData | null
  onToggleNative: () => void
  onToggleDrought: () => void
  onSelectSpecies: (s: SpeciesData) => void
}) {
  return (
    <div className="p-4">
      <div className="flex gap-2 mb-4">
        <FilterChip active={nativeOnly} onClick={onToggleNative} label="CA Native" />
        <FilterChip active={droughtOnly} onClick={onToggleDrought} label="Drought Tolerant" />
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12 text-gray-400 text-sm gap-2">
          <div className="w-4 h-4 border-2 border-green-500 border-t-transparent rounded-full animate-spin" />
          Loading species…
        </div>
      )}
      {error && <div className="py-6 text-center text-sm text-red-500">{error}</div>}
      {!loading && !error && species.length === 0 && (
        <div className="py-6 text-center text-sm text-gray-400">No species match the current filters.</div>
      )}

      <div className="space-y-3">
        {species.map((sp) => (
          <SpeciesCard
            key={sp.species_id}
            species={sp}
            selected={selectedSpecies?.species_id === sp.species_id}
            onSelect={() => onSelectSpecies(sp)}
          />
        ))}
      </div>

      {!loading && species.length > 0 && (
        <p className="text-xs text-gray-400 mt-4 text-center">
          Species availability subject to change — confirm with Our City Forest before visiting.
        </p>
      )}
    </div>
  )
}

function FilterChip({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors border ${
        active
          ? 'bg-green-600 text-white border-green-600'
          : 'bg-white text-gray-600 border-gray-300 hover:border-green-400'
      }`}
    >
      {label}
    </button>
  )
}

function SpeciesCard({ species: sp, selected, onSelect }: { species: SpeciesData; selected: boolean; onSelect: () => void }) {
  const isNative = sp.native_regions?.includes('california')

  return (
    <div
      onClick={onSelect}
      className={`rounded-lg border p-4 cursor-pointer transition-all ${
        selected ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-green-300 bg-white'
      }`}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="min-w-0">
          <p className="font-medium text-gray-900 text-sm">{sp.common_name}</p>
          <p className="text-xs text-gray-400 italic truncate">{sp.scientific_name}</p>
        </div>
        <div className="flex gap-1 shrink-0 flex-wrap justify-end">
          {isNative && <Badge text="CA Native" color="green" />}
          {sp.drought_tolerant && <Badge text="Drought OK" color="amber" />}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-gray-600 mb-3">
        <span>Height: {sp.mature_height_ft} ft</span>
        <span>Spread: {sp.mature_spread_ft} ft</span>
        <span>CO₂: {sp.co2_sequestration_kg_year} kg/yr</span>
        <span>Water: {sp.stormwater_interception_gal_year.toFixed(0)} gal/yr</span>
      </div>

      <a
        href={OCF_FREE_TREES_URL}
        target="_blank"
        rel="noopener noreferrer"
        onClick={(e) => e.stopPropagation()}
        className="block w-full text-center py-2 rounded-md bg-green-600 hover:bg-green-700 text-white text-xs font-medium transition-colors"
      >
        Get this tree free from Our City Forest →
      </a>
    </div>
  )
}

function Badge({ text, color }: { text: string; color: 'green' | 'amber' }) {
  const cls = color === 'green' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
  return <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${cls}`}>{text}</span>
}

// ---------------------------------------------------------------------------
// Tab 2: Environmental Benefits
// ---------------------------------------------------------------------------

function BenefitsTab({
  species, selectedSpecies, projectionYears, onSelectSpecies, onChangeYears,
}: {
  species: SpeciesData[]
  selectedSpecies: SpeciesData | null
  projectionYears: number
  onSelectSpecies: (s: SpeciesData) => void
  onChangeYears: (y: number) => void
}) {
  if (!selectedSpecies) {
    return (
      <div className="p-6 text-center text-sm text-gray-400">
        Select a species in the Species tab to see projected benefits.
      </div>
    )
  }

  const co2Total = selectedSpecies.co2_sequestration_kg_year * projectionYears
  const stormTotal = selectedSpecies.stormwater_interception_gal_year * projectionYears
  const airTotal = selectedSpecies.air_pollution_removal_kg_year * projectionYears
  const carMiles = Math.round(co2Total / 0.21)
  const laundryLoads = Math.round(stormTotal / 20)

  return (
    <div className="p-4">
      {species.length > 1 && (
        <div className="mb-4">
          <label className="text-xs text-gray-500 mb-1 block">Species</label>
          <select
            value={selectedSpecies.species_id}
            onChange={(e) => {
              const sp = species.find((s) => s.species_id === e.target.value)
              if (sp) onSelectSpecies(sp)
            }}
            className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 text-gray-800 focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            {species.map((sp) => (
              <option key={sp.species_id} value={sp.species_id}>{sp.common_name}</option>
            ))}
          </select>
        </div>
      )}

      <div className="mb-5">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-gray-500">Projection period</span>
          <span className="font-medium text-gray-800">{projectionYears} years</span>
        </div>
        <input
          type="range"
          min={1}
          max={30}
          value={projectionYears}
          onChange={(e) => onChangeYears(Number(e.target.value))}
          className="w-full accent-green-600"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-0.5">
          <span>1 yr</span>
          <span>30 yrs</span>
        </div>
      </div>

      <div className="space-y-3">
        <BenefitCard
          icon="🌿"
          label="CO₂ Absorbed"
          value={`${co2Total.toLocaleString(undefined, { maximumFractionDigits: 0 })} kg`}
          sub={`${selectedSpecies.co2_sequestration_kg_year} kg per year`}
          equiv={`≈ ${carMiles.toLocaleString()} miles of car emissions offset`}
          color="green"
        />
        <BenefitCard
          icon="💧"
          label="Stormwater Intercepted"
          value={`${stormTotal.toLocaleString(undefined, { maximumFractionDigits: 0 })} gal`}
          sub={`${selectedSpecies.stormwater_interception_gal_year.toFixed(0)} gal per year`}
          equiv={`≈ ${laundryLoads.toLocaleString()} loads of laundry worth of water`}
          color="blue"
        />
        <BenefitCard
          icon="💨"
          label="Air Pollution Removed"
          value={`${airTotal.toFixed(2)} kg`}
          sub={`${selectedSpecies.air_pollution_removal_kg_year} kg per year`}
          color="purple"
        />
      </div>

      <p className="text-xs text-gray-400 mt-4 text-center">
        Estimates based on i-Tree data for mature {selectedSpecies.common_name}.
      </p>
    </div>
  )
}

function BenefitCard({
  icon, label, value, sub, equiv, color,
}: {
  icon: string
  label: string
  value: string
  sub: string
  equiv?: string
  color: 'green' | 'blue' | 'purple'
}) {
  const styles = {
    green: { wrap: 'bg-green-50 border-green-200', val: 'text-green-700' },
    blue: { wrap: 'bg-blue-50 border-blue-200', val: 'text-blue-700' },
    purple: { wrap: 'bg-purple-50 border-purple-200', val: 'text-purple-700' },
  }[color]

  return (
    <div className={`rounded-lg border p-4 ${styles.wrap}`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-lg">{icon}</span>
        <span className="text-xs font-medium text-gray-600">{label}</span>
      </div>
      <p className={`text-2xl font-bold ${styles.val}`}>{value}</p>
      <p className="text-xs text-gray-500 mt-0.5">{sub}</p>
      {equiv && <p className="text-xs text-gray-400 mt-1 italic">{equiv}</p>}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Tab 3: Get Your Tree
// ---------------------------------------------------------------------------

function GetTreeTab({ diyOpen, onToggleDiy }: { diyOpen: boolean; onToggleDiy: () => void }) {
  return (
    <div className="p-5 space-y-5">
      {/* Primary CTA */}
      <div className="rounded-xl bg-green-600 text-white p-5 text-center">
        <div className="text-3xl mb-2">🌳</div>
        <h3 className="font-semibold text-lg mb-1">Our City Forest plants it for you</h3>
        <p className="text-green-100 text-sm mb-4">
          The most popular option — OCF&apos;s team plants your free tree at no cost to you.
        </p>
        <a
          href={OCF_FREE_TREES_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="block w-full py-3 rounded-lg bg-white text-green-700 font-semibold text-sm hover:bg-green-50 transition-colors"
        >
          Request Free Tree Planting →
        </a>
      </div>

      {/* Grant zone note */}
      <div className="rounded-lg bg-amber-50 border border-amber-200 p-4">
        <p className="font-medium text-amber-800 text-sm mb-1">Are you in the grant zone?</p>
        <p className="text-amber-700 text-xs mb-2">
          OCF&apos;s free planting service is available to addresses in their VTA-supported grant zone (shown on their website map).
        </p>
        <a
          href={OCF_GRANT_ZONE_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-amber-700 underline font-medium"
        >
          Check your eligibility on OCF&apos;s website →
        </a>
      </div>

      {/* DIY collapsible */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <button
          onClick={onToggleDiy}
          className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-gray-700 bg-gray-50 hover:bg-gray-100 transition-colors"
        >
          <span>I&apos;ll plant it myself</span>
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform ${diyOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {diyOpen && (
          <div className="px-4 py-4 text-sm text-gray-600 space-y-3">
            <p className="font-medium text-gray-700 text-xs">Basic planting steps:</p>
            <ol className="list-decimal list-inside space-y-2 text-xs leading-relaxed text-gray-600">
              <li>Call 811 at least 2 days before digging to mark underground utilities.</li>
              <li>Dig a hole 2–3× the width of the root ball and the same depth.</li>
              <li>Remove the tree from its container; gently loosen circling roots.</li>
              <li>Place tree so the root flare sits at or slightly above ground level.</li>
              <li>Backfill with native soil, tamping lightly to remove air pockets.</li>
              <li>Water deeply immediately; add 3–4 inches of mulch, keeping it away from the trunk.</li>
              <li>Water 2× per week for the first summer; once weekly after that.</li>
            </ol>
            <p className="text-xs text-gray-400">
              Contact Our City Forest for species-specific planting guidance.
            </p>
          </div>
        )}
      </div>

      <p className="text-xs text-gray-400 text-center">
        SmartCanopy is an independent tool supporting urban forestry in the Bay Area.
        Species availability is subject to change — visit Our City Forest to confirm.
      </p>
    </div>
  )
}
