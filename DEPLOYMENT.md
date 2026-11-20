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

## Free self-hosted deployment (Oracle Cloud Always Free + DuckDNS)

Runs the whole platform on one free server: `infrastructure/docker/docker-compose.selfhost.yml`
starts PostgreSQL/pgvector, Redis, the API, worker, scheduler, frontend and
Caddy (automatic HTTPS). Data lives in Docker volumes on the server and is
backed up daily by `scripts/backup_selfhost.sh`. Only ports 80 and 443 are
public. Total cost: $0 (Oracle Always Free, DuckDNS, Gemini free tier).

The images build natively on Oracle's ARM (Ampere) CPUs; every dependency,
including CPU-only PyTorch, has an ARM64 build.

### 1. Create the server (Oracle Cloud console)

1. Sign up at https://www.oracle.com/cloud/free/. A card is needed for identity
   verification; Always Free resources are not charged. Your *home region*
   cannot be changed later; pick one near you.
2. **Compute → Instances → Create instance**:
   - **Image:** Canonical Ubuntu 24.04 (the aarch64 build is selected automatically for Ampere).
   - **Shape:** *Ampere* → `VM.Standard.A1.Flex` with **4 OCPUs and 24 GB memory**
     (the Always Free allowance; 2 OCPUs / 12 GB also works).
   - **Networking:** keep "Assign a public IPv4 address" on.
   - **SSH keys:** paste your public key (`cat ~/.ssh/id_ed25519.pub`).
   - **Boot volume:** 100 GB (Always Free includes 200 GB in total).
   - If you get *"Out of capacity"*, try another availability domain or retry later.
3. Optional but recommended: **Networking → IP management → Reserved public IPs**,
   so the address never changes.
4. Open the web ports: **Networking → Virtual cloud networks → (your VCN) →
   Security Lists → Default Security List → Add Ingress Rules**:
   - Source CIDR `0.0.0.0/0`, IP protocol TCP, destination port **80**
   - Source CIDR `0.0.0.0/0`, IP protocol TCP, destination port **443**

### 2. Point a free domain at it (DuckDNS)

1. Sign in at https://www.duckdns.org, add a subdomain (e.g. `myrag`), and set
   its IP to the instance's public IP.
2. Your address is `myrag.duckdns.org`. Check it resolves: `ping myrag.duckdns.org`.

### 3. Prepare the server

```bash
ssh ubuntu@<public-ip>

# Oracle's Ubuntu image blocks incoming traffic except SSH in its own firewall.
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save

# Security updates and Docker
sudo apt update && sudo apt -y upgrade && sudo apt -y install unattended-upgrades git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu && exit     # log in again so the group applies
```

### 4. Get the code and configure it

```bash
ssh ubuntu@<public-ip>
git clone https://github.com/Harsh03004/enterprise-rag.git
cd enterprise-rag
```

(If the repository is private, clone with a GitHub personal access token or a
deploy key.)

Create `.env.production` (git-ignored; it holds your secrets):

```bash
cat > .env.production <<EOF
APP_DOMAIN=myrag.duckdns.org
ADMIN_EMAILS=you@example.com
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -hex 24)
LLM_PROVIDER=gemini
GEMINI_API_KEY=paste-your-gemini-key
GEMINI_MODEL=gemini-3.1-flash-lite
EOF
chmod 600 .env.production
```

Replace `myrag.duckdns.org`, the admin email and the Gemini key with your own.

### 5. Start it

```bash
docker compose --env-file .env.production \
  -f infrastructure/docker/docker-compose.selfhost.yml up -d --build
```

The first build takes roughly 10-20 minutes on the ARM server; the first start
then downloads the ML models (~0.5 GB, kept in a volume afterwards). Follow
progress with:

```bash
alias rag='docker compose --env-file .env.production -f infrastructure/docker/docker-compose.selfhost.yml'
rag ps
rag logs -f backend
curl https://myrag.duckdns.org/ready
```

When `/ready` reports `ready`, open `https://myrag.duckdns.org`, register with
the email from `ADMIN_EMAILS` (that account gets Administration), and upload a
document. Caddy obtains the HTTPS certificate automatically on the first
request; ports 80 and 443 must be reachable for that.

### 6. Daily backups

```bash
mkdir -p backups
scripts/backup_selfhost.sh          # test once: writes a database dump + uploads archive
crontab -e                          # then add:
15 3 * * * cd /home/ubuntu/enterprise-rag && scripts/backup_selfhost.sh >> backups/backup.log 2>&1
```

Backups older than 14 days are deleted (`KEEP_DAYS`). They are on the same
server, so occasionally copy them elsewhere, e.g. from your laptop:
`scp -r ubuntu@<public-ip>:enterprise-rag/backups ./rag-backups`.

#### Restoring a self-hosted backup

```bash
rag stop backend worker scheduler
rag exec -T postgres pg_restore -U postgres -d enterprise_rag --clean --if-exists --no-owner \
  < backups/enterprise_rag_<stamp>.dump
rag run --rm --no-deps -T --entrypoint tar backend xzf - -C /storage \
  < backups/uploads_<stamp>.tar.gz
rag up -d backend worker scheduler
```

### 7. Updating

```bash
cd ~/enterprise-rag
scripts/backup_selfhost.sh
git pull
rag up -d --build                  # migrations run automatically on start
```

### Notes

- **Logs:** `rag logs -f backend` (JSON lines with request IDs).
- **Memory:** the backend and each worker process load the ML models (~1 GB
  each). With 12 GB or more, the defaults are fine; on smaller servers set
  `WORKER_CONCURRENCY=1` in `.env.production`.
- **Oracle idle reclamation:** Oracle may reclaim Always Free instances that
  stay almost completely idle for a week; normal use avoids this.
- **Security:** SSH keys only (Oracle's default), automatic security updates,
  PostgreSQL and Redis are not exposed, and secrets stay in `.env.production`.

## Single-host production deployment (managed PostgreSQL and S3)

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
