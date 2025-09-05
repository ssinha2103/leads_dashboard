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

Google Drive Ingest

If you prefer to share a Google Drive link (file or folder) instead of committing data locally, the app can download, ingest, and clean up automatically.

- One-time on boot via `.env`:

  - `INGEST_ON_START=1`
  - `INGEST_GDRIVE_URL=https://drive.google.com/file/d/<id>/view` (or a folder link)
  - Optional: `INGEST_GLOB=all` (default), e.g. `**/*.csv`

On startup, Django will use `ingest_gdrive` to download to a temporary subfolder under `data/`, extract archives if needed, ingest into Postgres, and then clean up the temporary files. The `data/` folder is already in `.gitignore`, so nothing is added to the repo.

You can also run it manually inside the web container:

`docker compose exec web python manage.py ingest_gdrive --url "<gdrive_link>" --glob all`

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

GCP Deployment (Cloud Run)

Overview
- Container image builds in GitHub Actions on merge to `master`.
- Image pushes to Artifact Registry, then deploys to Cloud Run.
- App connects to Cloud SQL (Postgres) via Cloud Run attachment.

Bootstrap GCP (one time)
- Install gcloud locally and authenticate to your GCP project.
- Run:
  - `bash scripts/gcp_bootstrap.sh <PROJECT_ID> <REGION> <SERVICE_NAME> <ARTIFACT_REPO> <SQL_INSTANCE_NAME> <DB_NAME> <DB_USER> <DB_PASSWORD>`
  - Save the printed Cloud SQL connection name (format: `project:region:instance`).

GitHub Secrets (repository settings)
- `GCP_PROJECT_ID`: your project ID
- `GCP_SA_KEY`: JSON for a service account with roles: Artifact Registry Writer, Cloud Run Admin, Cloud SQL Client
- `CLOUD_RUN_REGION`: e.g., `us-central1`
- `CLOUD_RUN_SERVICE`: e.g., `leads-dashboard`
- `ARTIFACT_REPO`: Artifact Registry repo name, e.g., `leads-dashboard`
- `CLOUD_SQL_INSTANCE`: Cloud SQL connection name `project:region:instance`
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`: Postgres credentials
- `DJANGO_SECRET_KEY`: a strong random string
- `ALLOWED_HOSTS`: Cloud Run URL host or your domain (comma separated)
- Optional: `INGEST_ON_START`, `INGEST_GDRIVE_URL`, `INGEST_GLOB`

Deploy
- Push to `master`; the workflow `.github/workflows/deploy.yml` builds and deploys automatically.
- The service URL is printed in the job logs or can be retrieved via `gcloud run services describe`.

Notes
- The container uses Gunicorn in Cloud Run (`USE_GUNICORN=1`).
- Static files are served via WhiteNoise; they’re collected during build.
- Database sockets are mounted at `/cloudsql/<connectionName>`; env `DB_HOST` is set accordingly by the workflow.
