import { useState } from 'react'
import { api } from '../api/client'
import type { AiAdvice } from '../api/types'

/** Rendered inside TripDetail, which is keyed by trip id — state resets per trip. */
export function AdvicePanel({ tripId }: { tripId: number }) {
  const [advice, setAdvice] = useState<AiAdvice | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const ask = async () => {
    setLoading(true)
    setError(null)
    try {
      setAdvice(await api.advice(tripId))
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="advice">
      <div className="advice__head">
        <div>
          <h3>🧭 Doradca podróży</h3>
          <p>Analizuje porównanie, pogodę i Twoje notatki — i podpowiada, jak się przygotować.</p>
        </div>
        <button className="btn btn--accent" onClick={ask} disabled={loading}>
          {loading ? 'Myślę…' : advice ? 'Zapytaj ponownie' : 'Zapytaj doradcę'}
        </button>
      </div>

      {error && <p className="form-error">{error}</p>}

      {advice && (
        <div className="advice__body">
          <p className="advice__summary">{advice.summary}</p>
          {advice.tips.length > 0 && (
            <ul>
              {advice.tips.map((t) => (
                <li key={t}>{t}</li>
              ))}
            </ul>
          )}
          <span className="advice__source">
            {advice.source === 'ai' ? `✨ Wygenerowano przez AI (${advice.model})` : '⚙️ Tryb regułowy (brak klucza API)'}
          </span>
        </div>
      )}
    </section>
  )
}
