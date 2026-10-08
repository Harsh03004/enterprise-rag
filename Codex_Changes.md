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
