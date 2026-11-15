import type { Priority } from '../api/types'

export const PRIORITY_LABELS: Record<Priority, { label: string; icon: string; hint: string }> = {
  balanced: { label: 'Zrównoważony', icon: '⚖️', hint: 'czas, koszt i CO₂ po równo' },
  eco: { label: 'Eko', icon: '🌿', hint: 'najmniej CO₂' },
  fast: { label: 'Szybko', icon: '⚡', hint: 'najkrótszy czas' },
  cheap: { label: 'Tanio', icon: '💸', hint: 'najniższy koszt' },
}

const dateFmt = new Intl.DateTimeFormat('pl-PL', {
  weekday: 'short',
  day: 'numeric',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit',
})

export const formatDate = (iso: string) => dateFmt.format(new Date(iso))

export function formatDuration(min: number | null): string {
  if (min == null) return '—'
  if (min < 60) return `${min} min`
  const h = Math.floor(min / 60)
  const m = min % 60
  return m ? `${h} h ${m} min` : `${h} h`
}

export const formatPln = (v: number | null) =>
  v == null ? '—' : v === 0 ? '0 zł' : `${v.toFixed(2).replace('.', ',')} zł`

export const formatKg = (v: number | null) =>
  v == null ? '—' : `${v.toLocaleString('pl-PL', { maximumFractionDigits: 2 })} kg`

/** ISO string -> value for <input type="datetime-local"> in local time. */
export function toLocalInput(iso: string): string {
  const d = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export function defaultDeparture(): string {
  const d = new Date(Date.now() + 60 * 60 * 1000)
  d.setMinutes(0, 0, 0)
  return toLocalInput(d.toISOString())
}
