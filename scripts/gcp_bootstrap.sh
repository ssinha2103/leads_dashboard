#!/usr/bin/env bash
set -euo pipefail

# Bootstrap GCP resources for Cloud Run + Artifact Registry + Cloud SQL (Postgres)
# Usage:
#   scripts/gcp_bootstrap.sh <PROJECT_ID> <REGION> <SERVICE_NAME> <ARTIFACT_REPO> <SQL_INSTANCE_NAME> <DB_NAME> <DB_USER> <DB_PASSWORD>

PROJECT_ID=${1:?PROJECT_ID required}
REGION=${2:?REGION required (e.g. us-central1)}
SERVICE=${3:?SERVICE_NAME required}
REPO=${4:?ARTIFACT_REPO required}
SQL_INSTANCE=${5:?SQL_INSTANCE_NAME required}
DB_NAME=${6:?DB_NAME required}
DB_USER=${7:?DB_USER required}
DB_PASSWORD=${8:?DB_PASSWORD required}

if ! command -v gcloud >/dev/null 2>&1; then
  echo "Error: gcloud (Google Cloud CLI) is not installed or not on PATH." >&2
  echo "Install options:" >&2
  echo "- Cloud Shell (recommended quick start): open console.cloud.google.com and click 'Activate Cloud Shell' then rerun this script." >&2
  echo "- macOS:   brew install --cask google-cloud-sdk" >&2
  echo "- Debian/Ubuntu: sudo apt-get update && sudo apt-get install google-cloud-sdk" >&2
  echo "Docs: https://cloud.google.com/sdk/docs/install" >&2
  exit 127
fi

# Prevent zone values like us-central1-c. Cloud Run, Artifact Registry, and Cloud SQL expect regions (e.g., us-central1)
if [[ "$REGION" =~ -[a-z]$ ]]; then
  CANDIDATE=${REGION%-[a-z]}
  echo "Error: REGION looks like a zone ('$REGION'). Use a region such as '$CANDIDATE' (e.g., us-central1)." >&2
  exit 2
fi

echo "Enabling APIs..."
gcloud services enable run.googleapis.com artifactregistry.googleapis.com sqladmin.googleapis.com iam.googleapis.com --project "$PROJECT_ID"

echo "Creating Artifact Registry repo (if not exists)..."
if ! gcloud artifacts repositories describe "$REPO" --location="$REGION" --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$REPO" \
    --location="$REGION" --repository-format=DOCKER \
    --project "$PROJECT_ID"
fi

echo "Creating Cloud SQL Postgres instance (if not exists)..."
if ! gcloud sql instances describe "$SQL_INSTANCE" --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud sql instances create "$SQL_INSTANCE" \
    --database-version=POSTGRES_15 \
    --cpu=1 --memory=3840MiB \
    --region="$REGION" \
    --project "$PROJECT_ID"
fi

echo "Creating database (if not exists)..."
if ! gcloud sql databases describe "$DB_NAME" --instance="$SQL_INSTANCE" --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud sql databases create "$DB_NAME" --instance="$SQL_INSTANCE" --project "$PROJECT_ID"
fi

echo "Creating user (if not exists)..."
if ! gcloud sql users list --instance="$SQL_INSTANCE" --project "$PROJECT_ID" --filter="name:$DB_USER" --format="value(name)" | grep -q "^$DB_USER$"; then
  gcloud sql users create "$DB_USER" --instance="$SQL_INSTANCE" --password="$DB_PASSWORD" --project "$PROJECT_ID"
else
  gcloud sql users set-password "$DB_USER" --instance="$SQL_INSTANCE" --password="$DB_PASSWORD" --project "$PROJECT_ID"
fi

echo "Granting Cloud SQL Client to default Compute service account for Cloud Run..."
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
RUN_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$RUN_SA" \
  --role="roles/cloudsql.client" \
  --quiet

echo "Done. Note your Cloud SQL instance connection name:"
gcloud sql instances describe "$SQL_INSTANCE" --project "$PROJECT_ID" --format='value(connectionName)'
echo "Use it for the CLOUD_SQL_INSTANCE GitHub secret."
