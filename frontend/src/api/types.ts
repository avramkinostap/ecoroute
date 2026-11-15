// Mirrors the backend Pydantic schemas (app/schemas.py).

export type Priority = 'balanced' | 'eco' | 'fast' | 'cheap'
export type TripStatus = 'planned' | 'completed'

export interface Place {
  name: string
  lat: number
  lon: number
}

export interface PlaceSuggestion extends Place {
  country?: string | null
  region?: string | null
}

export interface Trip {
  id: number
  title: string
  origin: Place
  destination: Place
  distance_km: number
  departure_at: string
  passengers: number
  priority: Priority
  notes: string | null
  status: TripStatus
  chosen_mode: string | null
  co2_kg: number | null
  co2_saved_kg: number | null
  eco_points: number
  created_at: string
  updated_at: string
}

export interface TripInput {
  title: string
  origin: Place
  destination: Place
  departure_at: string
  passengers: number
  priority: Priority
  notes: string | null
}

export interface Weather {
  temperature_c: number
  precipitation_probability: number
  precipitation_mm: number
  wind_kmh: number
  weather_code: number
  description: string
  icon: string
  bad_for_active_modes: boolean
}

export interface ModeOption {
  mode: string
  label: string
  icon: string
  feasible: boolean
  duration_min: number | null
  cost_pln: number | null
  co2_kg: number | null
  score: number | null
  note: string | null
}

export interface Comparison {
  trip_id: number
  distance_km: number
  weather: Weather | null
  options: ModeOption[]
  recommended_mode: string | null
  reasons: string[]
  car_baseline_co2_kg: number
}

export interface AiAdvice {
  source: 'ai' | 'rules'
  summary: string
  tips: string[]
  model: string | null
}

export interface Stats {
  total_trips: number
  completed_trips: number
  eco_points: number
  co2_saved_kg: number
  level: string
  next_level_at: number | null
  favourite_mode: string | null
}

export interface TransportModeInfo {
  mode: string
  label: string
  icon: string
}
