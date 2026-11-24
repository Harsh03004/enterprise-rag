# Graph Report - enterprise-rag  (2026-11-24)

## Corpus Check
- 155 files · ~76,944 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 8, .css 2, .example 1)

## Summary
- 1253 nodes · 2842 edges · 111 communities (74 shown, 37 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 156 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6898754d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Frontend Chat & API Clients
- collections.py
- IngestionBoundaryTests
- typing
- package.json
- llm.py
- local backend service (FastAPI + alembic)
- _patch_pipeline
- calibrate_grounding.py
- rag.py
- text_extraction.py
- conversations.py
- logging.py
- sqlalchemy
- users.py
- runner.py
- test_hardening.py
- ChatContractTests
- compilerOptions
- Document
- test_evaluation.py
- App.tsx
- corpus.py
- grounding.py
- admin.ts
- compilerOptions
- schemas/user.py
- test_grounding.py
- react
- get_rag_config
- evaluator.py
- AdminContent.tsx
- api/auth.ts
- schemas/chat.py
- ground_answer
- Remaining Product Acceptance Work
- search_similar_chunks
- compare_summaries
- split_sentences
- build_context_and_sources
- RagOutcome
- DocumentChunk
- Passwords and MFA rules (14-char minimum)
- Evaluations.tsx
- AdminSettings.tsx
- config.py
- Empty Provider Response Handling
- verify_password
- run_evaluation.sh
- User
- lexically_supported
- LexicalSupportTests
- types/auth.ts
- AdminContentTests
- Bluesky Icon
- Stacked rounded layers visual motif
- tsconfig.json
- maintenance/__init__.py
- Graphify Output Refresh and Integrity Verification
- Abstract Gradient Lightning Mark
- backup_postgres.sh
- restore_postgres.sh
- CI frontend job (lint + build)
- Orion installation requirements
- Orion software and firmware support
- Frontend Structure Inventory
- Enterprise RAG Application Metadata
- Documentation Icon
- Social Profile Icon
- Frontend Documentation
- React Logo
- Vite Logo
- backend
- test_rag_pipeline.py
- document_service.py
- main.py
- Northwind Analytics Employee Handbook
- Enterprise RAG
- documents.py
- upload_document
- _load_resumable
- Free self-hosted deployment (Oracle Cloud Always Free + DuckDNS)
- crud/document.py
- Installing the tools
- Manual RAG test cases
- 9f6316708db3_add_embeddings_to_document_chunks.py
- load_dataset
- verify_citations
- reranking.py
- Deployment Runbook
- evaluation service (runs app.evaluation.runner)
- production backend service
- Docker in detail
- evidence_units
- Running without Docker (local development)
- Choosing an LLM provider
- Security incident severity levels (SEV-1..3)
- backup_selfhost.sh
- CI backend job (compile + unit tests)
- Access reviews
- Device rules (encryption, laptop wipe within 24h)
- Northwind Analytics IT Security Policy
- Orion Cloud subscription plans table
- Orion X2 vs X1 hardware comparison table
- Orion Smart Thermostat Product Specification

## God Nodes (most connected - your core abstractions)
1. `User` - 56 edges
2. `Document` - 42 edges
3. `apiFetch()` - 41 edges
4. `Sidebar()` - 36 edges
5. `ChatContractTests` - 30 edges
6. `Base` - 23 edges
7. `stream_answer()` - 23 edges
8. `ground_answer()` - 22 edges
9. `Layout()` - 22 edges
10. `DocumentChunk` - 19 edges

## Surprising Connections (you probably didn't know these)
- `CI rag-regression job (manual live benchmark)` --semantically_similar_to--> `evaluation service (runs app.evaluation.runner)`  [INFERRED] [semantically similar]
  .github/workflows/ci.yml → infrastructure/docker/docker-compose.evaluation.yml
- `CI rag-regression job (manual live benchmark)` --implements--> `RAG evaluation`  [INFERRED]
  .github/workflows/ci.yml → README.md
- `production backend service` --semantically_similar_to--> `local backend service (FastAPI + alembic)`  [INFERRED] [semantically similar]
  infrastructure/docker/docker-compose.production.yml → infrastructure/docker/docker-compose.yml
- `get_current_user()` --uses--> `User`  [INFERRED]
  backend/app/api/dependencies.py → backend/app/models/user.py
- `admin_summary()` --uses--> `Document`  [INFERRED]
  backend/app/api/routes/admin.py → backend/app/models/document.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Document Ingestion and Storage Lifecycle** — codex_changes_document_ingestion_and_processing, codex_changes_document_intelligence_and_object_storage, codex_changes_website_ingestion_response_limit [EXTRACTED 1.00]
- **Identity and Access Lifecycle** — codex_changes_authentication_and_admin_access, codex_changes_registration_conflict_handling, codex_changes_frontend_session_expiry_handling [EXTRACTED 1.00]
- **RAG Quality, Evaluation, and Provider Response Lifecycle** — codex_changes_rag_retrieval_context_citation_grounding, codex_changes_evaluation_regression_workflow, codex_changes_admin_analytics_and_runtime_settings, codex_changes_empty_provider_response_handling, codex_changes_empty_generation_validation, codex_changes_empty_stream_validation, codex_changes_llm_provider_fallback, codex_changes_empty_response_regression_tests, codex_changes_qwen3_live_smoke_verification [EXTRACTED 1.00]
- **Single-host production stack services** — infrastructure_docker_docker_compose_production_redis, infrastructure_docker_docker_compose_production_backend, infrastructure_docker_docker_compose_production_worker, infrastructure_docker_docker_compose_production_scheduler, infrastructure_docker_docker_compose_production_frontend, infrastructure_docker_docker_compose_production_proxy [EXTRACTED 1.00]
- **Social and community platform icons** — frontend_public_icons_bluesky_icon, frontend_public_icons_discord_icon, frontend_public_icons_github_icon, frontend_public_icons_x_icon [INFERRED 0.75]

## Communities (111 total, 37 thin omitted)

### Community 0 - "Frontend Chat & API Clients"
Cohesion: 0.05
Nodes (66): ChatSource, ChatStreamEvent, streamChat(), StreamChatOptions, apiFetch(), Collection, createCollection(), deleteCollection() (+58 more)

### Community 1 - "collections.py"
Cohesion: 0.20
Nodes (20): create_new_collection(), list_user_collections(), delete, get, patch, post, Session, remove_collection() (+12 more)

### Community 2 - "IngestionBoundaryTests"
Cohesion: 0.12
Nodes (12): _read_bounded_html(), validate_url(), Update job/document state and return retries left after this attempt., _record_processing_failure(), IngestionBoundaryTests, bs4, Exception, httpx (+4 more)

### Community 4 - "package.json"
Cohesion: 0.05
Nodes (44): dependencies, react, react-dom, react-markdown, react-router-dom, remark-gfm, devDependencies, eslint (+36 more)

### Community 5 - "llm.py"
Cohesion: 0.18
Nodes (15): generate_response(), _get_client(), _messages(), _provider_failure_hint(), Stream an LLM response token by token. The function yields only non-empty text…, Chat messages for one request. Qwen3 models "think" before answering by…, Provider-specific request parameters. Gemini 2.5 Flash/Flash-Lite think by…, Return the configured LLM client and model. Supported providers: - gemini -… (+7 more)

### Community 6 - "local backend service (FastAPI + alembic)"
Cohesion: 0.43
Nodes (7): local backend service (FastAPI + alembic), local frontend service (nginx), local postgres service (pgvector pg17), local redis service, local scheduler service (Celery beat), uploaded_files volume (shared by API and worker), local worker service (Celery)

### Community 7 - "_patch_pipeline"
Cohesion: 0.22
Nodes (6): ChatEntryPointTests, _patch_pipeline(), PipelineTestCase, Starlette runs each generator step in a fresh context copy (the bug that stored…, Patch retrieval, generation and grounding around the real orchestration., RunRagPipelineTests

### Community 8 - "calibrate_grounding.py"
Cohesion: 0.13
Nodes (22): evaluate_case(), Run one case through the same pipeline chat uses, without persistence., contains_phrase(), forbidden_hits(), matched_facts(), normalize_text(), Deterministic scoring functions for RAG evaluation., Lowercase, replace punctuation with spaces and collapse whitespace. (+14 more)

### Community 9 - "rag.py"
Cohesion: 0.16
Nodes (29): add_message(), extract_document_reference(), find_documents(), Session, get_last_used_provider(), reset_last_used_provider(), answer_question(), begin_rag_request() (+21 more)

### Community 10 - "text_extraction.py"
Cohesion: 0.08
Nodes (29): extract_docx(), extract_docx_images(), extract_pdf(), extract_pdf_page_blocks(), extract_pdf_pages(), extract_text(), extract_text_blocks(), is_usable_text() (+21 more)

### Community 11 - "conversations.py"
Cohesion: 0.19
Nodes (24): create_new_conversation(), get_conversation_detail(), list_user_conversations(), delete, get, patch, post, Session (+16 more)

### Community 12 - "logging.py"
Cohesion: 0.13
Nodes (15): configure_logging(), JsonFormatter, Structured logging shared by the API and the Celery worker. Every record…, RequestIdFilter, _bind_task_id(), _configure_worker_logging(), _unbind_task_id(), JsonLoggingTests (+7 more)

### Community 13 - "sqlalchemy"
Cohesion: 0.26
Nodes (11): Run migrations in 'offline' mode. This configures the context with just a URL…, Run migrations in 'online' mode. In this scenario we need to create an Engine…, run_migrations_offline(), run_migrations_online(), Base, Message, datetime, DeclarativeBase (+3 more)

### Community 14 - "users.py"
Cohesion: 0.15
Nodes (17): get_current_admin(), get_current_user(), Session, get_me(), is_admin_email(), decode_access_token(), get_db(), Session (+9 more)

### Community 15 - "runner.py"
Cohesion: 0.14
Nodes (16): argparse, LlmCache, Path, Local cache of LLM drafts for evaluation runs. Generation is the only step of…, _can_compare_regression(), _fmt(), main(), _print_case() (+8 more)

### Community 16 - "test_hardening.py"
Cohesion: 0.14
Nodes (19): login(), post, Session, register_user(), create_access_token(), hash_password(), create_user(), get_user_by_email() (+11 more)

### Community 17 - "ChatContractTests"
Cohesion: 0.14
Nodes (4): patch, update_admin_user_status(), validate_user_status_change(), ChatContractTests

### Community 18 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 19 - "Document"
Cohesion: 0.22
Nodes (13): main(), Document, ProcessingJob, process_document(), Session, materialize_uploaded_file(), Yield a local path for parser libraries, downloading S3 objects to a temp file…, generate_embedding() (+5 more)

### Community 20 - "test_evaluation.py"
Cohesion: 0.13
Nodes (12): chunk_relevance(), citation_scores(), passage_in_text(), Whether a labelled evidence quote appears in a chunk (whitespace/case-…, Map each (filename, content) chunk to the indexes of passages it contains., Retrieval quality for one ranked list, given per-chunk relevance sets.…, Precision/recall of cited [Source N] labels against sources holding evidence.…, retrieval_scores() (+4 more)

### Community 21 - "App.tsx"
Cohesion: 0.22
Nodes (13): login(), register(), AdminRoute(), Header(), HeaderProps, ProtectedRoute(), ProtectedRouteProps, useAuth() (+5 more)

### Community 22 - "corpus.py"
Cohesion: 0.19
Nodes (16): asyncio, corpus_fingerprint(), CorpusScope, ensure_corpus(), _evaluation_collection(), _evaluation_user(), _ingest_file(), Path (+8 more)

### Community 23 - "grounding.py"
Cohesion: 0.16
Nodes (17): _best_support(), _context_prefix(), _cosine(), _document_label(), entailment_scores(), _hypothesis(), _load_entailment_model(), Sentence-level grounding of generated answers. Every factual sentence in an… (+9 more)

### Community 24 - "admin.ts"
Cohesion: 0.21
Nodes (14): AdminAnalytics, AdminSummary, AdminUser, AnalyticsPoint, DocumentStatus, EvaluationSummary, getAdminAnalytics(), getAdminSummary() (+6 more)

### Community 25 - "compilerOptions"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 26 - "schemas/user.py"
Cohesion: 0.42
Nodes (8): CurrentUserResponse, PasswordChange, BaseModel, UserBase, UserCreate, UserLogin, UsernameUpdate, UserResponse

### Community 27 - "test_grounding.py"
Cohesion: 0.17
Nodes (7): CitationFormatTests, fake_embeddings(), fake_entailment(), FinalizeAnswerTests, recording(), GroundingTestCase, Tests for sentence-level grounding (the entailment model is replaced by a stub).

### Community 28 - "react"
Cohesion: 0.18
Nodes (9): AUTH_EXPIRED_EVENT, App(), AuthContext, AuthContextType, TOKEN_KEY, AuthProvider(), frontend_src_index, react (+1 more)

### Community 29 - "get_rag_config"
Cohesion: 0.17
Nodes (14): chat(), chat_stream(), event_generator(), post, Session, QueryEvent, get_admin_analytics(), get_query_summary() (+6 more)

### Community 30 - "evaluator.py"
Cohesion: 0.20
Nodes (11): Evaluation dataset format (version 2). A dataset is a JSON object:: {…, EvaluationResult, _median_words(), Score evaluation cases against the production RAG pipeline., Aggregate scores; each metric averages only the cases it applies to., summarize_results(), average(), extract_citation_ids() (+3 more)

### Community 31 - "AdminContent.tsx"
Cohesion: 0.26
Nodes (13): AdminCollection, AdminDocument, deleteAdminCollection(), deleteAdminDocument(), getAdminCollections(), getAdminDocuments(), retryAdminDocument(), AdminContent() (+5 more)

### Community 32 - "api/auth.ts"
Cohesion: 0.29
Nodes (12): changePassword(), CurrentUser, getCurrentUser(), LoginRequest, LoginResponse, RegisterRequest, updateUsername(), User (+4 more)

### Community 33 - "schemas/chat.py"
Cohesion: 0.47
Nodes (4): ChatRequest, ChatResponse, ChatSource, BaseModel

### Community 34 - "ground_answer"
Cohesion: 0.24
Nodes (5): ground_answer(), Replace a sentence's citations with one citation, before final punctuation., Keep only answer sentences that a source entails; fix or drop the rest., _with_citation(), GroundAnswerTests

### Community 35 - "Remaining Product Acceptance Work"
Cohesion: 0.18
Nodes (13): Admin Analytics and Runtime RAG Settings, Authentication and Admin Access Controls, Document Ingestion and Processing Reliability, Document Intelligence and Object Storage, Evaluation Regression Workflow and Diagnostics, Frontend Lint CI Gate, Frontend Expired Session Recovery, Incomplete Evaluation Run Handling (+5 more)

### Community 36 - "search_similar_chunks"
Cohesion: 0.33
Nodes (6): keyword_query(), overview_chunks(), Session, Opening chunks of the most recent documents in scope, in reading order., OR-combine the question's words for websearch_to_tsquery. Stop words are…, search_similar_chunks()

### Community 37 - "compare_summaries"
Cohesion: 0.10
Nodes (3): compare_summaries(), RegressionTests, collections_abc

### Community 38 - "split_sentences"
Cohesion: 0.38
Nodes (4): _clean_claim(), Split an answer into sentences with character spans into the original text., split_sentences(), SegmentationTests

### Community 39 - "build_context_and_sources"
Cohesion: 0.13
Nodes (14): build_context(), build_context_and_sources(), build_rag_prompt(), build_sources(), group_results_by_document(), prepare_generation(), prepare_results(), Remove duplicate/empty chunks while preserving relevance. This is shared by… (+6 more)

### Community 40 - "RagOutcome"
Cohesion: 0.22
Nodes (7): EvaluationCase, Passage, RagOutcome, Result of one pipeline run, before persistence or caching. status is one of:…, DatasetValidationTests, EvaluateCaseTests, _ranked()

### Community 41 - "DocumentChunk"
Cohesion: 0.21
Nodes (10): create_document_chunk(), create_document_chunks(), Session, DocumentChunk, chunk_text(), chunk_text_with_metadata(), ChunkData, embed_document_chunk() (+2 more)

### Community 43 - "Evaluations.tsx"
Cohesion: 0.31
Nodes (9): EvaluationRun, EvaluationRunSummary, getEvaluationRun(), getEvaluationRuns(), Evaluations(), selectRun(), formatMetric(), METRICS (+1 more)

### Community 44 - "AdminSettings.tsx"
Cohesion: 0.29
Nodes (7): getRagSettings(), RagSettings, updateRagSettings(), AdminNav(), LINKS, AdminSettings(), save()

### Community 45 - "config.py"
Cohesion: 0.28
Nodes (10): Any, Settings, cache_get(), cache_key(), cache_set(), generate_embeddings(), _load_model(), BaseSettings (+2 more)

### Community 46 - "Empty Provider Response Handling"
Cohesion: 0.25
Nodes (9): Empty Non-streaming Generation Validation, Empty Provider Response Handling, Empty-response Regression Tests, Empty Streaming Response Validation, Configured LLM Provider Fallback, LLM Provider Configuration and Docker Connectivity, Qwen3 Live Smoke Verification, RAG Retrieval, Context, Citation, and Grounding (+1 more)

### Community 47 - "verify_password"
Cohesion: 0.14
Nodes (9): change_password(), get_my_analytics(), get, patch, post, Session, update_me(), verify_password() (+1 more)

### Community 48 - "run_evaluation.sh"
Cohesion: 0.38
Nodes (5): env_value(), EVAL_MEMORY, OLLAMA_MEMORY, run_evaluation.sh script, to_mb()

### Community 49 - "User"
Cohesion: 0.28
Nodes (20): admin_analytics(), admin_collections(), admin_delete_collection(), admin_delete_document(), admin_documents(), admin_retry_document(), admin_summary(), admin_users() (+12 more)

### Community 50 - "lexically_supported"
Cohesion: 0.40
Nodes (6): lexically_supported(), Crude suffix stripping so "storing"/"stores"/"stored" match "store"., Crude suffix stripping so "enables"/"enable"/"enabled" match. Numbers are…, Every number and nearly every content word of the claim appears in the source.…, _stem(), _tokens()

### Community 52 - "types/auth.ts"
Cohesion: 0.40
Nodes (4): LoginRequest, RegisterRequest, TokenResponse, User

### Community 54 - "Bluesky Icon"
Cohesion: 1.00
Nodes (4): Bluesky Icon, Discord Icon, GitHub Icon, X Icon

### Community 55 - "Stacked rounded layers visual motif"
Cohesion: 0.67
Nodes (3): Hero illustration, Purple-accented lower layer, Stacked rounded layers visual motif

### Community 79 - "test_rag_pipeline.py"
Cohesion: 0.10
Nodes (11): GroundingResult, has_sufficient_confidence(), Determine whether the strongest retrieved chunk is relevant enough to support…, Page numbers a question refers to ("page 3", "p. 3", "pages 2-4", "pages 2 and…, requested_pages(), ConfidenceGateTests, LlmMessageTests, OverviewQuestionTests (+3 more)

### Community 80 - "document_service.py"
Cohesion: 0.17
Nodes (11): UploadFile, Remove an uploaded file only when its resolved path is inside storage., remove_uploaded_file(), _s3_client(), sanitize_filename(), save_uploaded_file(), validate_upload_filename(), boto3 (+3 more)

### Community 81 - "main.py"
Cohesion: 0.18
Nodes (13): health(), get, readiness(), request_logging_middleware(), root(), check_storage_ready(), fastapi_middleware_cors, fastapi_responses (+5 more)

### Community 82 - "Northwind Analytics Employee Handbook"
Cohesion: 0.17
Nodes (11): Annual Leave, Equipment, Expenses, Leave, Northwind Analytics Employee Handbook, Parental Leave, Probation and Notice, Remote Work (+3 more)

### Community 83 - "Enterprise RAG"
Cohesion: 0.18
Nodes (11): Configuration reference, Contents, Enterprise RAG, Features, How it works, Production deployment, Project structure, Quick start with Docker (recommended) (+3 more)

### Community 84 - "documents.py"
Cohesion: 0.42
Nodes (8): patch, rename_document(), update_document_collection_route(), DocumentCollectionUpdate, DocumentResponse, DocumentUpdate, DocumentURLCreate, BaseModel

### Community 85 - "upload_document"
Cohesion: 0.29
Nodes (10): ingest_url(), list_documents(), get, post, Session, UploadFile, retry_document_processing(), upload_document() (+2 more)

### Community 86 - "_load_resumable"
Cohesion: 0.27
Nodes (6): _load_resumable(), Path, Write a complete checkpoint without leaving a truncated result file., Completed results from an earlier run with identical settings, if any., _write_json_atomic(), ResumeTests

### Community 87 - "Free self-hosted deployment (Oracle Cloud Always Free + DuckDNS)"
Cohesion: 0.20
Nodes (10): 1. Create the server (Oracle Cloud console), 2. Point a free domain at it (DuckDNS), 3. Prepare the server, 4. Get the code and configure it, 5. Start it, 6. Daily backups, 7. Updating, Free self-hosted deployment (Oracle Cloud Always Free + DuckDNS) (+2 more)

### Community 88 - "crud/document.py"
Cohesion: 0.42
Nodes (8): delete, remove_document(), create_document(), delete_document(), get_document(), Session, update_document_collection(), update_document_filename()

### Community 89 - "Installing the tools"
Cohesion: 0.22
Nodes (9): Docker and Docker Compose, Git, Installing the tools, Node.js 22, Ollama (optional, for a local LLM), PostgreSQL 17 with pgvector, Python 3.12 and uv, Redis 7 (+1 more)

### Community 90 - "Manual RAG test cases"
Cohesion: 0.25
Nodes (7): Employee handbook, Employee handbook + IT security policy, IT security policy, Manual RAG test cases, Orion spec (PDF), Should refuse (not in any document), StuMeet report

### Community 92 - "load_dataset"
Cohesion: 0.29
Nodes (5): EvaluationDataset, load_dataset(), Path, DatasetIntegrityTests, Labels must stay valid against the committed corpus and real chunking.

### Community 93 - "verify_citations"
Cohesion: 0.29
Nodes (4): normalize_citation_groups(), Rewrite "[Source 1, Source 2]" / "[1, 2]" / "[Sources 1 and 2]" as "[Source 1]…, Verify that every [Source N] citation in the answer refers to a source that…, verify_citations()

### Community 94 - "reranking.py"
Cohesion: 0.33
Nodes (5): passage_windows(), Overlapping windows of a few sentences/lines from a chunk., Rank chunks by their best-matching passage. A 400-token chunk often mixes…, rerank_chunks(), sentence_transformers

### Community 95 - "Deployment Runbook"
Cohesion: 0.29
Nodes (5): Backups and restore testing, CI and benchmark regression, Deployment Runbook, Local stack, Single-host production deployment (managed PostgreSQL and S3)

### Community 96 - "evaluation service (runs app.evaluation.runner)"
Cohesion: 0.33
Nodes (6): CI rag-regression job (manual live benchmark), evaluation service (runs app.evaluation.runner), ollama-cpu service (GPU-less, resource-capped Ollama), RAG evaluation, Tests and evaluation, Unit tests

### Community 97 - "production backend service"
Cohesion: 0.47
Nodes (6): production backend service, production frontend service, Caddy proxy service (HTTPS), production redis (volatile-lru, appendonly), production scheduler service (Celery beat), production worker service

### Community 98 - "Docker in detail"
Cohesion: 0.33
Nodes (6): Applying a changed `.env`, Building the images by hand, Common commands, Docker in detail, Running the images with `docker run` (without Compose), Services in the local stack

### Community 100 - "Running without Docker (local development)"
Cohesion: 0.50
Nodes (4): 1. Database and cache, 2. Backend, 3. Frontend, Running without Docker (local development)

### Community 101 - "Choosing an LLM provider"
Cohesion: 0.50
Nodes (4): Choosing an LLM provider, Google Gemini (simplest, free tier available), Ollama (fully local, no API key), OpenRouter (many hosted models, some free)

### Community 102 - "Security incident severity levels (SEV-1..3)"
Cohesion: 0.67
Nodes (3): Data classification levels, Security incident severity levels (SEV-1..3), Lost or stolen devices (report within 1 hour)

## Knowledge Gaps
- **190 isolated node(s):** `backend`, `name`, `private`, `version`, `type` (+185 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 450 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **37 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `collections.py`, `calibrate_grounding.py`, `conversations.py`, `sqlalchemy`, `users.py`, `verify_password`, `test_hardening.py`, `ChatContractTests`, `documents.py`, `upload_document`, `corpus.py`, `crud/document.py`, `get_rag_config`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `Document` connect `Document` to `search_similar_chunks`, `calibrate_grounding.py`, `rag.py`, `text_extraction.py`, `sqlalchemy`, `User`, `documents.py`, `upload_document`, `corpus.py`, `crud/document.py`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Are the 41 inferred relationships involving `User` (e.g. with `get_current_user()` and `admin_analytics()`) actually correct?**
  _`User` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `Document` (e.g. with `admin_collections()` and `admin_delete_document()`) actually correct?**
  _`Document` has 26 INFERRED edges - model-reasoned connections that need verification._
- **What connects `backend`, `name`, `private` to the rest of the system?**
  _190 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Frontend Chat & API Clients` be split into smaller, more focused modules?**
  _Cohesion score 0.053235653235653234 - nodes in this community are weakly interconnected._
- **Should `IngestionBoundaryTests` be split into smaller, more focused modules?**
  _Cohesion score 0.12105263157894737 - nodes in this community are weakly interconnected._