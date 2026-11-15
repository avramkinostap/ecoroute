import { useState } from 'react'
import type { Place, Priority, Trip, TripInput } from '../api/types'
import { defaultDeparture, PRIORITY_LABELS, toLocalInput } from '../utils/format'
import { PlaceInput } from './PlaceInput'

interface Props {
  initial?: Trip
  onSubmit: (data: TripInput) => Promise<void>
  onCancel: () => void
}

export function TripForm({ initial, onSubmit, onCancel }: Props) {
  const [title, setTitle] = useState(initial?.title ?? '')
  const [origin, setOrigin] = useState<Place | null>(initial?.origin ?? null)
  const [destination, setDestination] = useState<Place | null>(initial?.destination ?? null)
  const [departure, setDeparture] = useState(initial ? toLocalInput(initial.departure_at) : defaultDeparture())
  const [passengers, setPassengers] = useState(initial?.passengers ?? 1)
  const [priority, setPriority] = useState<Priority>(initial?.priority ?? 'balanced')
  const [notes, setNotes] = useState(initial?.notes ?? '')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!origin || !destination) {
      setError('Wybierz punkt startowy i docelowy z listy podpowiedzi.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      await onSubmit({
        title: title.trim() || `${origin.name} → ${destination.name}`,
        origin,
        destination,
        departure_at: new Date(departure).toISOString(),
        passengers,
        priority,
        notes: notes.trim() || null,
      })
    } catch (err) {
      setError((err as Error).message)
      setSaving(false)
    }
  }

  return (
    <div className="modal" role="dialog" aria-modal="true" aria-labelledby="form-title" onMouseDown={onCancel}>
      <form className="modal__card" onSubmit={submit} onMouseDown={(e) => e.stopPropagation()}>
        <h2 id="form-title">{initial ? 'Edytuj podróż' : 'Nowa podróż'}</h2>

        <div className="field">
          <label htmlFor="title">Nazwa</label>
          <input
            id="title"
            value={title}
            maxLength={120}
            placeholder="np. Na zajęcia, Weekend w Krakowie"
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>

        <div className="grid-2">
          <PlaceInput label="Skąd" value={origin} onChange={setOrigin} placeholder="Wpisz miasto…" />
          <PlaceInput label="Dokąd" value={destination} onChange={setDestination} placeholder="Wpisz miasto…" />
        </div>

        <div className="grid-2">
          <div className="field">
            <label htmlFor="departure">Wyjazd</label>
            <input
              id="departure"
              type="datetime-local"
              required
              value={departure}
              onChange={(e) => setDeparture(e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="passengers">Liczba osób</label>
            <div className="stepper">
              <button type="button" onClick={() => setPassengers((p) => Math.max(1, p - 1))} aria-label="Mniej osób">−</button>
              <input id="passengers" type="number" min={1} max={8} value={passengers}
                onChange={(e) => setPassengers(Math.min(8, Math.max(1, Number(e.target.value) || 1)))} />
              <button type="button" onClick={() => setPassengers((p) => Math.min(8, p + 1))} aria-label="Więcej osób">+</button>
            </div>
          </div>
        </div>

        <fieldset className="field">
          <legend>Co jest dla Ciebie najważniejsze?</legend>
          <div className="priority-picker">
            {(Object.keys(PRIORITY_LABELS) as Priority[]).map((p) => (
              <label key={p} className={`priority ${priority === p ? 'priority--active' : ''}`}>
                <input type="radio" name="priority" value={p} checked={priority === p} onChange={() => setPriority(p)} />
                <span className="priority__icon">{PRIORITY_LABELS[p].icon}</span>
                <span className="priority__label">{PRIORITY_LABELS[p].label}</span>
                <span className="priority__hint">{PRIORITY_LABELS[p].hint}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <div className="field">
          <label htmlFor="notes">Notatki (opcjonalnie — widzi je też asystent AI)</label>
          <textarea id="notes" rows={2} maxLength={1000} value={notes}
            placeholder="np. wiozę duży bagaż, muszę być na 9:00"
            onChange={(e) => setNotes(e.target.value)} />
        </div>

        {error && <p className="form-error" role="alert">{error}</p>}

        <div className="modal__actions">
          <button type="button" className="btn btn--ghost" onClick={onCancel}>Anuluj</button>
          <button type="submit" className="btn btn--primary" disabled={saving}>
            {saving ? 'Zapisywanie…' : initial ? 'Zapisz zmiany' : 'Zaplanuj podróż'}
          </button>
        </div>
      </form>
    </div>
  )
}
