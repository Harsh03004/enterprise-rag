# Enterprise RAG

A self-hostable **Retrieval-Augmented Generation (RAG)** platform: upload your
documents (PDF, DOCX, Markdown, TXT or a public web page), organise them into
projects, and ask questions in a chat. Every answer is grounded in your
documents, carries inline citations (`[1]`, `[2]`) linked to source cards, and
is checked sentence by sentence before you see it.

---

## Contents

1. [Features](#features)
2. [How it works](#how-it-works)
3. [Tech stack](#tech-stack)
4. [Project structure](#project-structure)
5. [Quick start with Docker (recommended)](#quick-start-with-docker-recommended)
6. [Docker in detail](#docker-in-detail)
7. [Choosing an LLM provider](#choosing-an-llm-provider)
8. [Running without Docker (local development)](#running-without-docker-local-development)
9. [Installing the tools](#installing-the-tools)
10. [Configuration reference](#configuration-reference)
11. [Using the application](#using-the-application)
12. [Tests and evaluation](#tests-and-evaluation)
13. [Production deployment](#production-deployment)
14. [Troubleshooting](#troubleshooting)

---

## Features

**Documents**
- Upload PDF, DOCX, Markdown and TXT files, or ingest a public web page by URL.
- OCR for scanned PDF pages and for images embedded in DOCX files (Tesseract).
- PDF tables are extracted and kept as structured rows.
- Token-aware, heading-aware chunking with page and section metadata.
- Background processing with Celery: retries with backoff and automatic recovery of stuck jobs.

**Retrieval and answers**
- Hybrid search: semantic vectors (pgvector) plus Postgres full-text search, merged with reciprocal rank fusion.
- Cross-encoder reranking that scores each chunk by its best-matching passage.
- Page-aware retrieval ("what does page 3 say…").
- A confidence gate that refuses clearly unrelated questions without calling the LLM.
- Conversational query rewriting for follow-up questions.
- Streaming answers with inline citations and source cards.
- **Grounding check:** a CPU entailment model verifies every sentence against the source it cites. Unsupported sentences are removed with a note, wrong citations are corrected, and fully unsupported answers are replaced by a refusal.
- Answer and embedding caching in Redis.

**Workspace**
- Accounts with JWT authentication; account settings (username, password).
- Projects (collections) with project-scoped chats and sources; conversation history.
- Responsive UI with a phone-friendly sidebar drawer.

**Administration**
- Analytics: query volume, latency per pipeline stage, tokens, cost estimates, per-model statistics.
- User management (activate/deactivate), cross-user document and project management (retry, delete).
- Runtime RAG settings (provider, model, retrieval and reranking parameters).
- Evaluation history with regression checks.

**Operations**
- Multiple LLM providers: Ollama (local), Google Gemini, OpenRouter, with optional fallback provider.
- Structured JSON logs with a request ID that follows each request.
- Docker Compose stacks for local use and single-host production (Caddy with automatic HTTPS), backup and restore scripts, GitHub Actions CI.

---

## How it works

```
                 ┌──────────────┐      ┌──────────────────────────────────────────────┐
  Browser ─────► │  Frontend    │ ───► │  Backend API (FastAPI)                       │
                 │  React/Vite  │ ◄─── │                                              │
                 │  (nginx)     │  SSE │  question ─► rewrite ─► hybrid search ─┐     │
                 └──────────────┘      │                                        ▼     │
                                       │  confidence gate ◄─ rerank (best passage)    │
                                       │        │                                     │
                                       │        ▼                                     │
                                       │  grounded prompt ─► LLM ─► sentence-level    │
                                       │                            grounding ─► answer
                                       └───────┬───────────────┬──────────────────────┘
                                               │               │
                         ┌─────────────────────▼──┐   ┌────────▼───────┐   ┌──────────────────┐
                         │ PostgreSQL + pgvector  │   │ Redis          │   │ Celery worker    │
                         │ users, documents,      │   │ cache + queue  │◄──│ extraction, OCR, │
                         │ chunks + embeddings    │   └────────────────┘   │ chunking,        │
                         └────────────────────────┘                        │ embeddings       │
                                                                           └──────────────────┘
```

1. **Ingestion (worker):** the file is stored, text is extracted (with OCR where needed), split into ~400-token chunks with page and heading metadata, embedded with `BAAI/bge-small-en-v1.5`, and saved in Postgres/pgvector.
2. **Retrieval (API):** the question is rewritten if it depends on earlier messages, then vector search and keyword search each return candidates, which are fused and reranked by `cross-encoder/ms-marco-MiniLM-L-6-v2`.
3. **Generation:** the top chunks form a bounded context with numbered sources; the LLM must cite every statement.
4. **Verification:** `cross-encoder/nli-deberta-v3-xsmall` checks each sentence against its cited source (with a lexical fallback for exact paraphrases and table values) before the answer is shown.

All three ML models run on the CPU inside the backend; only the LLM is external or served by Ollama.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite, React Router, react-markdown; served by nginx in Docker |
| Backend API | Python 3.12, FastAPI, Uvicorn, Pydantic settings |
| Database | PostgreSQL 17 with the pgvector extension; SQLAlchemy 2 + Alembic migrations |
| Background jobs | Celery (worker + beat scheduler) with Redis as broker |
| Cache | Redis 7 (embeddings, answers) |
| ML models (CPU) | sentence-transformers / PyTorch (CPU build): bge-small embeddings, MiniLM reranker, DeBERTa entailment |
| Document parsing | PyMuPDF, pypdf, python-docx, BeautifulSoup, Tesseract OCR |
| LLM providers | Ollama, Google Gemini, OpenRouter (OpenAI-compatible APIs) |
| Auth | JWT (python-jose), Argon2 password hashing (pwdlib) |
| Storage | Local disk or S3-compatible object storage |
| Packaging | uv (Python), npm (Node) |
| Infrastructure | Docker, Docker Compose, Caddy (production HTTPS), GitHub Actions |

---

## Project structure

```
enterprise-rag/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routes (auth, chat, documents, collections, admin, users)
│   │   ├── core/           # settings, security, JWT, logging
│   │   ├── crud/           # database helpers
│   │   ├── db/             # session and base
│   │   ├── evaluation/     # evaluation runner, metrics, corpus loader
│   │   ├── maintenance/    # operator commands (re-embed documents)
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic request/response models
│   │   ├── services/       # RAG pipeline, retrieval, reranking, grounding, LLM, extraction
│   │   ├── main.py         # API entry point
│   │   ├── tasks.py        # Celery tasks
│   │   └── worker.py       # Celery app
│   ├── alembic/            # database migrations
│   ├── evaluation/         # evaluation corpus, dataset, baseline
│   ├── test_*.py           # unit tests
│   ├── Dockerfile
│   └── pyproject.toml / uv.lock
├── frontend/
│   ├── src/                # React app (pages, components, api clients)
│   ├── Dockerfile          # build with Node, serve with nginx
│   └── nginx.conf
├── infrastructure/docker/
│   ├── docker-compose.yml             # local stack
│   ├── docker-compose.production.yml  # production with managed PostgreSQL + S3
│   ├── docker-compose.selfhost.yml    # free all-in-one production (Postgres + files on the server)
│   ├── docker-compose.evaluation.yml  # resource-limited evaluation runs
│   └── Caddyfile                      # production reverse proxy / HTTPS
├── scripts/                # backups (managed + self-hosted), restore, run evaluation
├── .github/workflows/ci.yml
├── .env.example            # configuration template
├── DEPLOYMENT.md           # production runbook
└── README.md
```

---

## Quick start with Docker (recommended)

You only need **Git** and **Docker** (with Docker Compose); see [Installing the tools](#installing-the-tools).

```bash
# 1. Get the code
git clone https://github.com/Harsh03004/enterprise-rag.git
cd enterprise-rag

# 2. Create your configuration
cp .env.example .env
```

Edit `.env` and set at least:

| Setting | What to put |
|---|---|
| `SECRET_KEY` | A long random string, e.g. the output of `openssl rand -hex 32` |
| `ADMIN_EMAILS` | The email you will register with (comma-separated for several admins) |
| `LLM_PROVIDER` + key | `gemini` with `GEMINI_API_KEY=...` is the easiest start; see [Choosing an LLM provider](#choosing-an-llm-provider) |

```bash
# 3. Build and start everything
docker compose --env-file .env -f infrastructure/docker/docker-compose.yml up -d --build

# 4. Wait until the API is ready (the first start downloads the ML models)
curl http://localhost:8000/ready
```

Then open **http://localhost:5173**, create an account (use the email from
`ADMIN_EMAILS` to get the Administration pages), create a project, upload a
document and ask a question.

| URL | What |
|---|---|
| http://localhost:5173 | Web application |
| http://localhost:8000/docs | Interactive API documentation (Swagger) |
| http://localhost:8000/ready | Readiness check (database, Redis, storage) |

> **Tip:** every Compose command needs the same two flags. Save typing with an alias:
> `alias dc='docker compose --env-file .env -f infrastructure/docker/docker-compose.yml'`
> then use `dc ps`, `dc logs -f backend`, `dc down`.

---

## Docker in detail

### Services in the local stack

| Service | Image | Port (host) | Purpose |
|---|---|---|---|
| `postgres` | pgvector/pgvector:pg17 | 5434 | Database with vector search |
| `redis` | redis:7-alpine | 6379 | Cache and task queue |
| `backend` | enterprise-rag-backend (built from `backend/Dockerfile`) | 8000 | FastAPI app; runs migrations on start |
| `worker` | same image | – | Celery worker: document processing |
| `scheduler` | same image | – | Celery beat: recovers interrupted jobs every minute |
| `frontend` | built from `frontend/Dockerfile` | 5173 | React app served by nginx |

`backend`, `worker` and `scheduler` share one image. Uploaded files live in the
`uploaded_files` volume and the database in `postgres_data`, so data survives
restarts and rebuilds.

### Common commands

```bash
dc up -d --build          # build images and start (also applies code changes)
dc ps                     # status of all services
dc logs -f backend        # follow API logs (JSON lines with request IDs)
dc logs -f worker         # follow document-processing logs
dc restart backend        # restart one service
dc down                   # stop (data is kept in volumes)
dc down -v                # stop AND delete all data (database + uploads)
```

### Building the images by hand

```bash
# Backend (API, worker and scheduler)
docker build -t enterprise-rag-backend:latest backend

# Frontend; VITE_API_URL is baked in at build time
docker build -t enterprise-rag-frontend:latest \
  --build-arg VITE_API_URL=http://localhost:8000 frontend
```

### Running the images with `docker run` (without Compose)

Compose is the easiest way to run everything, but the images can also be run
one by one. The containers find each other by name on a shared network.

```bash
# 1. Network and volumes (database data and uploaded files)
docker network create rag-net
docker volume create rag-postgres-data
docker volume create rag-uploads

# 2. PostgreSQL with pgvector, and Redis
docker run -d --name rag-postgres --network rag-net \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=enterprise_rag \
  -v rag-postgres-data:/var/lib/postgresql/data \
  pgvector/pgvector:pg17
docker run -d --name rag-redis --network rag-net redis:7-alpine
```

Create a settings file for the backend containers, for example `docker.env`
(it holds secrets: keep it out of git; it is already listed in `.gitignore`):

```ini
APP_NAME=Enterprise RAG
DATABASE_URL=postgresql+psycopg://postgres:postgres@rag-postgres:5432/enterprise_rag
REDIS_URL=redis://rag-redis:6379/0
SECRET_KEY=change-me-to-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=http://localhost:5173
ADMIN_EMAILS=you@example.com
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-3.1-flash-lite
```

Wait a few seconds after starting Postgres (until `docker logs rag-postgres`
shows "ready to accept connections"), otherwise the API's migration step can
run before the database is up.

```bash
# 3. API: applies database migrations, then serves on port 8000
docker run -d --name rag-backend --network rag-net --env-file docker.env \
  -v rag-uploads:/storage -p 8000:8000 \
  --add-host=host.docker.internal:host-gateway \
  enterprise-rag-backend:latest \
  sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"

# 4. Worker (processes uploads) and scheduler (recovers stuck jobs): same image
docker run -d --name rag-worker --network rag-net --env-file docker.env \
  -v rag-uploads:/storage --add-host=host.docker.internal:host-gateway \
  enterprise-rag-backend:latest \
  celery -A app.worker.celery_app worker --loglevel=INFO --concurrency=2
docker run -d --name rag-scheduler --network rag-net --env-file docker.env \
  enterprise-rag-backend:latest \
  celery -A app.worker.celery_app beat --loglevel=INFO

# 5. Frontend on port 5173 (built with VITE_API_URL=http://localhost:8000)
docker run -d --name rag-frontend -p 5173:80 enterprise-rag-frontend:latest
```

Open http://localhost:5173 once `curl http://localhost:8000/ready` reports
`ready`. The API and the worker must share the `rag-uploads` volume. If you
use Ollama on the host, set `LLM_PROVIDER=ollama` and
`OLLAMA_BASE_URL=http://host.docker.internal:11434/v1` in `docker.env`.

Stop and remove everything (add `docker volume rm rag-postgres-data rag-uploads` to also delete the data):

```bash
docker rm -f rag-frontend rag-scheduler rag-worker rag-backend rag-redis rag-postgres
docker network rm rag-net
```

The backend image uses the **CPU-only build of PyTorch**, which keeps it to
about 4 GB instead of about 17 GB with CUDA. On the first start the containers
download the embedding, reranker and grounding models (about 0.5 GB) from
Hugging Face.

### Applying a changed `.env`

Containers read `.env` when they are created, so recreate them after editing it:
`dc up -d backend worker scheduler`.

---

## Choosing an LLM provider

The answer-writing model is the only external dependency. Pick one with
`LLM_PROVIDER` in `.env`. You can switch at runtime in **Administration → RAG
settings**, which also lets you set a fallback provider. A setting saved there
takes priority over `.env`.

### Google Gemini (simplest, free tier available)

1. Go to **https://aistudio.google.com/apikey** and sign in with a Google account.
2. Click **Create API key** and restrict it to the Gemini API.
3. In `.env`: `LLM_PROVIDER=gemini`, `GEMINI_API_KEY=<your key>`, `GEMINI_MODEL=gemini-3.1-flash-lite`.

Free-tier limits apply per project; you can see yours at https://aistudio.google.com/rate-limit.

### Ollama (fully local, no API key)

1. Install Ollama (see [Installing the tools](#installing-the-tools)) and pull a model:
   ```bash
   ollama pull qwen3:8b
   ```
2. Make Ollama reachable from Docker containers. By default it only listens on
   `localhost`. Bind it to all interfaces (or to the Docker bridge address):
   ```bash
   sudo systemctl edit ollama        # add the two lines below
   # [Service]
   # Environment="OLLAMA_HOST=0.0.0.0:11434"
   sudo systemctl restart ollama
   ```
3. In `.env`: `LLM_PROVIDER=ollama`, `OLLAMA_MODEL=qwen3:8b`,
   `OLLAMA_BASE_URL=http://host.docker.internal:11434/v1`.

An 8B model needs about 6 GB of GPU memory, or runs slowly on the CPU. See
[Troubleshooting](#troubleshooting) if your desktop freezes while Ollama generates.

### OpenRouter (many hosted models, some free)

1. Create a key at https://openrouter.ai/keys.
2. In `.env`: `LLM_PROVIDER=openrouter`, `OPENROUTER_API_KEY=<your key>`,
   `OPENROUTER_MODEL=google/gemma-4-31b-it:free` (models ending in `:free` are rate limited).

---

## Running without Docker (local development)

Run Postgres and Redis however you like (the Compose services are the easiest), and run the backend and frontend directly for fast reloads.

### 1. Database and cache

Either start just these two services from the Compose file:

```bash
docker compose --env-file .env -f infrastructure/docker/docker-compose.yml up -d postgres redis
# Postgres is then on localhost:5434 (user postgres, database enterprise_rag)
```

or install PostgreSQL 17 with the **pgvector** extension and Redis 7 natively
(see [Installing the tools](#installing-the-tools)) and create a database:

```bash
createdb enterprise_rag
psql enterprise_rag -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 2. Backend

```bash
cd backend
uv sync                      # creates .venv with Python 3.12 and all dependencies
```

Create `backend/.env`:

```ini
APP_NAME=Enterprise RAG
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5434/enterprise_rag
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-to-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ADMIN_EMAILS=you@example.com
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key
LOG_FORMAT=text
```

Then, each in its own terminal from `backend/`:

```bash
uv run alembic upgrade head                                         # create / update tables
uv run uvicorn app.main:app --reload --port 8000                    # API
uv run celery -A app.worker.celery_app worker --loglevel=INFO --concurrency=2   # document processing
uv run celery -A app.worker.celery_app beat --loglevel=INFO         # stuck-job recovery (optional)
```

Tesseract must be installed on the machine for OCR.

### 3. Frontend

```bash
cd frontend
npm ci
echo "VITE_API_URL=http://localhost:8000" > .env   # where the API runs
npm run dev                                         # http://localhost:5173
```

Other scripts: `npm run build` (production build into `dist/`), `npm run lint`, `npm run preview`.

---

## Installing the tools

Install only what your chosen setup needs:

| Setup | Needs |
|---|---|
| Docker quick start | Git, Docker + Compose |
| Local development | Git, Python 3.12 + uv, Node.js 22, PostgreSQL 17 + pgvector (or Docker), Redis 7 (or Docker), Tesseract |
| Local LLM | Ollama |

### Git
- **Ubuntu/Debian:** `sudo apt install git`
- **Fedora:** `sudo dnf install git`
- **macOS:** `xcode-select --install` (or `brew install git`)
- **Windows:** https://git-scm.com/download/win

### Docker and Docker Compose
- **Linux:** follow https://docs.docker.com/engine/install/ for your distribution (it installs the `docker compose` plugin), then let your user run Docker without sudo: `sudo usermod -aG docker $USER` and log in again.
- **macOS / Windows:** install Docker Desktop from https://www.docker.com/products/docker-desktop/ (includes Compose). On Windows, enable the WSL 2 backend.
- Check: `docker --version` and `docker compose version`.

### Python 3.12 and uv
uv installs and manages Python for you:
- **Linux / macOS:** `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Windows (PowerShell):** `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
- `uv sync` in `backend/` then downloads Python 3.12 automatically (pinned in `backend/.python-version`).

### Node.js 22
- Recommended: a version manager such as **fnm** (`curl -fsSL https://fnm.vercel.app/install | bash`, then `fnm install 22`) or **nvm**.
- Or download the LTS installer from https://nodejs.org/.
- Check: `node --version` (v22.x) and `npm --version`.

### PostgreSQL 17 with pgvector
- **Easiest:** use Docker (`pgvector/pgvector:pg17` already includes the extension), as in the Compose file.
- **Ubuntu/Debian:** install PostgreSQL 17 from the PGDG repository (https://www.postgresql.org/download/linux/ubuntu/), then `sudo apt install postgresql-17-pgvector`.
- **Fedora:** `sudo dnf install postgresql-server pgvector` (pick the pgvector package matching your PostgreSQL version).
- **macOS:** `brew install postgresql@17 pgvector`.
- Enable it once per database: `CREATE EXTENSION IF NOT EXISTS vector;`

### Redis 7
- **Easiest:** Docker (`redis:7-alpine`).
- **Ubuntu/Debian:** `sudo apt install redis-server`; **Fedora:** `sudo dnf install redis` (or `valkey`); **macOS:** `brew install redis`.

### Tesseract OCR (local development only; the Docker image already includes it)
- **Ubuntu/Debian:** `sudo apt install tesseract-ocr`
- **Fedora:** `sudo dnf install tesseract`
- **macOS:** `brew install tesseract`
- **Windows:** installer from https://github.com/UB-Mannheim/tesseract/wiki, then add it to `PATH`.

### Ollama (optional, for a local LLM)
- **Linux:** `curl -fsSL https://ollama.com/install.sh | sh`
- **macOS / Windows:** download from https://ollama.com/download
- Then `ollama pull qwen3:8b`.

---

## Configuration reference

All settings are environment variables (from `.env` in Docker, or `backend/.env` when running the backend directly). The full template is in `.env.example`.

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | – (required) | Key used to sign login tokens; use a long random value |
| `ADMIN_EMAILS` | empty | Comma-separated emails that get the Administration pages |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed frontend origins |
| `LLM_PROVIDER` | `ollama` | `ollama`, `gemini` or `openrouter` |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | – / `gemini-3.1-flash-lite` | Gemini settings |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | host Ollama / `qwen3:8b` | Ollama settings |
| `OPENROUTER_API_KEY` / `OPENROUTER_MODEL` | – / `google/gemma-4-31b-it:free` | OpenRouter settings |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Must produce 384-dimension vectors; changing it needs a re-embed |
| `GROUNDING_MODEL` / `GROUNDING_MIN_ENTAILMENT` | DeBERTa NLI / `0.5` | Sentence verification model and threshold |
| `STORAGE_BACKEND` | `local` | `local` or `s3` (then set `S3_BUCKET`, `S3_REGION`, `S3_ENDPOINT_URL`, credentials) |
| `POSTGRES_PASSWORD` | `postgres` | Password of the Compose Postgres |
| `CONTAINER_DATABASE_URL` | Compose Postgres | Point the containers at another database |
| `WORKER_CONCURRENCY` | `2` | Celery worker processes (each loads the ML models) |
| `LOG_FORMAT` / `LOG_LEVEL` | `json` / `INFO` | `text` is easier to read locally |
| `APP_DOMAIN` | – | Production only: public domain for Caddy/HTTPS |

Retrieval and generation parameters (top-k, reranking, confidence threshold,
context size, temperature, chunk size, cost rates) are set at runtime in
**Administration → RAG settings**.

---

## Using the application

1. **Register** at `/register`. Accounts whose email is in `ADMIN_EMAILS` also get **Administration** in the header.
2. **Create a project** in the sidebar (or use *All Documents*).
3. **Upload** files or **add a website**. Processing runs in the background; the badge changes from *Processing* to *Processed*. Failed documents can be retried.
4. **Ask questions** in the chat. The answer streams as a dimmed draft, then is replaced by the verified answer with `[n]` citations and source cards (file, chunk, page, section).
   - Scope: a single document, a project, or all documents.
   - Name a page to search only that page: "what does page 2 say about pricing?"
   - If the documents do not contain the answer, you get a refusal instead of a guess.
5. **Account settings** (`/settings`): change your username or password.
6. **Administration** (`/admin`): analytics, user management, *Content* (all documents and projects), *Evaluations* (benchmark history) and *RAG settings*.

On phones, the projects/chats sidebar opens from the menu button in the header.

---

## Tests and evaluation

### Unit tests

```bash
cd backend
uv run python -m unittest test_hardening.py test_rag_pipeline.py test_evaluation.py \
  test_grounding.py test_logging.py test_admin_content.py test_account_settings.py -v

cd ../frontend
npm run lint && npm run build
```

CI (`.github/workflows/ci.yml`) runs these on every push and pull request.

### RAG evaluation

`backend/evaluation/` contains a fixed test corpus (a DOCX report, a Markdown
handbook, a TXT policy and a PDF with tables), 75 questions with the facts a
correct answer must contain, and a baseline result. The runner ingests the
corpus for a dedicated, login-disabled evaluation account and runs every
question through the real pipeline. It reports answer accuracy, refusals,
retrieval and citation quality.

```bash
# Runs inside the Docker stack with CPU/memory limits; resumes if interrupted.
EVAL_PROVIDER=gemini scripts/run_evaluation.sh --limit 10        # next 10 questions
EVAL_PROVIDER=gemini scripts/run_evaluation.sh \
  --baseline evaluation/baselines/gemini-3.1-flash-lite.json     # all, with regression check
```

Model answers are cached in `backend/evaluation_runs/llm_cache/`, so re-runs only
send questions whose prompt changed. Results are written to
`backend/evaluation_runs/` and appear under **Administration → Evaluations**.
`EVAL_PROVIDER=ollama` runs a CPU-only Ollama container instead (slow, but
uses no GPU). A manual GitHub Actions job runs the same benchmark against Gemini.

---

## Production deployment

**Free option:** `infrastructure/docker/docker-compose.selfhost.yml` runs
everything (including PostgreSQL and file storage) on one server, e.g. an
Oracle Cloud Always Free ARM instance with a free DuckDNS domain and automatic
HTTPS, with daily backups via `scripts/backup_selfhost.sh`. Step-by-step guide:
[DEPLOYMENT.md → Free self-hosted deployment](DEPLOYMENT.md#free-self-hosted-deployment-oracle-cloud-always-free--duckdns).

**Managed option:** `infrastructure/docker/docker-compose.production.yml` runs the API, worker,
scheduler, frontend, Redis and **Caddy** (automatic HTTPS for `APP_DOMAIN`) on
one Linux host, with a managed PostgreSQL/pgvector database and S3-compatible
storage. `scripts/backup_postgres.sh` and `scripts/restore_postgres.sh` handle
backups. The complete runbook is in **[DEPLOYMENT.md](DEPLOYMENT.md)**.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `SECRET_KEY is required` from Compose | Add `--env-file .env` to every `docker compose` command (or use the `dc` alias). |
| Port already in use (5173, 8000, 5434, 6379) | Stop the other program, or change the left side of the `ports:` mapping in the Compose file. |
| First answer is slow / `/ready` is not ready yet | The first start downloads ~0.5 GB of models; wait 1–2 minutes and watch `dc logs -f backend`. |
| "The AI response could not be completed" | The LLM is unreachable: check the API key and model name, or that Ollama is running and reachable from Docker (`OLLAMA_HOST`). |
| Gemini `404 … model is no longer available` | Set `GEMINI_MODEL` to a current model (e.g. `gemini-3.1-flash-lite`) and recreate the containers. |
| Desktop freezes while Ollama answers | Ollama is using the same GPU that draws your screen. Run the desktop on the integrated GPU (hybrid graphics mode), use a remote provider, or use the CPU-only evaluation container. |
| Documents stay in *Processing* | Check `dc logs -f worker`; the scheduler retries interrupted jobs every minute, and failed ones can be retried from the sidebar or Administration → Content. |
| Changes to `.env` have no effect | Recreate the containers: `dc up -d backend worker scheduler`. |
