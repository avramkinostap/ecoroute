import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { Stats, Trip } from '../api/types'

/** Loads the trip list together with eco stats and exposes a single refresh(). */
export function useTrips() {
  const [trips, setTrips] = useState<Trip[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(
    () =>
      Promise.all([api.listTrips(), api.stats()])
        .then(([list, s]) => {
          setTrips(list)
          setStats(s)
          setError(null)
        })
        .catch((e: Error) => setError(e.message))
        .finally(() => setLoading(false)),
    [],
  )

  useEffect(() => {
    refresh()
  }, [refresh])

  return { trips, stats, loading, error, refresh }
}
