import type { ModeOption } from '../api/types'
import { formatDuration, formatKg, formatPln } from '../utils/format'

interface Props {
  option: ModeOption
  recommended: boolean
  chosen: boolean
  maxCo2: number
  baselineCo2: number
  onChoose?: () => void
  busy?: boolean
}

export function ModeCard({ option, recommended, chosen, maxCo2, baselineCo2, onChoose, busy }: Props) {
  const co2Width = maxCo2 > 0 ? Math.max(2, ((option.co2_kg ?? 0) / maxCo2) * 100) : 2
  const saved = Math.max(0, baselineCo2 - (option.co2_kg ?? 0))

  return (
    <article className={`mode ${recommended ? 'mode--best' : ''} ${chosen ? 'mode--chosen' : ''}`}>
      {recommended && <span className="mode__badge">Polecane</span>}
      {chosen && <span className="mode__badge mode__badge--chosen">Twój wybór</span>}
      <header className="mode__head">
        <span className="mode__icon" aria-hidden>{option.icon}</span>
        <h3>{option.label}</h3>
        <span className="mode__score" title="Dopasowanie do Twojego priorytetu">{Math.round(option.score ?? 0)}</span>
      </header>

      <dl className="mode__stats">
        <div><dt>Czas</dt><dd>{formatDuration(option.duration_min)}</dd></div>
        <div><dt>Koszt</dt><dd>{formatPln(option.cost_pln)}</dd></div>
        <div><dt>CO₂</dt><dd>{formatKg(option.co2_kg)}</dd></div>
      </dl>

      <div className="co2bar" aria-hidden>
        <div className="co2bar__fill" style={{ width: `${co2Width}%` }} />
      </div>

      <footer className="mode__foot">
        {option.note ? (
          <span className="mode__warn">⚠️ {option.note}</span>
        ) : saved > 0 ? (
          <span className="mode__saved">−{saved.toFixed(1)} kg CO₂ vs. auto solo</span>
        ) : (
          <span />
        )}
        {onChoose && (
          <button className="btn btn--small" onClick={onChoose} disabled={busy}>
            Jadę tym
          </button>
        )}
      </footer>
    </article>
  )
}
