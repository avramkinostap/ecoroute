import type { TransportModeInfo, Trip, TripStatus } from '../api/types'
import { formatDate, PRIORITY_LABELS } from '../utils/format'

export type Filter = 'all' | TripStatus

interface Props {
  trips: Trip[]
  filter: Filter
  onFilterChange: (f: Filter) => void
  selectedId: number | null
  onSelect: (id: number) => void
  modes: Record<string, TransportModeInfo>
}

const FILTERS: { key: Filter; label: string }[] = [
  { key: 'all', label: 'Wszystkie' },
  { key: 'planned', label: 'Zaplanowane' },
  { key: 'completed', label: 'Odbyte' },
]

export function TripList({ trips, filter, onFilterChange, selectedId, onSelect, modes }: Props) {
  const visible = filter === 'all' ? trips : trips.filter((t) => t.status === filter)

  return (
    <aside className="panel trips">
      <div className="segmented" role="tablist">
        {FILTERS.map((f) => (
          <button
            key={f.key}
            role="tab"
            aria-selected={filter === f.key}
            className={filter === f.key ? 'active' : ''}
            onClick={() => onFilterChange(f.key)}
          >
            {f.label}
          </button>
        ))}
      </div>

      {visible.length === 0 ? (
        <p className="empty">Brak podróży w tym widoku.</p>
      ) : (
        <ul className="ticket-list">
          {visible.map((t) => {
            const mode = t.chosen_mode ? modes[t.chosen_mode] : null
            return (
              <li key={t.id}>
                <button
                  className={`ticket ${selectedId === t.id ? 'ticket--active' : ''} ${t.status === 'completed' ? 'ticket--done' : ''}`}
                  onClick={() => onSelect(t.id)}
                >
                  <span className="ticket__title">{t.title}</span>
                  <span className="ticket__route">
                    {t.origin.name} <span aria-hidden>→</span> {t.destination.name}
                  </span>
                  <span className="ticket__meta">
                    <span>{formatDate(t.departure_at)}</span>
                    <span>{t.distance_km} km</span>
                    {t.status === 'completed' && mode ? (
                      <span className="chip chip--green">
                        {mode.icon} +{t.eco_points} pkt
                      </span>
                    ) : (
                      <span className="chip">{PRIORITY_LABELS[t.priority].icon} {PRIORITY_LABELS[t.priority].label}</span>
                    )}
                  </span>
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </aside>
  )
}
