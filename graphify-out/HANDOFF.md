# Enterprise RAG Platform — Codex Handoff

Updated: 2026-10-13

## Resume instructions

The user has authorized continued implementation but will run the full RAG evaluation benchmark themselves. The working tree contains the implementation described below, and many modified/untracked files were present before this pass. Do not reset or clean the worktree. `backend/.env` contains local credentials and is ignored; never include its contents in a report or commit.

## Completed in the current implementation pass

- Hardened document upload and processing: supported extension/size validation, safe stored-file cleanup, page/section/table-aware extraction metadata, OCR for scanned PDF pages and embedded DOCX images, bounded token chunking, and staged chunk/embedding replacement so failed reindexing preserves the previous chunk set.
- Strengthened RAG generation: retained reranker order through context assembly, bounded context construction, unified stream/non-stream source selection, stricter evidence/citation prompting, citation repair and verification, grounding checks, persisted source metadata, and verified streaming output. Added provider fallback behavior that does not switch providers after partial output.
- Added Gemini/Ollama provider configuration, model/provider settings, compatible 384-dimensional embedding model selection and a maintenance reindex command. Added Redis fail-open embedding and verified-answer caching.
- Added runtime RAG settings for provider/fallback, retrieval/reranking/context/generation/chunk/cache and estimated token rates; admin settings UI and API. Embedding model remains environment configured and requires reindexing.
- Added admin analytics and persisted evaluation run history, baseline/regression comparison, per-case failure capture, atomic per-case JSON checkpointing, and evaluation/analytics/settings screens. CI includes a manually dispatched RAG regression benchmark; it requires external database/provider secrets.
- Added query telemetry for provider/model, stage latency, retrieval/citations, estimated token/cost values, fallback/cache state. Cost is estimated from operator-configured rates, not provider billing.
- Improved Celery retries/stale-job recovery and added S3-compatible object storage support. Added production-shaped Compose/Caddy and backup/restore scripts/runbook, plus `.env.example`.
- Fixed Docker DB URL separation: containers use `CONTAINER_DATABASE_URL`; the developer host uses `DATABASE_URL`. The local private `backend/.env` now points containers at the Compose PostgreSQL service (`postgres:5432`); host-side `DATABASE_URL` remains `localhost:5433`. These are distinct databases, and the Compose database is exposed on host port 5434.
- Frontend chat selections restore after refresh, saved assistant source metadata is displayed with citation links, the login page is the root landing route, streaming state is retained for newly created conversations, and the frontend has Analytics, Evaluations and Settings pages. `frontend/index.html` now has the product title/metadata.
- `README.md`, `DEPLOYMENT.md`, and `Codex_Changes.md` contain setup and change details. The latest change log has more file-level details than this summary.

## Verification completed

- Backend hardening suite: 28 tests passed (`HF_HUB_OFFLINE=1 ./.venv/bin/python -m unittest test_hardening.py -v`).
- Backend compile check passed; Alembic chain/head checks passed with head `d9a84c1f2b70`.
- Frontend production build passed (`npm run build`). Docker frontend image build passed.
- Development and production Compose configuration validation passed. `git diff --check` passed.
- The external-provider benchmark did not finish. Do not treat a partial output JSON as a final score or regression result.

## Current live services and database caveats

- There are two distinct PostgreSQL data stores: the old `enterprise-rag-db` container published at host port 5433 contains the user's original data (reported 8 users / 17 documents and evaluation fixture user 4/document 8); the Compose project's PostgreSQL on host port 5434 contains a separate smaller database (reported 1 user / 1 document / 6 chunks). Both databases were given the additive migration through `d9a84c1f2b70`; neither was deleted. A pre-migration dump was saved at `/tmp/enterprise-rag-before-d9a84c1f2b70.dump`.
- The user's recent Docker logs showed Compose PostgreSQL healthy and the API completing migrations and `/ready` successfully. The backend performs model initialization before Uvicorn begins accepting connections; early startup can reset localhost requests. Local and production Compose now give that healthcheck 120 seconds for model initialization. Verify `docker compose ps` and `/ready` before using the frontend.
- Ollama is on the host and `qwen3:8b` was reachable from the Docker network at `host.docker.internal:11434`; the host Python process reached it using `OLLAMA_BASE_URL=http://172.17.0.1:11434/v1`. Host `localhost:11434` did not work in that session.
- A live evaluation run against `evaluation_dataset.json`, user 4/document 8, provider Ollama/model `qwen3:8b`, baseline `evaluation_results_ollama_v3.json`, output `/tmp/enterprise-rag-evaluation-current.json` was explicitly interrupted by the user. It had reached the first case after hybrid retrieval; it is not a completed run. There may be a partial checkpoint at that `/tmp` path. The earlier failed attempt used an unreachable host Ollama URL. The fixture has not yielded a current regression verdict.
- Prior container access showed `/ready` return 200 on the smaller Compose DB before switching the API to the original database. That does not prove the latest API instance is healthy.

## Remaining work / suggested order

1. **Run and review the full RAG benchmark.** The backend hardening suite and provider smoke checks pass, but the full dataset benchmark has not completed. Run it against the intended evaluation database/document and reachable Ollama endpoint, save the JSON and `.txt` transcript, then inspect per-case failures and baseline deltas. Improve generation/citation/grounding only in response to measured failures. The user said they will run this benchmark.
2. **Run authenticated end-to-end product checks.** Current live checks cover container health, `/ready`, frontend HTTP, API docs HTTP, and Ollama reachability. Still verify login/registration, upload through worker completion, streaming chat, clickable citations, refresh/conversation/source persistence, and project/collection source assignment/removal/scoping. Also verify admin analytics/evaluation/settings flows and non-admin access denial using real accounts.
3. **Exercise live reliability integrations.** Unit tests cover retry-state handling and cache-related logic, but Redis outage/fail-open and invalidation behavior, retry/recovery against the running worker, and S3-compatible upload/read/delete/materialization remain unverified against those services.
4. **Choose and validate a production target.** Production Compose is a template, not a verified deployment. Supply the actual domain, managed PostgreSQL/pgvector URL, S3-compatible bucket/permissions, secret-management approach, and provider configuration, then validate and deploy to that target.
5. **Test production operations before relying on deployment.** Run a backup and restore drill against an isolated database, verify corresponding object-storage recovery/retention, and configure external health monitoring and alerts. No production target or S3 credentials are configured here.
6. **Verify release automation.** Local backend tests/compile, frontend lint/build, Compose validation, and shell syntax checks pass. Confirm the GitHub Actions CI run after the changes are pushed; the live benchmark workflow additionally needs its configured database/provider secrets and fixture.

### Latest local runtime verification (2026-10-13)

- All six local Compose services were up; backend, PostgreSQL, and Redis were healthy. `/ready` returned HTTP 200 with database, Redis, and storage checks true.
- Frontend (`http://localhost:5173`) and API docs (`http://localhost:8000/docs`) returned HTTP 200. Ollama's Docker-reachable API returned the configured `qwen3:8b` model.
- The runtime check did not authenticate as a user or submit a document/chat request, so it does not close the authenticated end-to-end items above.

## Important files

- RAG: `backend/app/services/rag.py`, `citation_verifier.py`, `rag_settings.py`, `llm.py`, `embedding.py`, `cache.py`.
- Ingestion: `backend/app/api/routes/documents.py`, `backend/app/services/document_service.py`, `document_processing.py`, `document_jobs.py`, `text_extraction.py`, `chunking.py`, `backend/app/tasks.py`, `worker.py`.
- Evaluation/analytics/admin: `backend/app/evaluation/`, `backend/app/services/analytics.py`, `backend/app/api/routes/admin.py`, models `evaluation_run.py`, `app_setting.py`, migration `backend/alembic/versions/d9a84c1f2b70_add_evaluation_run_history.py`.
- Frontend: `frontend/src/App.tsx`, `frontend/src/pages/Chat.tsx`, `Admin.tsx`, `Evaluations.tsx`, `AdminSettings.tsx`, `frontend/src/api/`.
- Operations/docs: `infrastructure/docker/docker-compose.yml`, `docker-compose.production.yml`, `Caddyfile`, `.env.example`, `DEPLOYMENT.md`, `README.md`, `Codex_Changes.md`.

## Worktree note

Implementation files listed by `git status --short` remain modified/untracked and are not committed. Preserve all of them. `Codex_Changes.md` notes that some unrelated files were already dirty before this pass, so do not attribute every existing diff to the latest implementation without checking its history/diff.

## Latest continuation (2026-10-12)

- RAG system instructions now request at most one sentence/35 words for a direct fact or definition and explicitly reject redundant trailing source lists. `verify_citations()` strips a trailing `Sources: 1, 2` footer before validating inline citations. Both stream and non-stream use the shared prompt/verification function.
- Evaluation case artifacts now preserve `draft_answer` and `failure_reasons`; the Evaluation UI surfaces the model's draft when it differs from the final grounded/fallback answer and lists failed gates.
- Added tests for parenthesized and bracketed trailing source-list cleanup. The focused backend suite passed 23 tests, backend compile passed, and `npm run build` passed. `git diff --check` passed.
- The user will run the full RAG benchmark. Run from `backend/` to store JSON plus a timestamped terminal transcript in `backend/evaluation_runs/`:

```bash
cd /home/harsh/Files/Development/Projects/enterprise-rag/backend
mkdir -p evaluation_runs
RUN_STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
set -o pipefail
OLLAMA_BASE_URL=http://172.17.0.1:11434/v1 HF_HUB_OFFLINE=1 ./.venv/bin/python -m app.evaluation.runner \
  --dataset evaluation_dataset.json \
  --user-id 4 \
  --document-id 8 \
  --provider ollama \
  --model qwen3:8b \
  --baseline evaluation_results_ollama_v3.json \
  --output "evaluation_runs/evaluation_${RUN_STAMP}.json" \
  2>&1 | tee "evaluation_runs/evaluation_${RUN_STAMP}.txt"
```

- The user reports the database is active. The benchmark has not been rerun in this continuation; its final score/regression status is therefore still pending. The database/API reachability from the host Python environment and the Ollama endpoint configured in the private `backend/.env` should be checked if the command reports a connection error.

## Latest evaluation failure diagnosis (2026-10-12)

- The user's benchmark log showed 16/16 cases failing at generation with `LLM generation failed: Connection error`. The prior host-runner config default is `http://localhost:11434/v1`; previous `ss` output showed Ollama listening on `172.17.0.1:11434`. Run `curl -fsS http://172.17.0.1:11434/v1/models` to verify before evaluation and override `OLLAMA_BASE_URL` as shown above. Do not interpret those failed case errors as a RAG quality regression.
- `backend/app/evaluation/runner.py` now marks runs with case errors or no results `incomplete`, skips baseline comparison, writes the case-error JSON artifact, and does not persist them as normal evaluation history. It exits nonzero so the connection issue remains visible.
- The added runner, document retry, analytics percentile, and provider diagnostic tests bring the hardening suite to 28 tests. After the runner/dashboard/worker changes, all 28 hardening tests passed, backend compile passed, frontend production build passed, production Compose config validation passed, CI YAML and operational shell syntax checks passed, and `git diff --check` passed. The user will run the actual benchmark.
- The failure output from the user's run reflects a provider connection problem, not a measured RAG quality regression. `backend/.env` has no `OLLAMA_BASE_URL`, so host Python uses the config default `http://localhost:11434/v1`. The previous host listener output showed `172.17.0.1:11434`; verify `curl -fsS http://172.17.0.1:11434/v1/models`, then rerun with the explicit `OLLAMA_BASE_URL` prefix in the command above.
- Runner now writes failed/partial case runs as `status: incomplete`, skips baseline comparison and DB history persistence, but keeps its JSON case-error artifact and exits nonzero. The admin API derives status for older persisted runs from `case_errors`; the Evaluation page marks those rows incomplete and excludes them from metrics/trends. This prevents the user's already-stored all-zero run from appearing as a valid regression.
- As of the prior verification, the user reports the database service is active. This environment cannot make local socket requests, so DB/API and Ollama reachability must be verified in the user's terminal.
- Continued reliability audit fixed job retry status handling in `backend/app/tasks.py`: retries now use persisted attempts (including recovered Celery messages), preserve `processing` UI state during backoff/recovery, and mark the document failed only after exhausting attempts.
- Production Redis now uses `volatile-lru`; expiring application cache entries can be evicted under memory pressure without Redis arbitrarily evicting Celery queue keys.
- `scripts/restore_postgres.sh` now has executable permissions, matching the direct invocation documented in `DEPLOYMENT.md`.
- CI benchmark logs are captured as `.txt` artifacts beside JSON. Admin analytics uses nearest-rank p95, and provider failures now include provider/model context and configuration hints without exposing credentials.

## Latest continuation (2026-10-13)

- The user's backend log identified the chat failure as `NameError: DocumentChunk is not defined` in `_retrieval_scope_version()`, called when constructing the answer-cache key. `backend/app/services/rag.py` now imports `DocumentChunk`, and `backend/test_hardening.py` includes a regression test for the cache-scope count.
- Added server-side exception logging for unexpected streaming-route errors and LLM streaming failures. Client-facing errors remain generic; the underlying traceback is available in backend logs.
- Local and production Compose backend healthchecks now allow 120 seconds for model initialization before counting failed probes. This addresses observed cold starts where model weights loaded before Uvicorn started.
- Admin analytics now computes headline metrics, daily trends, provider/model usage, and exact nearest-rank p95 in PostgreSQL instead of loading every query event into Python memory. The API response shape is unchanged.
- RAG settings validation now rejects non-object updates and non-string provider/fallback/embedding model values as client validation errors; regression tests cover the malformed inputs.
- PostgreSQL restore validates the archive before touching the target and uses `--exit-on-error --single-transaction` so failed restores roll back rather than leaving a partial restore.
- Graphify was refreshed after the latest code changes: 841 nodes, 1,915 edges, and 58 communities. The existing label set has 61 entries; refresh community names only if an LLM labeling backend is intentionally configured.
- The user has not yet rebuilt and rechecked the backend after the missing-import fix and healthcheck change. Rebuild with `docker compose --env-file backend/.env -f infrastructure/docker/docker-compose.yml up --build -d`, then wait for backend `healthy` and `/ready` 200 before testing chat.
- Verification at the time of this update passed: offline hardening suite (31 at that point; 34 after the admin-status tests below), Python compilation, frontend build, local Compose config, operational shell syntax, `git diff --check`, and focused mocked analytics checks with PostgreSQL SQL compilation. An earlier test attempt failed while tokenizer cache data was unavailable; the cache became available and the suite passed offline. The full RAG benchmark remains explicitly for the user to run.
- Admin dashboard follow-up: `backend/app/api/routes/admin.py` now supports admin-only user activate/deactivate, protecting both the acting admin and emails listed in `ADMIN_EMAILS`; the user list reports which controls are available. `frontend/src/pages/Admin.tsx` adds per-user actions with loading and error states. Five regression cases were added; the hardening suite now passes 36 tests and frontend build passes. Live API operation still requires verification against the user's running Docker stack.
- Graph refresh was attempted with `graphify . --update`, but its configured Ollama backend rejected extraction because `OLLAMA_API_KEY` is unset. The existing graph files therefore do not yet include this latest admin feature. No key was invented or written; rerun the Graphify update once its locally approved model endpoint configuration is available.
- Authentication follow-up: `/users/me` now includes the server-derived `is_admin`; frontend admin routes and the Administration link wait for and use this value. Login now refuses inactive accounts with a generic 401. The latest hardening suite passes 37 tests and frontend build/compile checks pass. This changes code after the last successful graph snapshot too.
- Website ingestion now streams and caps decoded HTML at 5 MiB (including when `Content-Length` is absent or incorrect), preventing unbounded response buffering. New tests cover both declared and streamed oversize bodies. Current hardening suite: 39 passing tests; compile, frontend build, Compose config, and diff checks pass.
- Registration now normalizes email lookup/storage, checks unique usernames, and catches database uniqueness races with rollback and HTTP 409. The hardening suite is now 42 tests and passes with backend compilation.

## Current continuation (2026-10-13)

- Frontend lint found synchronous effect state changes in `AuthContext.tsx` and `Admin.tsx`. Auth state now resets in the login/logout actions; the admin dashboard derives loading status from the selected and loaded periods. ESLint and the production build both pass.
- Added the passing frontend lint command to the frontend CI job and local check instructions, so lint failures now block CI alongside build failures.
- A later auth review found that API 401 responses left the frontend token stored. The shared API client now dispatches an unauthorized-session event, and `AuthProvider` clears expired/deactivated sessions so protected routes return to login.
- Graphify was refreshed for the current repository state. `graph.json` and `graph.html` cover 890 nodes, 1,825 edges, 9 hyperedges, and 66 communities; all community labels have matching membership signatures. The update replaced 43 nodes from re-extracted files, added the latest auth/CI relationships, and passed Graphify's endpoint-integrity check with zero dangling or collapsed edges. Incremental detection is clean. Temporary extraction files were removed; dated snapshots and stable outputs remain.
- Current verification: 42 backend hardening tests pass offline, Python compilation passes, frontend ESLint and production build pass, local Compose config validates, and `git diff --check` passes.
- Production Compose validation still needs deployment-specific values. Docker runtime/API/Ollama checks cannot be established from this environment; verify them in the user's terminal. The full RAG evaluation benchmark remains intentionally for the user to run. Do not treat deployment/integration/evaluation as complete based on local unit/build checks.
- Runtime access was subsequently granted for read-only checks: all six local Compose services are running (backend, PostgreSQL, and Redis healthy), `/ready` returned 200 with DB/Redis/storage true, and Ollama Qwen3 was reachable at `172.17.0.1:11434` (host `localhost:11434` is not listening). A tiny generation through backend-container `generate_response` and `stream_response` returned `OK` for both paths.
- The tiny generation also exposed empty content when Qwen3 had only 16 output tokens and used them for reasoning. `llm.py` now rejects empty responses, tries configured fallback, or raises the normal provider failure; four regression tests were added. Current hardening suite: 46 passing; compilation passed. Full document RAG and evaluation remain unverified by choice.

## Graphify refresh (2026-10-13)

- Refreshed the graph to include the verified remaining acceptance checklist. `graph.json` and `graph.html` now cover 905 nodes, 1,777 edges, 9 hyperedges, and 67 communities. All community label entries have matching membership signatures.
- Re-extracted the complete `Codex_Changes.md`, preserving its previous concepts and adding the remaining-work concept with links to evaluation, authentication, ingestion, job recovery, object storage, production operations, and CI. The three document-ingestion, identity/access, and RAG-quality lifecycle hyperedges remain present.
- Graph integrity validation found zero dangling or missing edge endpoints, zero duplicate edges, zero self-loops, and no unresolved hyperedge members. Incremental detection reports zero changed or deleted files.
- Reverification: 46 hardening tests passed; backend compilation, frontend lint, and frontend production build passed. The user's full RAG benchmark remains pending; production deployment and backup/restore still require the user's actual target configuration and verification.
