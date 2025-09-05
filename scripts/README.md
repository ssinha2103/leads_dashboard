Scripts Command Guide

This guide lists copy‑paste commands for local development and Google Cloud deployment using the helper scripts in this folder, tailored to your repo and project.

Prerequisites
- Docker and Docker Compose for local.
- Google Cloud SDK (or use Cloud Shell) for GCP commands.
- GitHub CLI `gh` (optional) to set repo secrets from the command line.

Where to run these commands?
- You do NOT need to create a VM for Cloud Run. Cloud Run is serverless; it runs your container for you.
- Option A (recommended): Google Cloud Shell (browser‑based, gcloud preinstalled)
  - Open https://console.cloud.google.com and click “Activate Cloud Shell”.
  - Clone your repo and enter it:
    `git clone https://github.com/ssinha2103/leads_dashboard.git && cd leads_dashboard`
  - Ensure you’re using the right project:
    `gcloud config set project click-it-3d06c`
- Option B: Your local machine
  - Install the Google Cloud SDK: https://cloud.google.com/sdk/docs/install
  - Clone and enter the repo:
    `git clone https://github.com/ssinha2103/leads_dashboard.git && cd leads_dashboard`
  - Login and set the project:
    `gcloud auth login && gcloud config set project click-it-3d06c`

Local Development (Docker Compose)
- Start (attached):
  `bash scripts/run.sh up`
- Start (detached):
  `bash scripts/run.sh up-d`
- Logs:
  `bash scripts/run.sh logs`
- Stop:
  `bash scripts/run.sh down`
- Migrate:
  `bash scripts/run.sh migrate`
- Create admin user:
  `bash scripts/run.sh superuser`
- Ingest local folder (CSV/XLSX):
  `bash scripts/run.sh ingest --root "data/USA Database Business Leads" --glob all`
- Ingest from Google Drive (file or folder link):
  `bash scripts/run.sh ingest-gdrive --url "<your_gdrive_link>" --glob all`

GCP Bootstrap (one‑time)
Use these exact values for your setup:
`export PROJECT_ID="click-it-3d06c"`
`export REGION="us-central1"`  # Use regions, not zones like us-central1-c
`export SERVICE_NAME="leads-dashboard"`
`export ARTIFACT_REPO="leads-dashboard"`
`export SQL_INSTANCE_NAME="leads-prod-sql"`
`export DB_NAME="leads"`
`export DB_USER="leads"`
`export DB_PASSWORD="<STRONG_PASSWORD>"`  # choose a password or: export DB_PASSWORD="$(openssl rand -base64 24)"

Create Artifact Registry + Cloud SQL (Postgres):
`bash scripts/gcp_bootstrap.sh "$PROJECT_ID" "$REGION" "$SERVICE_NAME" "$ARTIFACT_REPO" "$SQL_INSTANCE_NAME" "$DB_NAME" "$DB_USER" "$DB_PASSWORD"`

Get the Cloud SQL connection name (used by CI/CD and Cloud Run):
`CONN=$(gcloud sql instances describe "$SQL_INSTANCE_NAME" --project "$PROJECT_ID" --format='value(connectionName)'); echo "$CONN"`

Create Deploy Service Account (one‑time)
`gcloud iam service-accounts create deployer --project "$PROJECT_ID"`
`gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:deployer@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/run.admin"`
`gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:deployer@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/artifactregistry.writer"`
`gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:deployer@${PROJECT_ID}.iam.gserviceaccount.com" --role="roles/cloudsql.client"`

Configure GitHub Actions (Workload Identity Federation)
Create a WIF pool/provider for this repo (owner/repo = ssinha2103/leads_dashboard):
`bash scripts/setup_wif.sh "$PROJECT_ID" github-pool github-provider ssinha2103 leads_dashboard deployer@${PROJECT_ID}.iam.gserviceaccount.com`

Compute the WIF provider resource string and save the two values for GitHub Secrets:
`PN=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')`
`WIP="projects/${PN}/locations/global/workloadIdentityPools/github-pool/providers/github-provider"`
`echo "$WIP"`
`echo "deployer@${PROJECT_ID}.iam.gserviceaccount.com"`

Set GitHub Secrets (UI or CLI)
Option A — GitHub UI: Repo → Settings → Secrets and variables → Actions → “New repository secret”. Add the following keys and values.

Option B — GitHub CLI: run these commands locally or in Cloud Shell with `gh auth login` first. The `-R` flag targets your repo directly.

- Core:
`gh secret set -R ssinha2103/leads_dashboard GCP_PROJECT_ID -b "$PROJECT_ID"`
`gh secret set -R ssinha2103/leads_dashboard CLOUD_RUN_REGION -b "$REGION"`
`gh secret set -R ssinha2103/leads_dashboard CLOUD_RUN_SERVICE -b "$SERVICE_NAME"`
`gh secret set -R ssinha2103/leads_dashboard ARTIFACT_REPO -b "$ARTIFACT_REPO"`
`gh secret set -R ssinha2103/leads_dashboard CLOUD_SQL_INSTANCE -b "$CONN"`
`gh secret set -R ssinha2103/leads_dashboard DB_NAME -b "$DB_NAME"`
`gh secret set -R ssinha2103/leads_dashboard DB_USER -b "$DB_USER"`
`gh secret set -R ssinha2103/leads_dashboard DB_PASSWORD -b "$DB_PASSWORD"`
`gh secret set -R ssinha2103/leads_dashboard DJANGO_SECRET_KEY -b "$(openssl rand -base64 50)"`
`gh secret set -R ssinha2103/leads_dashboard ALLOWED_HOSTS -b "*"`

- Auth (WIF):
`gh secret set -R ssinha2103/leads_dashboard WORKLOAD_IDENTITY_PROVIDER -b "$WIP"`
`gh secret set -R ssinha2103/leads_dashboard SERVICE_ACCOUNT_EMAIL -b "deployer@${PROJECT_ID}.iam.gserviceaccount.com"`

- Optional (ingest on first start):
`gh secret set -R ssinha2103/leads_dashboard INGEST_ON_START -b "1"`
`gh secret set -R ssinha2103/leads_dashboard INGEST_GDRIVE_URL -b "https://drive.google.com/drive/folders/123SJA6T-seFwKSEP4HMm4FTjr2nbq93G?%20usp=sharing"`
`gh secret set -R ssinha2103/leads_dashboard INGEST_GLOB -b "all"`

Trigger CI/CD Deploy
- Push to master to build and deploy automatically. From your dev machine:
`git push origin master`

Post‑Deploy
- Get service URL from Cloud Run UI or workflow logs.
- Tighten ALLOWED_HOSTS to that hostname and update the secret:
`gh secret set -R ssinha2103/leads_dashboard ALLOWED_HOSTS -b "<your-cloud-run-hostname>"`
`git commit --allow-empty -m "bump deploy" && git push`

Optional: Run on a VM instead of Cloud Run (not recommended)
- Only if you explicitly want a VM: create a Compute Engine VM, SSH in, install Docker, clone the repo, and run `bash scripts/run.sh up-d`.
- This bypasses Cloud Run and CI/CD; you’ll manage uptime, scaling, and updates yourself.


