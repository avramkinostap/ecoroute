import type { Stats, TransportModeInfo } from '../api/types'

interface Props {
  stats: Stats | null
  modes: Record<string, TransportModeInfo>
}

export function StatsBar({ stats, modes }: Props) {
  const points = stats?.eco_points ?? 0
  const progress = stats?.next_level_at ? Math.min(100, (points / stats.next_level_at) * 100) : 100
  const fav = stats?.favourite_mode ? modes[stats.favourite_mode] : null

  return (
    <section className="board" aria-label="Twoje eko-statystyki">
      <div className="board__cell">
        <span className="board__label">Eko-punkty</span>
        <span className="board__value">{String(points).padStart(4, '0')}</span>
      </div>
      <div className="board__cell">
        <span className="board__label">Zaoszczędzone CO₂</span>
        <span className="board__value">
          {(stats?.co2_saved_kg ?? 0).toFixed(1)}
          <small> kg</small>
        </span>
      </div>
      <div className="board__cell">
        <span className="board__label">Przejazdy</span>
        <span className="board__value">
          {stats?.completed_trips ?? 0}
          <small>/{stats?.total_trips ?? 0}</small>
        </span>
      </div>
      <div className="board__cell board__cell--wide">
        <span className="board__label">
          Poziom {fav && <>· ulubiony: {fav.icon} {fav.label}</>}
        </span>
        <span className="board__level">{stats?.level ?? '🌱 Nowicjusz'}</span>
        <div className="progress" title={stats?.next_level_at ? `Następny poziom: ${stats.next_level_at} pkt` : 'Maksymalny poziom'}>
          <div className="progress__bar" style={{ width: `${progress}%` }} />
        </div>
      </div>
    </section>
  )
}
