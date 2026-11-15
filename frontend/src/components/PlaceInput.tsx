import { useEffect, useId, useRef, useState } from 'react'
import { api } from '../api/client'
import type { Place, PlaceSuggestion } from '../api/types'

interface Props {
  label: string
  value: Place | null
  onChange: (p: Place | null) => void
  placeholder?: string
}

/** Text input with debounced place autocomplete (backed by /api/places). */
export function PlaceInput({ label, value, onChange, placeholder }: Props) {
  const id = useId()
  const [query, setQuery] = useState(value?.name ?? '')
  const [suggestions, setSuggestions] = useState<PlaceSuggestion[]>([])
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const skipNext = useRef(false)

  useEffect(() => {
    if (skipNext.current) {
      skipNext.current = false
      return
    }
    if (query.trim().length < 2) return
    const ctrl = new AbortController()
    const timer = setTimeout(() => {
      api
        .searchPlaces(query.trim(), ctrl.signal)
        .then((s) => {
          setSuggestions(s)
          setActive(0)
          setOpen(true)
        })
        .catch(() => setSuggestions([]))
    }, 250)
    return () => {
      clearTimeout(timer)
      ctrl.abort()
    }
  }, [query])

  const pick = (s: PlaceSuggestion) => {
    skipNext.current = true
    setQuery(s.name)
    setOpen(false)
    onChange({ name: s.name, lat: s.lat, lon: s.lon })
  }

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (!open || suggestions.length === 0) return
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActive((a) => (a + 1) % suggestions.length)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActive((a) => (a - 1 + suggestions.length) % suggestions.length)
    } else if (e.key === 'Enter') {
      e.preventDefault()
      pick(suggestions[active])
    } else if (e.key === 'Escape') {
      setOpen(false)
    }
  }

  return (
    <div className="field place">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        value={query}
        placeholder={placeholder}
        autoComplete="off"
        role="combobox"
        aria-expanded={open}
        aria-invalid={query.length > 0 && !value}
        onChange={(e) => {
          setQuery(e.target.value)
          if (e.target.value.trim().length < 2) setSuggestions([])
          onChange(null) // typed text is not a confirmed place until picked
        }}
        onKeyDown={onKeyDown}
        onFocus={() => suggestions.length && setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
      />
      {value && <span className="place__ok" title={`${value.lat.toFixed(3)}, ${value.lon.toFixed(3)}`}>✓</span>}
      {open && suggestions.length > 0 && (
        <ul className="suggestions" role="listbox">
          {suggestions.map((s, i) => (
            <li
              key={`${s.name}-${s.lat}-${s.lon}`}
              role="option"
              aria-selected={i === active}
              className={i === active ? 'active' : ''}
              onMouseDown={() => pick(s)}
            >
              <strong>{s.name}</strong>
              <span>{[s.region, s.country].filter(Boolean).join(', ')}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
