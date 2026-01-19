// Map types
export type MapTier = 'city' | 'neighborhood' | 'street'

export interface ViewState {
  center: [number, number] // [lng, lat]
  zoom: number
}

// City data (Tier 1 - Mock)
export interface CityData {
  id: string
  name: string
  state: string
  coordinates: [number, number] // [lng, lat]
  bounds: [[number, number], [number, number]] // [[sw_lng, sw_lat], [ne_lng, ne_lat]]
  canopyPercentage: number
  population: number
  treeEquityScore: number // 0-100
}

// Neighborhood data (Tier 2 - Mock)
export interface NeighborhoodCell {
  id: string
  cityId: string
  name: string
  geometry: GeoJSON.Polygon
  canopyPercentage: number
  heatIslandIndex: number // 0-100, higher = hotter
  needScore: number // calculated: inverse of canopy + heat
  center: [number, number]
}

// API Response Types (from backend)
export interface PlantingSiteResponse {
  site_id: string
  location_lat: number
  location_lon: number
  avg_ndvi: number
  ndvi_category: 'bare_soil_or_pavement' | 'sparse_vegetation' | 'moderate_vegetation' | 'dense_vegetation'
  avg_slope: number
  slope_category: 'flat' | 'gentle' | 'moderate' | 'steep'
  area_sq_ft: number
  suitability_score: number
  has_nearby_roads: boolean
  has_nearby_buildings: boolean
}

export interface ExistingTreeResponse {
  lat: number
  lon: number
  confidence: number
  bbox_width: number
  bbox_height: number
}

export interface AnalysisResponse {
  analysis_id: string
  address: string
  latitude: number
  longitude: number
  planting_sites: PlantingSiteResponse[]
  existing_trees: ExistingTreeResponse[]
  existing_trees_count: number
  imagery_saved: boolean
  timestamp: string
}

export interface AnalysisRequest {
  address: string
  buffer_m?: number
  save_images?: boolean
}

// Chat types
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  toolCalls?: ToolCall[]
  isPartial?: boolean
}

export interface ToolCall {
  tool: string
  input: Record<string, unknown>
  success?: boolean
}

export interface ChatRequest {
  message: string
  conversation_id?: string
  conversation_history?: Array<{ role: string; content: string }>
  site_context?: Record<string, unknown>
  max_tool_rounds?: number
}

export interface ChatResponse {
  conversation_id: string
  response: string
  conversation_history: Array<{ role: string; content: string }>
  tool_calls: ToolCall[]
  rounds: number
  timestamp: string
}

// WebSocket message types
export type WSMessage =
  | { type: 'chunk'; text: string }
  | { type: 'tool_use'; tool_name: string; tool_input: Record<string, unknown> }
  | { type: 'tool_result'; tool_name: string; success: boolean }
  | { type: 'complete'; full_response: string; tool_calls: ToolCall[]; conversation_id: string }
  | { type: 'error'; message: string }

// Species types
export interface Species {
  species_id: string
  common_name: string
  scientific_name: string
  tree_type: string
  mature_height_ft: number
  mature_spread_ft: number
  growth_rate: string
  hardiness_zone_min: number
  hardiness_zone_max: number
  drought_tolerant: boolean
  co2_sequestration_kg_year: number
  stormwater_interception_gal_year: number
  air_pollution_removal_kg_year: number
  native_regions: string[]
  maintenance_level: string
  price_6ft: number
}

// Filter types
export interface Filters {
  priorityLevel: 'all' | 'high' | 'medium' | 'low'
  showInfrastructureWarnings: boolean
  nearSchools: boolean
  nearParks: boolean
}

// Helper functions for classification
export function getCanopyCategory(percentage: number): 'critical' | 'low' | 'healthy' {
  if (percentage < 15) return 'critical'
  if (percentage < 25) return 'low'
  return 'healthy'
}

export function getPriorityLevel(suitabilityScore: number): 'high' | 'medium' | 'low' {
  if (suitabilityScore >= 0.7) return 'high'
  if (suitabilityScore >= 0.4) return 'medium'
  return 'low'
}

export function getPriorityNumber(suitabilityScore: number): number {
  // Convert 0-1 score to 1-10 priority
  return Math.round(suitabilityScore * 10)
}
