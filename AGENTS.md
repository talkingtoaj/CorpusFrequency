# CorpusFrequency

Deploy stage: 1 (MVP Online)

Deploy: `gcloud builds submit --config cloudbuild.yaml --substitutions _TAG=$(git rev-parse HEAD)` (see README, "Deploying").

Rollback: check out the old commit and deploy again.
