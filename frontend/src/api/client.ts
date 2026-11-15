import type {
  AiAdvice,
  Comparison,
  PlaceSuggestion,
  Stats,
  TransportModeInfo,
  Trip,
  TripInput,
  TripStatus,
} from './types'

const BASE_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '')

export class ApiError extends Error {
  readonly status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

/** Turns FastAPI error bodies (string or validation list) into one readable message. */
function errorMessage(body: unknown, fallback: string): string {
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail
        .map((d) => (typeof d === 'object' && d && 'msg' in d ? String(d.msg) : String(d)))
        .join('; ')
    }
  }
  return fallback
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    })
  } catch {
    throw new ApiError(0, 'Brak połączenia z serwerem API. Czy backend działa na porcie 8000?')
  }
  if (res.status === 204) return undefined as T
  const body = await res.json().catch(() => null)
  if (!res.ok) throw new ApiError(res.status, errorMessage(body, `Błąd ${res.status}`))
  return body as T
}

export const api = {
  listTrips: (status?: TripStatus) =>
    request<Trip[]>(`/api/trips${status ? `?status=${status}` : ''}`),
  getTrip: (id: number) => request<Trip>(`/api/trips/${id}`),
  createTrip: (data: TripInput) =>
    request<Trip>('/api/trips', { method: 'POST', body: JSON.stringify(data) }),
  updateTrip: (id: number, data: Partial<TripInput>) =>
    request<Trip>(`/api/trips/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteTrip: (id: number) => request<void>(`/api/trips/${id}`, { method: 'DELETE' }),

  compare: (id: number) => request<Comparison>(`/api/trips/${id}/comparison`),
  complete: (id: number, mode: string) =>
    request<Trip>(`/api/trips/${id}/complete`, { method: 'POST', body: JSON.stringify({ mode }) }),
  advice: (id: number) => request<AiAdvice>(`/api/trips/${id}/advice`, { method: 'POST' }),

  stats: () => request<Stats>('/api/stats'),
  modes: () => request<TransportModeInfo[]>('/api/modes'),
  searchPlaces: (q: string, signal?: AbortSignal) =>
    request<PlaceSuggestion[]>(`/api/places?q=${encodeURIComponent(q)}`, { signal }),
}
