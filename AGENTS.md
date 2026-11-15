# AGENTS.md — instrukcje dla agentów AI (Claude Code, Cursor, Copilot…)

Ten plik opisuje zasady, których mają się trzymać narzędzia AI pracujące nad tym repozytorium.
Spisuje konwencje, według których powstał projekt, żeby kolejne zmiany były z nimi spójne.

## Projekt w skrócie
EcoRoute — planer podróży (full-stack MVP). Backend: FastAPI + SQLAlchemy 2 + SQLite (`backend/`).
Frontend: React 19 + TypeScript + Vite, bez bibliotek UI (`frontend/`). Szczegóły w `README.md`.

## Architektura — zasady nienaruszalne
- Backend ma warstwy: `api/routes` → `services` → `repositories`. Router nie zawiera logiki
  biznesowej ani SQL; serwis nie importuje FastAPI; SQL tylko w repozytoriach.
- Błędy domenowe to wyjątki z `services/trip_service.py` (`NotFoundError`, `ConflictError`,
  `DomainValidationError`) — mapowane na HTTP w `main.py`. Nie rzucaj `HTTPException` z serwisów.
- Integracje zewnętrzne (pogoda, geokodowanie, AI) są za protokołami i wstrzykiwane przez
  `api/deps.py`. Awaria zewnętrznego API **nigdy** nie może wywrócić endpointu — zawsze fallback.
- Rekomendację liczy deterministyczny kod (`recommender.py`). LLM tylko ją **wyjaśnia** — nie
  przekazuj modelowi decyzji i nie pozwalaj mu podawać liczb spoza przekazanych danych.
- Kontrakt API = `schemas.py`. Każda zmiana schematu wymaga aktualizacji `frontend/src/api/types.ts`.

## Styl kodu
- Python: type hints wszędzie, docstring na poziomie modułu, nazwy po angielsku.
  Teksty widoczne dla użytkownika (komunikaty błędów, uzasadnienia) — po polsku.
- TypeScript: `strict`, bez `any`; wywołania HTTP tylko przez `src/api/client.ts`.
- React: komponenty funkcyjne, stan pochodny wyliczaj w renderze zamiast synchronizować go
  w `useEffect` (lint `react(set-state-in-effect)` musi być czysty).
- CSS: zmienne z `:root` w `styles.css`, klasy w konwencji BEM-like (`block__element--modifier`).
- Bez nowych zależności, jeśli zadanie da się zrobić standardową biblioteką.

## Definicja „gotowe”
Przed zakończeniem zadania uruchom i upewnij się, że przechodzą:
```bash
cd backend && pytest                       # wszystkie testy zielone
cd frontend && npm run build && npm run lint   # tsc + build + oxlint bez ostrzeżeń
```
Nowa logika w backendzie = nowy test w `backend/tests/` (testy nie mogą wymagać internetu —
używaj podmian zależności z `tests/conftest.py`).

## Czego nie robić
- Nie commituj `.env`, kluczy API, `*.db`, `node_modules`, `.venv`.
- Nie zmieniaj współczynników w `transport.py` bez aktualizacji sekcji „Założenia modelu” w README.
- Nie dodawaj zależności od zewnętrznego serwera bazy danych — projekt ma się uruchamiać lokalnie
  bez konfiguracji.
