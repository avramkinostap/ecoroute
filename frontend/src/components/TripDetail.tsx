import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Comparison, TransportModeInfo, Trip } from '../api/types'
import { formatDate, formatKg, PRIORITY_LABELS } from '../utils/format'
import { AdvicePanel } from './AdvicePanel'
import { ModeCard } from './ModeCard'

interface Props {
  trip: Trip
  modes: Record<string, TransportModeInfo>
  onEdit: () => void
  onDelete: () => void
  onCompleted: (trip: Trip) => void
}

export function TripDetail({ trip, modes, onEdit, onDelete, onCompleted }: Props) {
  // Comparison is tagged with the trip version it was computed for, so an edit
  // (new updated_at) shows the loader again without resetting state in an effect.
  const version = trip.updated_at
  const [loaded, setLoaded] = useState<{ version: string; data: Comparison } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const comparison = loaded?.version === version ? loaded.data : null
  const [busy, setBusy] = useState(false)
  const [showAll, setShowAll] = useState(false)

  useEffect(() => {
    let cancelled = false
    api
      .compare(trip.id)
      .then((data) => {
        if (cancelled) return
        setLoaded({ version, data })
        setError(null)
      })
      .catch((e: Error) => !cancelled && setError(e.message))
    return () => {
      cancelled = true
    }
  }, [trip.id, version])

  const choose = async (mode: string) => {
    setBusy(true)
    try {
      onCompleted(await api.complete(trip.id, mode))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }

  const planned = trip.status === 'planned'
  const feasible = (comparison?.options ?? [])
    .filter((o) => o.feasible)
    .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
  const unavailable = (comparison?.options ?? []).filter((o) => !o.feasible)
  const shown = showAll ? feasible : feasible.slice(0, 4)
  const maxCo2 = Math.max(0, ...feasible.map((o) => o.co2_kg ?? 0))
  const chosen = trip.chosen_mode ? modes[trip.chosen_mode] : null

  return (
    <section className="panel detail">
      <header className="detail__head">
        <div>
          <p className="eyebrow">
            {formatDate(trip.departure_at)} · {trip.passengers} {trip.passengers === 1 ? 'osoba' : 'osoby'} ·{' '}
            {PRIORITY_LABELS[trip.priority].icon} {PRIORITY_LABELS[trip.priority].label}
          </p>
          <h2>{trip.title}</h2>
          <p className="route">
            <span>{trip.origin.name}</span>
            <span className="route__line" aria-hidden><i>{trip.distance_km} km</i></span>
            <span>{trip.destination.name}</span>
          </p>
          {trip.notes && <p className="notes">📝 {trip.notes}</p>}
        </div>
        <div className="detail__actions">
          {planned && <button className="btn btn--ghost" onClick={onEdit}>Edytuj</button>}
          <button className="btn btn--ghost btn--danger" onClick={onDelete}>Usuń</button>
        </div>
      </header>

      {!planned && chosen && (
        <div className="result">
          <span className="result__icon">{chosen.icon}</span>
          <div>
            <strong>Podróż odbyta: {chosen.label}</strong>
            <span>
              Emisja {formatKg(trip.co2_kg)} · zaoszczędzone {formatKg(trip.co2_saved_kg)} CO₂
            </span>
          </div>
          <span className="result__points">+{trip.eco_points} pkt</span>
        </div>
      )}

      {error && <p className="form-error">{error}</p>}
      {!comparison && !error && <div className="skeleton" aria-label="Ładowanie porównania" />}

      {comparison && (
        <>
          <div className="insight">
            <div className={`weather ${comparison.weather?.bad_for_active_modes ? 'weather--bad' : ''}`}>
              {comparison.weather ? (
                <>
                  <span className="weather__icon">{comparison.weather.icon}</span>
                  <div>
                    <strong>{comparison.weather.temperature_c}°C · {comparison.weather.description}</strong>
                    <span>
                      opady {comparison.weather.precipitation_probability}% · wiatr {comparison.weather.wind_kmh} km/h
                    </span>
                  </div>
                </>
              ) : (
                <>
                  <span className="weather__icon">🌡️</span>
                  <div>
                    <strong>Prognoza niedostępna</strong>
                    <span>Pogoda jest znana do ~15 dni naprzód</span>
                  </div>
                </>
              )}
            </div>
            <ul className="reasons">
              {comparison.reasons.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          </div>

          <div className="modes">
            {shown.map((o) => (
              <ModeCard
                key={o.mode}
                option={o}
                recommended={o.mode === comparison.recommended_mode}
                chosen={o.mode === trip.chosen_mode}
                maxCo2={maxCo2}
                baselineCo2={comparison.car_baseline_co2_kg}
                onChoose={planned ? () => choose(o.mode) : undefined}
                busy={busy}
              />
            ))}
          </div>

          <div className="modes__more">
            {feasible.length > 4 && (
              <button className="link" onClick={() => setShowAll((s) => !s)}>
                {showAll ? 'Pokaż mniej' : `Pokaż wszystkie (${feasible.length})`}
              </button>
            )}
            {unavailable.length > 0 && (
              <span className="muted">
                Niedostępne: {unavailable.map((o) => `${o.icon} ${o.label} (${o.note})`).join(', ')}
              </span>
            )}
          </div>

          {planned && <AdvicePanel tripId={trip.id} />}
        </>
      )}
    </section>
  )
}
