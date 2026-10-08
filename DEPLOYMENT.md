# Deployment Runbook

## Local Production-Shaped Stack

Create a secret and start the services:

```bash
export SECRET_KEY="replace-with-a-long-random-secret"
docker compose -f infrastructure/docker/docker-compose.yml up --build
```

The API is available at `http://localhost:8000`, the frontend at
`http://localhost:5173`, and readiness is exposed at `http://localhost:8000/ready`.

The API container runs Alembic migrations before starting. Document processing is
handled by the separate Celery worker through Redis.

## Backups

Create a custom-format PostgreSQL backup:

```bash
DATABASE_URL="postgresql://postgres:postgres@localhost:5434/enterprise_rag" \
  BACKUP_DIR=./backups \
  ./scripts/backup_postgres.sh
```

Restore a backup only during a maintenance window:

```bash
DATABASE_URL="postgresql://postgres:postgres@localhost:5434/enterprise_rag" \
  BACKUP_FILE=./backups/enterprise_rag_YYYYMMDDTHHMMSSZ.dump \
  ./scripts/restore_postgres.sh
```

Backups must be copied to storage outside the host running PostgreSQL. Test a
restore regularly in an isolated database before relying on the backup.

## CI

GitHub Actions runs backend compilation/tests and the frontend production build.
Evaluation regression checks can be added to the backend job once a database and
model provider are available in CI.