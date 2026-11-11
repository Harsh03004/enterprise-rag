# Codex Changes

This document records the implementation changes made during the Codex work in this session. It describes the specific changes made on top of the repository state that was present when implementation began.

> **Worktree note:** Several files were already modified or untracked when this implementation pass started. Their pre-existing changes are not attributed to this pass unless explicitly listed below. No pre-existing changes were reset or discarded.

## 1. Provider configuration and Docker connectivity

### `backend/app/core/config.py`

- Removed the required `openrouter_api_key` setting. The application did not use OpenRouter in its LLM provider code, and requiring this value made local Ollama configuration depend on an unused secret.
- Made `gemini_api_key` optional, with an empty default, so Ollama users do not need to supply a Gemini credential.
- Added usable defaults for `gemini_model`, `llm_provider`, and `ollama_model`.
- Added `ollama_base_url`, defaulting to the local OpenAI-compatible Ollama endpoint. It can be overridden through the corresponding environment variable.

### `backend/app/services/llm.py`

- Changed Ollama client creation to use `settings.ollama_base_url` instead of a hard-coded module constant.
- Gemini remains selected through the same OpenAI-compatible client abstraction and Gemini base URL.

### `infrastructure/docker/docker-compose.yml`

- Added a named `uploaded_files` volume and mounted it at `/storage` in both the API and Celery worker containers. Uploaded file paths are therefore visible to the worker that processes them and persist across container replacement.
- Passed `OLLAMA_BASE_URL` to both backend containers. The Compose default uses `host.docker.internal` and `host-gateway` so containers can reach an Ollama service running on the host on supported Docker installations.
- The Compose stack still does not run or install Ollama. The user must run Ollama separately and pull the selected model.
- Removed hard-coded `container_name` values from all Compose services. Docker Compose now assigns project-scoped names, preventing collisions with containers created by another Compose project.
- Made the host PostgreSQL port configurable with `POSTGRES_HOST_PORT`, defaulting to `5434` to avoid the occupied host port `5433` reported during startup. The service continues listening on internal port `5432`, which is what backend containers use.
- Updated README and deployment backup examples to use the published port `5434` by default.

## 2. Upload validation and stored-file cleanup

### `backend/app/services/document_service.py`

- Added an allowlist matching the extractor’s actual supported upload formats: `.pdf`, `.docx`, `.md`, and `.txt`.
- Added `validate_upload_filename`, which sanitizes the supplied name and rejects unsupported extensions before the upload is written.
- Added `remove_uploaded_file`, which resolves the stored path and removes it only when it is inside the application storage directory. This prevents a database path outside the upload area from being unlinked.

### `backend/app/api/routes/documents.py`

- Validates the filename before collection lookup, file persistence, and background job creation.
- Returns HTTP 415 for unsupported upload extensions.
- Uses `application/octet-stream` if the client omits the content type, avoiding a null value for the database’s non-null content type column.

### `backend/app/crud/document.py`

- Captures the file path, deletes the document and its database dependents, then removes the uploaded file through the guarded cleanup helper.
- Website records have no local file path, so cleanup safely does nothing for them.

### `frontend/src/components/Sidebar.tsx`

- Updated the file picker to advertise the supported `.txt` format and removed `.markdown`, which the backend extractor does not accept. Markdown files use `.md`.

## 2.3. Enable pgvector during database migration

### `backend/alembic/versions/9f6316708db3_add_embeddings_to_document_chunks.py`

- The migration now runs `CREATE EXTENSION IF NOT EXISTS vector` before adding the embedding column. The `pgvector/pgvector` image contains the extension files, but each database must enable the extension before PostgreSQL recognizes the `VECTOR` column type.
- The extension is intentionally left installed when downgrading the column migration, since the extension may be used elsewhere in the database.

## 2.2. pgvector Alembic migration imports

### `backend/alembic/versions/9f6316708db3_add_embeddings_to_document_chunks.py` and `db0380c2f0d5_change_embedding_dimension_to_384.py`

- Imported `VECTOR` directly from `pgvector.sqlalchemy` and used that symbol in migration type declarations. The previous `import pgvector` did not make `pgvector.sqlalchemy` available as an attribute, which caused fresh database initialization to stop while adding the embedding column.

## 2.1. Backend container PostgreSQL driver runtime

### `backend/Dockerfile`

- Added the `libpq5` runtime package alongside Tesseract. Psycopg is installed in pure-Python mode by the current dependency lock and needs the system `libpq` shared library at runtime; without it, both Alembic startup and the Celery worker fail with `no pq wrapper available`.

## 3. Authentication behavior

### `backend/app/api/dependencies.py`

- `get_current_user` now rejects accounts whose `is_active` flag is false, returning the same unauthorized response used for missing users.

## 4. Retrieval, context construction, citations, and grounding

### `backend/app/services/rag.py`

- Preserved candidate order within each document when grouping chunks for context construction. Previously, chunks were reordered by their original document index after reranking; the context now retains reranker order within a document.
- Corrected context character-budget accounting. The builder now tracks the actual header and chunk text lengths, including separators, rather than adding the count of existing segments. It continues scanning later chunks when an earlier chunk does not fit.
- Made the non-streaming reranker result limit match the streaming path (`limit`, normally five), preventing different source sets between chat modes.
- Runs citation repair after initial citation cleanup in both paths, allowing uncited claims to be repaired even when another claim already has a valid citation.
- Applies citation and grounding verification to streaming answers before sending any answer text to the client. The provider is still consumed as a stream, but output is buffered until validation completes; the verified text is then sent in chunks, followed by the final answer and sources events.
- Persists the validated user/assistant messages before yielding display chunks, so disconnecting while the verified answer is being displayed does not discard the completed turn.
- Uses a single helper to remove internal `_content` and `_embedding` fields from response sources.
- Returns a grounding fallback when semantic validation fails, and sends no sources for that fallback.

### `backend/app/services/citation_verifier.py`

- Changed missing-citation repair so it attempts to annotate every uncited claim, rather than returning unchanged whenever any citation exists in the answer.
- Improved claim splitting for the common punctuation form `Claim. [Source 1] Next claim.` so the citation remains attached to the preceding claim.
- Changed grounding verification to reject uncited claims instead of silently skipping them. Each claim must reference an available source and pass the configured semantic similarity check.

### `frontend/src/pages/Chat.tsx`

- Citation rendering now recognizes both `[Source N]` and compact `[N]` citation forms and links recognized citations to their matching source card.

## 5. Evaluation behavior

### `backend/app/evaluation/evaluator.py`

- Added the production reranker confidence gate to evaluation. Low-confidence cases use the same relevant-information fallback as production instead of always invoking the LLM.
- Added the production citation repair and semantic grounding checks after answer generation. Invalid or unsupported answers are replaced with the grounding fallback before answer/citation metrics are calculated.
- Keeps evaluation focused on one retrieval/rerank operation per case and does not create conversations.

This brings the evaluator closer to production behavior. The benchmark still uses an empty conversation history, which is appropriate for its current cases but does not measure conversational query rewriting.

## 6. Documentation

### `README.md`

- Replaced the empty root README with current setup and usage guidance covering Docker Compose, host Ollama configuration, Gemini configuration, supported ingestion types, backend/frontend checks, and evaluation invocation.
- Clarified that the Compose stack does not provide Ollama and that evaluation output is not currently a CI gate.

## 7. Regression tests

### `backend/test_hardening.py`

Added tests for:

- Preserving reranked chunk order while enforcing the context character budget.
- Repairing an uncited claim in an answer that already has another citation.
- Rejecting a mixed cited/uncited answer during grounding verification.
- Keeping citations after sentence punctuation attached to the correct claim.
- Accepting `.txt` and rejecting `.markdown` according to the backend extractor’s supported formats.
- Writing atomic evaluation checkpoints and preserving existing chunks when replacement embedding generation fails.

## 8. Verification performed

The following checks passed after the changes:

- `./.venv/bin/python -m unittest test_hardening.py -v` — 16 tests passed.
- `./.venv/bin/python -m compileall -q app` — passed.
- `npm run build` in `frontend/` — passed (TypeScript compile and Vite production build).
- `SECRET_KEY=check-only docker compose -f infrastructure/docker/docker-compose.yml config --quiet` — passed; this validates Compose configuration without starting containers.
- `git diff --check` — passed.

The Hugging Face Hub authentication warning during tests is informational; the tests completed successfully using the locally available model weights.

## 9. Benchmark status and known limits

The 16-case evaluation command was started against the existing user 4/document 8 fixture and configured LLM provider, with the requested output path under `/tmp`. The run was interrupted before it completed. It had reached case 9 of 16; early cases showed that retrieval recall could be high while answer F1 remained low, and some relevant answers were rejected by grounding checks. Since the runner writes its JSON output at the end, there is no completed result at `/tmp/enterprise-rag-evaluation-current.json` from that interrupted run. The checked-in historical benchmark files were not overwritten.

The ad hoc scripts `backend/test_rag_suite.py` and `backend/test_reranker.py` were not run: they use fixed database IDs, and the RAG suite creates conversations and invokes the configured provider. The unit suite and CI-equivalent frontend/backend checks listed above did complete.

## 10. Login landing route and durable chat sources

### `frontend/src/App.tsx`

- Added an explicit `/` route that redirects to `/login`; unknown paths now also land on the login page.

### `frontend/src/components/Layout.tsx`

- Persists the active document, collection, and conversation selection in browser local storage and restores that scope after a page refresh. This makes the selected conversation load again instead of opening an empty chat.

### `backend/app/models/message.py`, `backend/app/crud/conversation.py`, `backend/app/schemas/conversation.py`, and `backend/app/services/rag.py`

- Added a JSON `sources` field to saved messages and exposed it in conversation history responses.
- Both regular and streaming RAG paths now save the same public source metadata that they return to the frontend. Messages without citations store an empty list.
- Added Alembic revision `c4e19b8a6d72` to create the JSON column and initialize existing messages with an empty source list.

### `frontend/src/api/conversations.ts` and `frontend/src/pages/Chat.tsx`

- Loads each assistant message’s saved sources with the conversation and renders its source panel beside that answer. Citation links now target the matching message’s sources, even when several answers use source number 1.
- Streaming messages retain their returned sources immediately, before the conversation is reopened.
- Selecting the just-created conversation no longer resets the active stream, so the answer stays visible as it arrives without requiring a refresh.
- Existing messages created before this migration have no source metadata to restore; their source panels will be empty. New answers will retain sources after the database migration and frontend rebuild.

## 11. Roadmap implementation: evaluation history, analytics, and runtime settings

### Database and admin API

- Added `backend/app/models/evaluation_run.py` and `backend/app/models/app_setting.py`, registered in `backend/app/models/__init__.py`.
- Added Alembic revision `d9a84c1f2b70_add_evaluation_run_history.py`. It creates evaluation history and singleton application settings storage, extends query telemetry with provider/model, retrieval and citation counts, token estimates, fallback/cache flags, cost estimates, and stage timings, and adds chunk-rebuild state to processing jobs.
- `backend/app/evaluation/runner.py` accepts provider/model and a baseline, atomically checkpoints the JSON artifact after every case, rolls back failed case transactions, records unexpected case exceptions while continuing, saves run summary/results, and returns a failing process status when a configured regression check fails. `evaluator.py` includes failed cases in pass-rate calculations.
- `backend/app/api/routes/admin.py` exposes admin-only evaluation history/detail, analytics, and RAG settings endpoints.

### Analytics and evaluation UI

- `backend/app/services/analytics.py` records query-level retrieval/generation/verification timing, provider/model, cache and fallback events, citations, and estimated token/cost values; it aggregates daily trends and provider/model breakdowns.
- `frontend/src/pages/Admin.tsx` now presents usage, latency, query trends, provider/model breakdown, and account/document summaries. Cost values are estimates based on operator-configured per-token rates, not vendor billing data.
- `frontend/src/pages/Evaluations.tsx` shows saved run history, metric trends, failed cases, and regression status. The page is routed from `frontend/src/App.tsx` and linked from admin navigation.
- Evaluation summary cards now format every rate consistently as a percentage and include keyword recall, so fallback accuracy is not shown as a confusing raw `1.0` value.
- `.github/workflows/ci.yml` has an explicitly dispatched RAG regression job that requires configured database and provider secrets, runs migrations and a benchmark, then uploads the JSON artifact. Ordinary CI retains compilation, the focused backend suite, and the frontend build.

### Runtime RAG configuration and answer behavior

- `backend/app/services/rag_settings.py` resolves bounded database-backed defaults/overrides for provider and fallback, retrieval top-k/candidate multiplier, reranking limits/threshold, context budget, generation temperature/output cap, chunk size/overlap, cache TTL, and estimated token rates. `frontend/src/pages/AdminSettings.tsx` provides the admin editor.
- `backend/app/services/llm.py` supports configured primary/fallback providers, model/temperature/output settings, and avoids restarting on a fallback after streaming has already emitted partial output. `backend/app/services/rag.py` uses the runtime retrieval/context settings and sends a separate system instruction that treats documents and history as untrusted evidence, requires support and citations, and asks for concise answers.
- RAG telemetry reports the actual provider/model used. The configurable embedding model is selected through `EMBEDDING_MODEL` and is constrained to compatible 384-dimensional models; it is an environment-level choice requiring a reindex, rather than a hot-swappable admin setting.
- `backend/app/services/cache.py` adds fail-open Redis JSON caching. Embeddings are cached by model and text. Verified RAG answers are cached by user, scope, rewritten query, history, corpus version, settings, and prompt version; only grounded, non-fallback answers are stored.
- `backend/app/maintenance/reindex_embeddings.py` provides an explicit-confirmation maintenance command for rebuilding embeddings and chunks after changing the embedding model. The API/worker should be stopped and data backed up before this operation.

## 12. Document intelligence, job recovery, and object storage

- `backend/app/services/chunking.py` builds bounded token windows while respecting Markdown section boundaries and nearby paragraph/line boundaries, retaining heading and page metadata and marking table-like blocks.
- `backend/app/services/text_extraction.py` preserves PDF page boundaries (including empty/scanned pages), runs OCR on scanned pages, extracts PDF tables where supported, retains DOCX headings, serializes DOCX tables, and OCRs embedded images.
- `backend/app/services/document_service.py` supports local storage or S3-compatible object storage with upload size limits, safe key handling, cleanup, and worker-side materialization of remote files. `backend/app/main.py` includes storage in readiness checks.
- `backend/app/tasks.py` and `backend/app/worker.py` add periodic recovery for stale queued/retrying/processing jobs, with bounded redelivery and terminal failure handling.
- `backend/app/services/document_processing.py` stages extraction and all replacement embeddings before deleting existing chunk rows. Reindex swaps the completed chunk set transactionally; a parsing/model failure leaves the previous vectors available.
- `infrastructure/docker/docker-compose.yml` includes the recovery scheduler and storage/embedding configuration. `infrastructure/docker/docker-compose.production.yml` and `infrastructure/docker/Caddyfile` provide a single-host HTTPS deployment shape with an external PostgreSQL/pgvector database, private Redis, S3-compatible file storage, API, worker, scheduler, frontend, and reverse proxy. `.env.example` documents configuration names without real credentials.
- `DEPLOYMENT.md` documents local and production-shaped startup, environment/secrets, backup/restore expectations, evaluation workflow, and embedding reindex procedure. Production deployment, object-store integration, and backup/restore remain unverified against a real target account.

## 13. Latest verification and remaining environmental blockers

- Latest local checks: `python -m compileall -q app`, Alembic head check (`d9a84c1f2b70`), offline SQL generation for the full migration chain, frontend `npm run build`, local and production Compose `config --quiet`, and `git diff --check` pass.
- The latest hardening-suite rerun passed all 18 tests. It required outbound Hugging Face access to load the cross-encoder; the unauthenticated Hub warning was informational.
- The live evaluation runner previously failed because the database had no `app_settings` table. Applying the new migration requires the local PostgreSQL service, which is not reachable in this session; Docker socket access is also denied. Start the migrated stack to apply the migration and rerun the benchmark.
- No cloud deployment has been performed because no production domain, database, object-store account, or deployment credentials were supplied. Production Compose configuration validates, but this is not equivalent to a deployed or integration-tested production system.

## 14. RAG answer precision and evaluation diagnostics (2026-10-12)

### `backend/app/services/rag.py`

- Tightened the shared system prompt for compact answers: direct definitions/facts should fit in one sentence and 35 words, and must not have an extra trailing source list. The instructions preserve inline `[Source N]` citations and evidence-only answering for both normal and streaming generation.
- `verify_citations()` now removes a redundant trailing `Sources: 1, 2` footer before checking citations. The cleanup is limited to a source-list suffix, so citations attached to the answer body continue through normal validation and only cited, valid source records are returned.

### `backend/app/evaluation/evaluator.py` and `frontend/src/pages/Evaluations.tsx`

- Each completed evaluation case now keeps the raw model draft separately from the returned answer. This makes grounding fallbacks diagnosable in stored run results and the Evaluation dashboard.
- Case results now include machine-readable failure reasons for retrieval confidence, retrieval recall/precision, answer F1, keyword recall, citation recall, unexpected fallback, and citation-grounding failures. The dashboard displays those checks with the draft and final answer when they differ.

### `backend/test_hardening.py`

- Added checks for parenthesized and bracketed trailing source-list cleanup while confirming that the answer's inline citation/source mapping remains intact.

### `README.md` and `graphify-out/HANDOFF.md`

- Updated the benchmark instructions to write a uniquely timestamped JSON artifact and a matching `.txt` transcript via `tee`, with `pipefail` so benchmark failures still return a nonzero shell status. Corrected the stale statement that evaluation is not part of CI; the dispatched regression workflow is a CI gate when configured.
- Refreshed the Graphify handoff with current RAG/evaluation changes, latest test counts, and the user's requested benchmark command. The handoff explicitly records that the benchmark itself has not been run in this continuation.

### Verification for this update

- `HF_HUB_OFFLINE=1 ./.venv/bin/python -m unittest test_hardening.py -v` — 23 tests passed. Offline mode avoids unnecessary Hugging Face Hub retries; the locally cached reranker weights were available.
- `./.venv/bin/python -m compileall -q app test_hardening.py` — passed.
- `npm run build` in `frontend/` — passed.
- `git diff --check` — passed.
- The full RAG evaluation benchmark was intentionally left for the user to run. It should write its normal JSON result plus a terminal transcript `.txt` log; a timestamped command is provided in the current handoff.

## 15. Incomplete benchmark handling and Ollama endpoint diagnosis (2026-10-12)

### `backend/app/evaluation/runner.py`

- The user's latest benchmark log showed all 16 generations failing with `LLM generation failed: Connection error`. The runner previously summarized those operational case errors as all-zero evaluation metrics, compared those zeros to a valid baseline, and could persist the invalid run as benchmark history.
- Evaluation runs with zero completed cases or any case errors are now written with `status: incomplete`, skip baseline regression comparison, and are not persisted as a normal `EvaluationRun`. The runner still exits nonzero and keeps the case-level errors in its JSON output so the endpoint can be fixed and retried.

### `backend/test_hardening.py` and `README.md`

- Added unit coverage ensuring failed/partial runs are not considered regression-comparable, while fully completed runs remain comparable.
- Documented that host evaluation defaults to `http://localhost:11434/v1` and that `OLLAMA_BASE_URL` must be overridden if Ollama listens on a different address.

### Diagnosis

- `backend/app/core/config.py` defaults `ollama_base_url` to `http://localhost:11434/v1`. The previous host listener inspection showed Ollama bound to `172.17.0.1:11434`. For a host-run CLI in that setup, the base URL must be `http://172.17.0.1:11434/v1` (confirm with `/v1/models` first). The benchmark was not rerun here.

## 16. Processing retry state and Redis queue protection (2026-10-12)

### `backend/app/tasks.py`

- Processing failures now use the persisted job attempt count to determine the remaining retries. This preserves the retry budget when a task was recovered and re-enqueued as a fresh Celery message.
- During retry backoff, the document remains visibly `processing` and its transient error is cleared. After the final attempt, both job and document become `failed`, and the job gets a completion timestamp and the document receives the error.
- Stale recovery also keeps requeued documents in the `processing` state, so the frontend does not enable chat or manual retry while recovery is underway.

### `infrastructure/docker/docker-compose.production.yml`

- Changed Redis max-memory eviction from `allkeys-lru` to `volatile-lru`. Cache entries are written with TTLs and can be evicted under pressure; Celery's persistent queue keys must not be subject to arbitrary eviction.
- Set the documented PostgreSQL restore script's executable bit so the runbook's `./scripts/restore_postgres.sh` command works.

### Existing incomplete evaluation history

- `backend/app/api/routes/admin.py` marks historical rows with case errors as `incomplete`. `frontend/src/pages/Evaluations.tsx` labels them as operational failures, hides their invalid aggregate score, and excludes them from metric trends/regression claims. The failed run the user already created remains stored for its case-error details but is no longer presented as a valid benchmark score.

### Verification after these changes

- `HF_HUB_OFFLINE=1 ./.venv/bin/python -m unittest test_hardening.py -v` — 26 tests passed.
- `./.venv/bin/python -m compileall -q app test_hardening.py` — passed.
- `npm run build` in `frontend/` — passed.
- Production Compose `config --quiet`, shell syntax for operational scripts, and `git diff --check` — passed.
- No RAG evaluation benchmark was run.

## 17. Remaining operational hardening (2026-10-12)

### Analytics and provider diagnostics

- `backend/app/services/analytics.py` now computes p95 latency using the nearest-rank percentile index; the previous rounding selected the 96th observation for 100 samples.
- `backend/app/services/llm.py` includes the provider/model and next checks (provider URL, service/model, or Gemini key/network) in generation errors, which are captured in local evaluation case-error output. Credentials are not printed.

### CI artifact and deployment details

- The dispatched benchmark in `.github/workflows/ci.yml` now pipes output through `tee` with `pipefail` and uploads both the JSON result and `.txt` transcript, even when the benchmark fails.
- `DEPLOYMENT.md` now includes bucket check/list permissions required by the production S3 readiness check.
- `scripts/restore_postgres.sh` is executable, matching the deployment runbook invocation.

### Verification after the operational hardening

- `HF_HUB_OFFLINE=1 ./.venv/bin/python -m unittest test_hardening.py -v` — 28 tests passed.
- `./.venv/bin/python -m compileall -q app test_hardening.py` — passed.
- `npm run build` in `frontend/` — passed.
- Production Compose config, CI workflow YAML parsing, operational shell syntax, and `git diff --check` — passed.
- The full RAG evaluation remains intentionally unrun; endpoint reachability must first pass `curl -fsS http://172.17.0.1:11434/v1/models` in the user's host environment.

## 19. Admin user status controls (2026-10-13)

- Added `PATCH /admin/users/{user_id}/status` in `backend/app/api/routes/admin.py` so authenticated administrators can deactivate or reactivate user accounts. The route returns 404 for an unknown user and rejects deactivation of the acting admin or any email configured in `ADMIN_EMAILS`.
- The users listing reports `can_change_status` so the frontend hides controls for protected admin accounts. `frontend/src/api/admin.ts` exposes the update request, and `frontend/src/pages/Admin.tsx` provides a pending-aware action, updates the row on success, and reports API errors. Responsive styles are in `frontend/src/App.css`.
- Added route-guard unit tests in `backend/test_hardening.py` for self-protection, configured-admin protection, and activation.
- Verification: hardening suite — 36 tests passed; frontend production build passed. Live admin API use was not verified against the user's running Docker database.

## 20. Authentication and admin route access (2026-10-13)

- `backend/app/api/routes/auth.py` now rejects inactive accounts at login with the same generic 401 response used for invalid credentials, instead of issuing a token that every protected endpoint would reject.
- `backend/app/api/routes/users.py` adds the server-derived `is_admin` flag to `/users/me` through `CurrentUserResponse` in `backend/app/schemas/user.py`. It uses the same `ADMIN_EMAILS` policy as the admin API.
- `frontend/src/context/AuthContext.tsx` loads `/users/me` when a token is present; `AdminRoute.tsx` gates all admin pages, and the header only shows its Administration link to server-identified admins. The backend remains the authorization boundary.
- Added regression coverage that inactive accounts cannot log in or obtain a token. Verification: 37 hardening tests passed, Python compilation passed, and `npm run build` passed. Live authenticated flows still need verification against the user's running stack.

## 21. Website ingestion response size limit (2026-10-13)

- `backend/app/services/web_extraction.py` now streams remote page bodies and caps decoded content at 5 MiB, checking `Content-Length` early and enforcing the same cap as chunks arrive. This prevents a single website ingestion from buffering an unbounded or compressed oversized response in memory. Existing private-address validation and redirect rejection remain in place.
- Added coverage for oversized declared lengths, oversized streamed bodies, and accepted bounded HTML in `backend/test_hardening.py`.
- Verification: hardening suite — 39 tests passed; backend compilation and `git diff --check` passed. No live website fetch or RAG evaluation was run.

## 22. Registration conflict handling (2026-10-13)

- `backend/app/crud/user.py` now normalizes email addresses to lowercase for storage and lookup. Registration checks both email and username before insert and returns HTTP 409 for either collision. A database uniqueness race also rolls back the failed transaction and returns the same conflict response instead of a 500. Login uses the normalized lookup path.
- Added hardening cases for duplicate usernames, database uniqueness races/rollback, and case-normalized email lookup.
- Verification: hardening suite — 42 tests passed; Python compilation passed.

## 18. Startup and chat failure follow-up (2026-10-13)

- Diagnosed the user's streaming chat failure from backend logs: `_retrieval_scope_version()` referenced `DocumentChunk` without importing it, so the answer-cache key construction raised `NameError` before retrieval/generation. Added the model import in `backend/app/services/rag.py` and added a focused unit regression check in `backend/test_hardening.py`.
- Added backend exception logging for unexpected stream-route errors and LLM streaming errors while preserving generic client-facing messages. This makes server traces useful without returning internal exceptions to users.
- Local and production Compose backend healthchecks now use a 120-second `start_period`, matching observed cold starts where model initialization completed before Uvicorn started. Updated `README.md` and `DEPLOYMENT.md` to document the wait and the correct Ollama URL difference for host Python versus Compose containers.
- PostgreSQL restore now validates the dump archive before touching the target and uses `--exit-on-error --single-transaction` so a failed restore rolls back instead of leaving a partially restored database.
- Admin analytics now aggregates totals, daily trends, provider/model usage, and exact nearest-rank p95 in PostgreSQL instead of loading the full query-event history into Python memory. The admin dashboard response shape is unchanged.
- RAG settings validation now returns a clear `ValueError` for non-object updates and non-string provider, fallback, or embedding-model fields, rather than leaking `TypeError` as a 500 response. Added regression cases for these malformed values.
- Verification: `HF_HUB_OFFLINE=1 ./.venv/bin/python -m unittest test_hardening.py -v` — 31 tests passed. Python `compileall`, focused analytics output checks plus PostgreSQL SQL compilation, frontend `npm run build`, local Compose `config --quiet`, operational shell syntax checks, and `git diff --check` passed. An initial test attempt could not fetch missing tokenizer data while outbound DNS was unavailable; the cache became available and the full hardening suite passed offline. The live RAG benchmark was not run.

## 23. Frontend lint cleanup and refreshed project graph (2026-10-13)

- `frontend/src/context/AuthContext.tsx` now clears administrator/loading state directly in login/logout actions rather than synchronously in an effect. Authentication lookup remains asynchronous and guarded against stale completions.
- `frontend/src/pages/Admin.tsx` derives its loading state from the requested and loaded analytics periods. This removes synchronous effect state updates and keeps period changes visibly loading while the request is pending.
- Refreshed `graphify-out/graph.json`, `graphify-out/graph.html`, `graphify-out/GRAPH_REPORT.md`, and labels for the current repository state. See `graphify-out/GRAPH_REPORT.md` and `graphify-out/HANDOFF.md` for the exact graph totals and integrity results. Recomputed label membership signatures and removed only temporary extraction files from that refresh; dated snapshots and stable graph outputs remain.
- Added `npm run lint` to the frontend CI job and documented it alongside the frontend build check. Frontend lint had previously been available locally but was not enforced in CI.
- The shared frontend API client now broadcasts an unauthorized-session event on HTTP 401 responses when a token is present. `AuthProvider` responds by clearing the stored token and admin state, so expired or deactivated accounts are redirected through the normal protected-route login flow instead of staying in a broken authenticated session.
- Verification: all 42 backend hardening tests passed; backend compilation, frontend ESLint, frontend production build, local Compose configuration, and `git diff --check` passed. Production Compose validation needs deployment values such as `APP_DOMAIN`, `S3_BUCKET`, and `ADMIN_EMAILS`. Live database/Ollama integration and the full RAG benchmark remain for user-side verification.

## 24. Empty provider response handling (2026-10-13)

- A live provider smoke test showed that Qwen3 can finish a very small output budget with reasoning text but no answer content. `backend/app/services/llm.py` now treats empty non-streaming and streaming responses as provider failures. A configured fallback can run; without one the existing generic generation error path is used. Streaming records a provider as selected only after it yields answer text.
- Added four mocked regression tests for empty generation/stream responses with and without fallback.
- Verification: 46 backend hardening tests passed and backend compilation passed. The running Compose backend was healthy, `/ready` returned HTTP 200 with database/Redis/storage checks true, and the configured Qwen3 endpoint was reachable at `172.17.0.1:11434`. The backend-container normal and streaming generation helpers both returned `OK` with a regular output budget. The user's full RAG benchmark was not run.
- Refreshed the Graphify graph, report, and HTML visualization after this change. The update preserves existing change-log concepts and lifecycle groupings, adds the empty-provider handling concepts, and passes graph endpoint and hyperedge-member validation.

## 25. Verified remaining acceptance work (2026-10-13)

The repository implementation and local unit/build checks are not equivalent to full product or production acceptance. The remaining work is:

- Run the full RAG evaluation dataset against the intended database/document and reachable provider. Save the structured JSON and terminal `.txt` transcript, inspect case-level failures and baseline deltas, and tune generation/citation/grounding based on measured results. The user will run this benchmark.
- Perform an authenticated end-to-end check of registration/login, upload and worker completion, streaming chat, citation click-through, and persistence after refresh. Verify project/collection assignment, removal, and retrieval scoping, plus admin analytics/evaluation/settings authorization and non-admin denial.
- Exercise Redis outage/fail-open and cache invalidation, Celery retry/recovery with the running worker, and S3-compatible object upload/read/delete/materialization against live integrations. Existing hardening tests do not prove those external-service paths.
- Select a production target and provide its domain, managed PostgreSQL/pgvector, object-storage bucket/permissions, secret-management approach, and LLM provider configuration. Validate and deploy the production Compose stack against those real services.
- Complete an isolated-database backup/restore drill, verify object-storage recovery/retention, and configure external health monitoring and alerts.
- Confirm the GitHub Actions CI result after pushing. The manually dispatched live RAG regression job additionally needs its database/provider secrets and seeded fixture.

Latest local runtime checks found all six Compose services running, backend/PostgreSQL/Redis healthy, `/ready` returning HTTP 200 with all checks true, frontend and API docs returning HTTP 200, and Ollama serving `qwen3:8b`. These checks did not exercise authenticated application flows or production integrations.
