import { useEffect, useMemo, useState } from 'react'
import { api } from './api/client'
import type { TransportModeInfo, Trip, TripInput } from './api/types'
import { StatsBar } from './components/StatsBar'
import { TripDetail } from './components/TripDetail'
import { TripForm } from './components/TripForm'
import { type Filter, TripList } from './components/TripList'
import { useTrips } from './hooks/useTrips'

type FormState = { mode: 'create' } | { mode: 'edit'; trip: Trip } | null

export default function App() {
  const { trips, stats, loading, error, refresh } = useTrips()
  const [modes, setModes] = useState<Record<string, TransportModeInfo>>({})
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [filter, setFilter] = useState<Filter>('all')
  const [form, setForm] = useState<FormState>(null)
  const [confirmDelete, setConfirmDelete] = useState<Trip | null>(null)
  const [toast, setToast] = useState<string | null>(null)

  useEffect(() => {
    api
      .modes()
      .then((list) => setModes(Object.fromEntries(list.map((m) => [m.mode, m]))))
      .catch(() => undefined)
  }, [])


  useEffect(() => {
    if (!toast) return
    const t = setTimeout(() => setToast(null), 3500)
    return () => clearTimeout(t)
  }, [toast])

  // Derived selection: falls back to the first trip when nothing (or a deleted trip) is selected.
  const selected = useMemo(
    () => trips.find((t) => t.id === selectedId) ?? trips[0] ?? null,
    [trips, selectedId],
  )

  const saveTrip = async (data: TripInput) => {
    if (form?.mode === 'edit') {
      await api.updateTrip(form.trip.id, data)
      setToast('Zapisano zmiany')
    } else {
      const created = await api.createTrip(data)
      setSelectedId(created.id)
      setFilter('all')
      setToast('Podróż zaplanowana — sprawdź porównanie')
    }
    setForm(null)
    await refresh()
  }

  const deleteTrip = async (trip: Trip) => {
    await api.deleteTrip(trip.id)
    setConfirmDelete(null)
    setToast('Usunięto podróż')
    await refresh()
  }

  const onCompleted = async (trip: Trip) => {
    setToast(trip.eco_points > 0 ? `Brawo! +${trip.eco_points} eko-punktów 🌱` : 'Podróż zapisana jako odbyta')
    await refresh()
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand__mark" aria-hidden>◐</span>
          <div>
            <h1>EcoRoute</h1>
            <p>Planer podróży, który liczy czas, pieniądze i CO₂</p>
          </div>
        </div>
        <button className="btn btn--primary" onClick={() => setForm({ mode: 'create' })}>
          + Nowa podróż
        </button>
      </header>

      <StatsBar stats={stats} modes={modes} />

      {error && <div className="banner banner--error">{error}</div>}

      {loading ? (
        <div className="skeleton skeleton--page" />
      ) : trips.length === 0 ? (
        <section className="panel onboarding">
          <span className="onboarding__icon" aria-hidden>🗺️</span>
          <h2>Zaplanuj pierwszą podróż</h2>
          <p>
            Wpisz skąd i dokąd jedziesz — porównamy 9 środków transportu, sprawdzimy prognozę pogody
            i podpowiemy najlepszy wybór. Za ekologiczne przejazdy zbierasz eko-punkty.
          </p>
          <button className="btn btn--primary" onClick={() => setForm({ mode: 'create' })}>
            + Nowa podróż
          </button>
        </section>
      ) : (
        <main className="layout">
          <TripList
            trips={trips}
            filter={filter}
            onFilterChange={setFilter}
            selectedId={selected?.id ?? null}
            onSelect={setSelectedId}
            modes={modes}
          />
          {selected && (
            <TripDetail
              key={selected.id}
              trip={selected}
              modes={modes}
              onEdit={() => setForm({ mode: 'edit', trip: selected })}
              onDelete={() => setConfirmDelete(selected)}
              onCompleted={onCompleted}
            />
          )}
        </main>
      )}

      {form && (
        <TripForm
          initial={form.mode === 'edit' ? form.trip : undefined}
          onSubmit={saveTrip}
          onCancel={() => setForm(null)}
        />
      )}

      {confirmDelete && (
        <div className="modal" role="alertdialog" aria-modal="true" onMouseDown={() => setConfirmDelete(null)}>
          <div className="modal__card modal__card--small" onMouseDown={(e) => e.stopPropagation()}>
            <h2>Usunąć podróż?</h2>
            <p>„{confirmDelete.title}” zostanie trwale usunięta{confirmDelete.eco_points ? ' razem z jej eko-punktami' : ''}.</p>
            <div className="modal__actions">
              <button className="btn btn--ghost" onClick={() => setConfirmDelete(null)}>Anuluj</button>
              <button className="btn btn--danger-solid" onClick={() => deleteTrip(confirmDelete)}>Usuń</button>
            </div>
          </div>
        </div>
      )}

      {toast && <div className="toast" role="status">{toast}</div>}
    </div>
  )
}
