# 🌿 EcoRoute — planer podróży, który liczy czas, pieniądze i CO₂

Full-stack MVP: planujesz podróż (skąd → dokąd, kiedy, ile osób, co jest najważniejsze),
a aplikacja porównuje **9 środków transportu**, sprawdza **prognozę pogody na godzinę wyjazdu**,
poleca najlepszą opcję i wyjaśnia dlaczego. Po odbyciu przejazdu zbierasz **eko-punkty**
za CO₂ zaoszczędzone względem jazdy samochodem w pojedynkę. **Doradca AI** podpowiada,
jak się przygotować do drogi.

## 🎬 Demo

![Demo EcoRoute](docs/demo.gif)

Wersja w lepszej jakości: [docs/demo.mp4](docs/demo.mp4) · zrzut ekranu: [docs/screenshot.png](docs/screenshot.png)

Na nagraniu: przegląd podróży → porównanie środków transportu → nowa podróż z autouzupełnianiem
miast i wyborem priorytetu → porada doradcy → „Jadę tym” i naliczenie eko-punktów → filtrowanie,
edycja i usuwanie.

> Nagranie powstało w środowisku bez dostępu do internetu, dlatego widać „Prognoza niedostępna”
> i doradcę w trybie regułowym. Z internetem pojawia się prognoza z Open-Meteo, a z kluczem API — porada od Claude.

| Warstwa | Technologia |
|---|---|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2, Pydantic 2 |
| Baza | SQLite (plik `ecoroute.db`, tworzony automatycznie) lub in-memory (`DATABASE_URL=sqlite://`) |
| Frontend | React 19 + TypeScript + Vite (bez bibliotek UI — własny CSS) |
| Zewnętrzne API | Open-Meteo (pogoda + geokodowanie, darmowe, bez klucza), opcjonalnie Claude API |

---

## ✨ Creative twist

1. **Rekomendacja świadoma pogody** — jeśli o godzinie wyjazdu ma padać, wiać > 35 km/h, być mróz
   albo upał, rower / hulajnoga / spacer dostają karę w rankingu, a uzasadnienie mówi to wprost
   („Prognoza: deszcz, 4°C — rower, hulajnoga i spacer zostały ocenione niżej”).
2. **Priorytet podróżnego** — ⚖️ zrównoważony / 🌿 eko / ⚡ szybko / 💸 tanio zmienia wagi
   kryteriów (czas, koszt, CO₂). Ta sama trasa daje różne rekomendacje różnym osobom.
3. **Eko-punkty i poziomy** — 1 pkt za każdy kg CO₂ zaoszczędzony względem „każdy jedzie
   swoim autem” + 5 pkt bonusu za przejazd zeroemisyjny. Poziomy: 🌱 → 🌿 → 🌳 → 🌍.
   Tablica wyników stylizowana na tablicę odjazdów.
4. **Doradca AI (Claude)** — patrz niżej.

## 🤖 Jak działa AI — „deterministyczny silnik decyduje, model wyjaśnia”

Rekomendacja jest liczona **deterministycznie** (testowalna, powtarzalna, bez halucynacji).
Model językowy dostaje *wyłącznie* wyliczone już dane (trasa, opcje z czasem/kosztem/CO₂,
pogoda, uzasadnienie systemu, notatki użytkownika) i ma za zadanie przełożyć je na
krótką, praktyczną poradę: co zabrać, na co uważać, ile czasu zaplanować.

Prompt (`backend/app/services/ai_advisor.py`) wymusza m.in.:
- korzystanie tylko z przekazanych danych — **żadnych wymyślonych liczb, linii, cen**,
- niezmienianie rekomendacji systemu (model ją objaśnia, może wskazać jedną alternatywę),
- odpowiedź w ściśle określonym formacie JSON (`summary` + max 3 `tips`) — parsowanym
  odpornie nawet gdy model owinie go w markdown.

**Bez klucza API** (lub przy błędzie sieci / niepoprawnym JSON-ie) działa **doradca regułowy**
o tym samym kontrakcie — funkcja zawsze działa, a UI pokazuje źródło porady
(✨ AI / ⚙️ tryb regułowy).

---

## 🚀 Uruchomienie

Wymagania: **Python 3.11+** i **Node.js 20+**.

### 1. Backend (port 8000)

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Dokumentacja API (Swagger): <http://localhost:8000/docs>

Opcjonalnie — włączenie AI: skopiuj `backend/.env.example` do `backend/.env` i wpisz
`ANTHROPIC_API_KEY`. Bez klucza aplikacja działa w pełni (doradca regułowy).

### 2. Frontend (port 5173)

```bash
cd frontend
npm install
npm run dev
```

Otwórz <http://localhost:5173>. Adres API można zmienić zmienną `VITE_API_URL` (`frontend/.env.example`).

### Testy backendu

```bash
cd backend
pytest
```

17 testów: CRUD, walidacja, filtrowanie, logika rekomendacji (w tym kara za pogodę),
naliczanie punktów, konflikty (409), CORS, fallback geokodera. Testy używają bazy
in-memory i podmienionych zależności (pogoda, geokoder, AI) — nie wymagają internetu.

---

## 🧱 Architektura

```
ecoroute/
├── backend/
│   ├── app/
│   │   ├── main.py                  # składanie aplikacji, CORS, mapowanie wyjątków → HTTP
│   │   ├── core/config.py           # ustawienia ze zmiennych środowiskowych (.env)
│   │   ├── db.py                    # silnik SQLAlchemy, sesje
│   │   ├── models.py                # model ORM Trip
│   │   ├── schemas.py               # kontrakt API (Pydantic)
│   │   ├── api/
│   │   │   ├── deps.py              # wstrzykiwanie zależności (podmieniane w testach)
│   │   │   └── routes/              # trips.py (CRUD + akcje), meta.py (stats, places…)
│   │   ├── repositories/            # dostęp do danych — jedyne miejsce z SQL
│   │   └── services/                # logika domenowa, niezależna od FastAPI
│   │       ├── trip_service.py      # orkiestracja przypadków użycia
│   │       ├── transport.py         # katalog środków transportu, szacowanie czasu/kosztu/CO₂
│   │       ├── recommender.py       # ranking ważony priorytetem + kara pogodowa
│   │       ├── weather.py           # Open-Meteo, bez wyjątków przy braku sieci
│   │       ├── geocoding.py         # Open-Meteo + offline'owa lista miast jako fallback
│   │       ├── eco_points.py        # grywalizacja
│   │       └── ai_advisor.py        # Claude + doradca regułowy (ten sam interfejs)
│   └── tests/
└── frontend/
    └── src/
        ├── api/                     # typowany klient HTTP + typy odpowiadające schematom
        ├── hooks/useTrips.ts        # ładowanie listy i statystyk
        ├── components/              # StatsBar, TripList, TripForm, PlaceInput, TripDetail, ModeCard, AdvicePanel
        ├── utils/format.ts          # formatowanie (pl-PL)
        └── styles.css
```

Zasady: router → serwis → repozytorium; serwisy rzucają wyjątki domenowe
(`NotFoundError`, `ConflictError`, `DomainValidationError`), które `main.py` mapuje na 404/409/422.
Integracje zewnętrzne są za protokołami (`WeatherProvider`, `Geocoder`, `Advisor`), dzięki czemu
łatwo je podmienić w testach i żadna awaria zewnętrznego API nie wywraca aplikacji.

## 📡 API

| Metoda | Endpoint | Opis |
|---|---|---|
| GET | `/api/trips?status=planned\|completed` | lista podróży |
| POST | `/api/trips` | utworzenie (201 + nagłówek `Location`); dystans liczony na serwerze |
| GET | `/api/trips/{id}` | szczegóły |
| PATCH | `/api/trips/{id}` | częściowa edycja (zmiana miejsc przelicza dystans; 409 dla odbytych) |
| DELETE | `/api/trips/{id}` | usunięcie (204) |
| GET | `/api/trips/{id}/comparison` | porównanie środków transportu + pogoda + rekomendacja |
| POST | `/api/trips/{id}/complete` | `{ "mode": "train" }` — oznacz jako odbytą, nalicz punkty |
| POST | `/api/trips/{id}/advice` | porada doradcy (AI lub regułowa) |
| GET | `/api/stats` | eko-punkty, poziom, zaoszczędzone CO₂, ulubiony środek |
| GET | `/api/places?q=wroc` | podpowiedzi miejsc (autouzupełnianie) |
| GET | `/api/modes` | katalog środków transportu |
| GET | `/api/health` | status + czy AI jest włączone |

## 📐 Założenia modelu

- Dystans = odległość po łuku (haversine) × 1,25 (typowy współczynnik objazdu sieci drogowej).
- Prędkości, koszty i emisje to uśrednione wartości dla Polski (wskaźniki emisji wzorowane
  na EEA / UK DESNZ) — służą do **porównania** opcji, nie do sprzedaży biletów.
- Samochód: emisja i koszt liczone na pojazd (do 5 osób); wspólny przejazd: koszt i emisja
  dzielone na 3 osoby (realistyczne średnie obłożenie).
- Każdy środek ma zakres sensownego dystansu (np. pieszo ≤ 6 km, samolot ≥ 300 km).
- Prognoza pogody jest dostępna ok. 15 dni naprzód; dla dalszych dat rekomendacja pomija pogodę.

## 🧠 Jak korzystałem z narzędzi AI

- **Claude (agent z dostępem do terminala)** — przekazałem mu treść zadania jako prompt
  ([docs/ai/prompt-zadania.md](docs/ai/prompt-zadania.md)). Agent zaproponował pomysł i architekturę,
  wygenerował kod backendu i frontendu, napisał testy, a potem sam zweryfikował działanie:
  uruchomił `pytest`, `tsc` + build, lint (`oxlint`) i przeklikał aplikację w przeglądarce (Playwright).
  Na tym etapie poprawił m.in. skalę eko-punktów (pierwsza wersja dawała ~900 pkt za jeden przejazd),
  normalizację rankingu (skala logarytmiczna, żeby samolot nie „spłaszczał” różnic między innymi opcjami)
  oraz efekty Reacta zgłaszane przez linter.
- **Claude** pomógł mi też uruchomić projekt lokalnie, wrzucić go na GitHuba i nagrać to demo.
- **Konfiguracja agentów:** [AGENTS.md](AGENTS.md) spisuje zasady architektury, stylu kodu i
  „definicję gotowe” (testy + build + lint), których mają się trzymać narzędzia AI przy dalszej pracy
  nad repozytorium.
- **AI w samej aplikacji:** doradca podróży (Claude API) — opis podejścia w sekcji
  „Jak działa AI” powyżej.

<!-- TODO (Ostap): dopisz własnymi słowami, co zrobiłeś sam — np. co sprawdziłeś, zmieniłeś,
     czego się nauczyłeś. Usuń ten komentarz przed wysłaniem. -->

## 🔭 Co dalej (poza zakresem MVP)

Prawdziwe trasy i rozkłady (OSRM / GTFS / API PKP), konta użytkowników, wspólne przejazdy
z zapraszaniem znajomych, migracje bazy (Alembic), testy E2E frontendu (Playwright).
