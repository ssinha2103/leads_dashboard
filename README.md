Leads Dashboard (Dockerized Django)

A minimal MVP implementing the Explore dashboard for searching and filtering large CSV-based business lead datasets. It ingests CSVs from the `data/` folder into Postgres and exposes a simple, fast dashboard UI.

Quick Start

- Requirements: Docker + Docker Compose
- Start the stack:

`bash scripts/run.sh up`

This builds images, starts Postgres and Django, and serves http://localhost:8000.

Ingest Data

The default dataset root is `data/USA Database Business Leads`. You can trigger ingestion in two ways:

1) One-time on boot by enabling in `.env`:

`INGEST_ON_START=1`

2) Run manually with the helper script:

`bash scripts/run.sh ingest --root "data/USA Database Business Leads"`

The ingestor tracks per-file hash, size, and timestamps in `SourceFile`; it only re-processes when the file content changes.

Explore UI

- Explore at http://localhost:8000/leads/
- Filters: Category, State, City, Has Email, Has Website.
- Search: name/domain/email substring.
- Sorting: name, score, state, city.
- Export: current result set to CSV (capped at 10k rows).
- Saved views: save current filters for quick access.

Schema

Key tables (see `leads/models.py`):
- `State`, `City`, `Category`
- `Source`, `SourceFile` (per-file metadata with hash)
- `Lead` (business_name, website, email, phone, address, domain, quality_score, JSON `extra`)
- `Tag`, `LeadTag`, `SavedView`

Uniqueness is enforced on lowercased email, and on (lower(domain), city, state) when domain is present.

Notes

- The UI uses Tailwind via CDN; no Node install required.
- Initial focus is a working dashboard; outreach, auth, and admin features can follow.
- Dataset variance is handled with flexible column mapping; unmapped fields are stored in `Lead.extra`.

Common Commands

`bash scripts/run.sh up-d` — start in detached mode

`bash scripts/run.sh logs` — tail logs

`bash scripts/run.sh migrate` — run makemigrations + migrate

`bash scripts/run.sh superuser` — create an admin user


Run full-root ingest now

Start services (detached): `bash scripts/run.sh up-d`
Kick off full ingest (CSV + XLSX): `bash scripts/run.sh ingest --root "data/USA Database Business Leads" --glob all`
