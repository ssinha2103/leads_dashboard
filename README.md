Leads Dashboard — Scripts and GCP Deployment Guide

Overview
This Django app ingests CSV/XLSX business lead datasets into Postgres and provides a fast UI for search, filters, and export. It is containerized for local development and ships with scripts to bootstrap and deploy to Google Cloud Run with Cloud SQL.

Scripts
1) scripts/run.sh
- Purpose: local dev lifecycle and ingestion helpers (Docker Compose).
- Commands:
  - `up`: build and start stack (attached)
  - `up-d`: build and start detached
  - `down`: stop the stack
  - `build`: rebuild images
  - `logs`: tail logs
  - `ps`: show service status
  - `migrate`: run makemigrations + migrate inside the container
  - `ingest [--root PATH] [--glob GLOB] [--limit N]`: ingest from local folder (CSV/XLSX). Defaults: `root="data/USA Database Business Leads"`, `glob="all"`.
  - `ingest-gdrive --url URL [--glob GLOB] [--keep] [--out-dir DIR]`: download a Google Drive file/folder, ingest, then clean up (unless `--keep`).
  - `superuser`: create a Django superuser.

2) scripts/gcp_bootstrap.sh
- Purpose: one‑time creation of core GCP resources for this app.
- Creates: Artifact Registry repo (Docker), Cloud SQL Postgres instance, database, and user.
- Usage:
  - `bash scripts/gcp_bootstrap.sh <PROJECT_ID> <REGION> <SERVICE_NAME> <ARTIFACT_REPO> <SQL_INSTANCE_NAME> <DB_NAME> <DB_USER> <DB_PASSWORD>`
- Notes:
  - REGION must be a region (e.g., `us-central1`), not a zone (e.g., `us-central1-c`).
  - Requires `gcloud` (use Cloud Shell or install SDK).
  - Prints the Cloud SQL “Instance connection name” used by Cloud Run and CI.

3) scripts/setup_wif.sh
- Purpose: configure Workload Identity Federation (WIF) for keyless GitHub Actions deploys.
- Usage:
  - `bash scripts/setup_wif.sh <PROJECT_ID> <POOL> <PROVIDER> <GITHUB_OWNER> <GITHUB_REPO> <SERVICE_ACCOUNT_EMAIL>`
- What it does:
  - Creates a WIF pool and OIDC provider for GitHub.
  - Grants your GitHub repo permission to impersonate the deploy Service Account.
  - Outputs two values to add as GitHub secrets: `WORKLOAD_IDENTITY_PROVIDER`, `SERVICE_ACCOUNT_EMAIL`.

Local Development
- Requirements: Docker + Docker Compose
- Start app: `bash scripts/run.sh up` (http://localhost:8000)
- Ingest local folder: `bash scripts/run.sh ingest --root "data/USA Database Business Leads" --glob all`
- Ingest from Google Drive: `bash scripts/run.sh ingest-gdrive --url "<gdrive_link>" --glob all`
- Create admin: `bash scripts/run.sh superuser`

Deploy to GCP (Cloud Run + Cloud SQL)
Why this stack
- Cloud Run: serverless containers with autoscaling and HTTPS — minimal ops.
- Cloud SQL (Postgres): fits relational filters and substring search (pg_trgm GIN indexes).
- Artifact Registry: first‑party container registry with IAM.
- GitHub Actions + WIF: keyless CI/CD (no JSON key secrets).

Step‑by‑step
1) Bootstrap GCP resources (run once)
- Open Cloud Shell (https://console.cloud.google.com → “Activate Cloud Shell”).
- Choose values (example):
  - PROJECT_ID: your project id (e.g., `click-it-3d06c`)
  - REGION: a GCP region (e.g., `us-central1`)
  - SERVICE_NAME: Cloud Run service name (e.g., `leads-dashboard`)
  - ARTIFACT_REPO: Artifact Registry repo (e.g., `leads-dashboard`)
  - SQL_INSTANCE_NAME: Cloud SQL instance (e.g., `leads-prod-sql`)
  - DB_NAME/DB_USER: `leads` / `leads`
  - DB_PASSWORD: strong password
- Run:
  - `bash scripts/gcp_bootstrap.sh $PROJECT_ID $REGION $SERVICE_NAME $ARTIFACT_REPO $SQL_INSTANCE_NAME $DB_NAME $DB_USER "$DB_PASSWORD"`
- Copy the printed Cloud SQL “Instance connection name” (format `project:region:instance`).

2) Create deploy Service Account and grant roles (run once)
- `gcloud iam service-accounts create deployer --project $PROJECT_ID`
- Grant roles on the project: `roles/run.admin`, `roles/artifactregistry.writer`, `roles/cloudsql.client`.
- Example:
  - `gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:deployer@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/run.admin"`
  - Repeat for the other two roles above.

3) Configure keyless CI/CD with WIF (recommended)
- Run:
  - `bash scripts/setup_wif.sh $PROJECT_ID github-pool github-provider <GITHUB_OWNER> <GITHUB_REPO> deployer@$PROJECT_ID.iam.gserviceaccount.com`
- Save outputs as GitHub repository secrets:
  - `WORKLOAD_IDENTITY_PROVIDER`
  - `SERVICE_ACCOUNT_EMAIL`

4) Add GitHub Secrets (Repo → Settings → Secrets and variables → Actions)
- Required:
  - `GCP_PROJECT_ID`: your project id
  - `CLOUD_RUN_REGION`: e.g., `us-central1`
  - `CLOUD_RUN_SERVICE`: e.g., `leads-dashboard`
  - `ARTIFACT_REPO`: e.g., `leads-dashboard`
  - `CLOUD_SQL_INSTANCE`: connection name from step 1
  - `DB_NAME`, `DB_USER`, `DB_PASSWORD`: Postgres credentials
  - `DJANGO_SECRET_KEY`: `openssl rand -base64 50`
  - `ALLOWED_HOSTS`: `*` initially; later set to your Cloud Run URL
- Auth (WIF):
  - `WORKLOAD_IDENTITY_PROVIDER`, `SERVICE_ACCOUNT_EMAIL` (from step 3)
- Optional (first‑run ingestion):
  - `INGEST_ON_START=1`
  - `INGEST_GDRIVE_URL=<your Google Drive link>` (file or folder)
  - `INGEST_GLOB=all`

5) Deploy via GitHub Actions
- Push/merge to `master`.
- Workflow `.github/workflows/deploy.yml` will:
  - Authenticate to GCP using WIF.
  - Build Docker image and push to Artifact Registry.
  - Deploy to Cloud Run with Cloud SQL attached and env vars set.
- Find the service URL in job output or the Cloud Run UI. Add that host to `ALLOWED_HOSTS` and push again to tighten.

Operational Notes
- Production server: Gunicorn (`USE_GUNICORN=1`) with WhiteNoise for static files.
- Database socket: `/cloudsql/<connectionName>` is mounted by Cloud Run; `DB_HOST` is set accordingly by the workflow.
- Ingestion: `ingest_gdrive` downloads to a temp subfolder under `data/`, extracts archives, ingests, then cleans up by default.

Troubleshooting
- gcloud not found: use Cloud Shell or install the SDK (https://cloud.google.com/sdk/docs/install).
- Region vs zone: use regions like `us-central1`, not zones like `us-central1-c`.
- Permission errors: ensure deployer SA has `run.admin`, `artifactregistry.writer`, `cloudsql.client` on the project.
- Large datasets: consider running ingestion one‑off (not on every deploy) or via a Cloud Run Job.

FAQ
- Should we use NoSQL? Not here. Relational filters + substring search are best served by Postgres with trigram (pg_trgm) GIN indexes.

