# Deployment Runbook

## Local stack

Copy the environment template, replace the secret/provider values, and start the
local services:

```bash
cp .env.example .env
docker compose -f infrastructure/docker/docker-compose.yml up --build
```

The API is available at `http://localhost:8000`, the frontend at
`http://localhost:5173`, and readiness at `http://localhost:8000/ready`. The API
applies Alembic migrations before serving. The worker processes ingestion jobs;
the scheduler recovers jobs abandoned by worker failures.
On a cold start the API can take up to two minutes to load embedding and
reranking models before it becomes healthy. Follow the backend logs and wait
for its health status and `/ready` endpoint before using the frontend.

For local Compose, `DATABASE_URL` in `backend/.env` is for commands run directly
on the host. Containers use the Compose network URL for PostgreSQL by default;
set `CONTAINER_DATABASE_URL` only when intentionally using another database
address reachable from the containers.

## Single-host production deployment

`infrastructure/docker/docker-compose.production.yml` is a deployable single
Linux host setup. It uses a managed PostgreSQL/pgvector database, private S3
compatible object storage, internal Redis, the API, worker, scheduler, frontend,
and Caddy HTTPS proxy. Point DNS for the application domain to the host and allow
inbound ports 80 and 443. Create a private bucket and grant the app only the
required bucket check/list and object read/write/delete permissions. Configure
server-side encryption and bucket versioning/retention to match your data policy.

On the host, create an untracked environment file from the template and fill in
production values:

```bash
cp .env.example .env.production
openssl rand -hex 32
```

Set `APP_DOMAIN`, `ADMIN_EMAILS`, `DATABASE_URL` (including the database
provider's TLS requirements), `SECRET_KEY`, `S3_BUCKET`, `S3_REGION`, and the
selected LLM provider credentials. Keep `.env.production` in the host's secret
store or an access-controlled deployment directory; never commit it. Prefer
workload identity/instance roles to static object-storage keys when available.

`EMBEDDING_MODEL` may be `BAAI/bge-small-en-v1.5` or
`sentence-transformers/all-MiniLM-L6-v2` (both 384 dimensions). Changing models
requires a maintenance window: back up PostgreSQL and S3, stop the stack, update
the setting, run the reindex command below in the backend container, then restart.
The command replaces chunk rows and embeddings; do not run it while API/worker
services are processing documents.

```bash
docker compose --env-file .env.production \
  -f infrastructure/docker/docker-compose.production.yml stop backend worker scheduler
docker compose --env-file .env.production \
  -f infrastructure/docker/docker-compose.production.yml run --rm backend \
  python -m app.maintenance.reindex_embeddings --confirm-reindex
docker compose --env-file .env.production \
  -f infrastructure/docker/docker-compose.production.yml up -d
```

Start the deployment:

```bash
docker compose --env-file .env.production \
  -f infrastructure/docker/docker-compose.production.yml up --build -d
```

Check service health and the public readiness endpoint:

```bash
docker compose --env-file .env.production \
  -f infrastructure/docker/docker-compose.production.yml ps
curl --fail "https://${APP_DOMAIN}/ready"
```

The production stack does not expose PostgreSQL or Redis ports. `/ready` checks
PostgreSQL, Redis, and object storage. Admin analytics includes request latency,
retrieval/generation/verification timing, retrieval and citation counts,
provider/model usage, estimated tokens, and estimated cost. Cost rates are
operator-configured estimates, not provider billing records.

## Backups and restore testing

Create a custom-format PostgreSQL backup:

```bash
DATABASE_URL="postgresql://postgres:postgres@localhost:5434/enterprise_rag" \
  BACKUP_DIR=./backups \
  ./scripts/backup_postgres.sh
```

Restore only during a maintenance window and into an isolated database first:

```bash
DATABASE_URL="postgresql://postgres:postgres@localhost:5434/enterprise_rag" \
  BACKUP_FILE=./backups/enterprise_rag_YYYYMMDDTHHMMSSZ.dump \
  ./scripts/restore_postgres.sh
```

Copy backups outside the database host. PostgreSQL backups do not include S3
objects; configure a separate bucket versioning/replication and retention policy.
Verify restored document retrieval and object reads before relying on a backup.

## CI and benchmark regression

GitHub Actions runs backend compilation/tests, frontend lint, and the frontend
production build.
For a live benchmark, configure `CI_SECRET_KEY` and `GEMINI_API_KEY` as GitHub
Actions secrets, then use **Actions → CI → Run workflow**. The job starts a
throwaway pgvector database, applies migrations, and the runner ingests the
committed evaluation corpus itself. Optionally supply a baseline JSON path
(relative to `backend/`) to run the regression check; the JSON result and the
terminal transcript are uploaded as artifacts. Live evaluation is manual because
it calls an external model.
