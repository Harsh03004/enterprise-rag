# Graph Report - enterprise-rag  (2026-11-20)

## Corpus Check
- 167 files · ~75,106 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 8, .css 2, .example 1)

## Summary
- 1198 nodes · 2797 edges · 79 communities (52 shown, 27 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 167 edges (avg confidence: 0.92)
- Token cost: 91,094 input · 0 output

## Community Hubs (Navigation)
- Frontend Chat & API Clients
- Admin API Routes
- App Entry & Storage Service
- Early Schema Migrations
- Frontend Tooling & Packages
- Later Schema Migrations
- Eval Corpus & CI Jobs
- Reranking & Grounding Results
- Evaluation Scoring
- RAG Answer Pipeline
- Text Extraction & OCR
- Conversation Routes
- Structured Logging & Worker
- Migration Env & Base Models
- Auth Dependencies & Chat Route
- Eval Runner & LLM Cache
- Auth Routes & JWT
- Citation Normalization & Contract Tests
- TS App Config
- Settings & Document Processing
- Eval Metrics & Regression
- Frontend Routing & Header
- Eval Corpus Loader
- Entailment Grounding Core
- Admin API Client
- TS Node Config
- User Account Routes
- Grounding Format Tests
- Frontend Auth Context
- Chat Stream & Query Analytics
- Eval Dataset Format
- Admin Content Page
- Auth API Client
- Chat Schemas & Hardening Tests
- Answer Grounding Tests
- Codex Hardening Changelog
- Retrieval & Embedding Service
- Grounding Calibration
- Answer Sentence Segmentation
- Context Building
- Evaluate Case Tests
- Chunking & Chunk CRUD
- RAG Pipeline Concepts
- Evaluations Page
- Admin Settings & Nav
- Embeddings & Redis Cache
- LLM Fallback Changelog
- Account Settings Tests
- Local Evaluation Script
- Auth Schemas
- Lexical Support Check
- Lexical Support Tests
- Auth Types
- Admin Content Tests
- Social Icons
- Hero Illustration
- TS Root Config
- Maintenance Package
- Codex Change Record
- Favicon
- Postgres Backup Script
- Postgres Restore Script
- CI Frontend Job
- Orion Installation
- Orion Software Support
- Frontend Structure Inventory
- App Metadata
- Documentation Icon
- Social Profile Icon
- Frontend Docs
- React Logo
- Vite Logo
- Backend Root

## God Nodes (most connected - your core abstractions)
1. `User` - 56 edges
2. `Document` - 41 edges
3. `apiFetch()` - 41 edges
4. `Sidebar()` - 36 edges
5. `ChatContractTests` - 30 edges
6. `Base` - 23 edges
7. `stream_answer()` - 23 edges
8. `ground_answer()` - 22 edges
9. `Layout()` - 22 edges
10. `DocumentChunk` - 18 edges

## Surprising Connections (you probably didn't know these)
- `CI rag-regression job (manual live benchmark)` --semantically_similar_to--> `evaluation service (runs app.evaluation.runner)`  [INFERRED] [semantically similar]
  .github/workflows/ci.yml → infrastructure/docker/docker-compose.evaluation.yml
- `Orion X2 vs X1 hardware comparison table` --conceptually_related_to--> `Ingestion pipeline (extraction, OCR, ~400-token chunking, bge-small embeddings)`  [INFERRED]
  backend/evaluation/corpus/orion_thermostat_spec.pdf → README.md
- `RAG evaluation (75 questions, baseline regression)` --references--> `Orion Smart Thermostat Product Specification`  [EXTRACTED]
  README.md → backend/evaluation/corpus/orion_thermostat_spec.pdf
- `Near-miss test cases (must-not-say values)` --conceptually_related_to--> `Page-aware retrieval`  [AMBIGUOUS]
  backend/evaluation/MANUAL_TEST_CASES.md → README.md
- `CI rag-regression job (manual live benchmark)` --implements--> `RAG evaluation (75 questions, baseline regression)`  [INFERRED]
  .github/workflows/ci.yml → README.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Document Ingestion and Storage Lifecycle** — codex_changes_document_ingestion_and_processing, codex_changes_document_intelligence_and_object_storage, codex_changes_website_ingestion_response_limit [EXTRACTED 1.00]
- **Identity and Access Lifecycle** — codex_changes_authentication_and_admin_access, codex_changes_registration_conflict_handling, codex_changes_frontend_session_expiry_handling [EXTRACTED 1.00]
- **RAG Quality, Evaluation, and Provider Response Lifecycle** — codex_changes_rag_retrieval_context_citation_grounding, codex_changes_evaluation_regression_workflow, codex_changes_admin_analytics_and_runtime_settings, codex_changes_empty_provider_response_handling, codex_changes_empty_generation_validation, codex_changes_empty_stream_validation, codex_changes_llm_provider_fallback, codex_changes_empty_response_regression_tests, codex_changes_qwen3_live_smoke_verification [EXTRACTED 1.00]
- **Social and community platform icons** — frontend_public_icons_bluesky_icon, frontend_public_icons_discord_icon, frontend_public_icons_github_icon, frontend_public_icons_x_icon [INFERRED 0.75]
- **RAG query pipeline: rewrite -> hybrid search -> rerank -> confidence gate -> grounding** — readme_query_rewriting, readme_hybrid_search, readme_cross_encoder_reranking, readme_confidence_gate, readme_grounding_check [EXTRACTED 1.00]
- **Fixed evaluation corpus documents** — backend_evaluation_corpus_northwind_employee_handbook_handbook, backend_evaluation_corpus_northwind_it_security_policy_policy, backend_evaluation_corpus_orion_thermostat_spec_spec, backend_evaluation_manual_test_cases_stumeet_report [EXTRACTED 1.00]
- **Single-host production stack services** — infrastructure_docker_docker_compose_production_redis, infrastructure_docker_docker_compose_production_backend, infrastructure_docker_docker_compose_production_worker, infrastructure_docker_docker_compose_production_scheduler, infrastructure_docker_docker_compose_production_frontend, infrastructure_docker_docker_compose_production_proxy [EXTRACTED 1.00]

## Communities (79 total, 27 thin omitted)

### Community 0 - "Frontend Chat & API Clients"
Cohesion: 0.05
Nodes (66): ChatSource, ChatStreamEvent, streamChat(), StreamChatOptions, apiFetch(), Collection, createCollection(), deleteCollection() (+58 more)

### Community 1 - "Admin API Routes"
Cohesion: 0.07
Nodes (81): get_current_admin(), admin_analytics(), admin_collections(), admin_delete_collection(), admin_delete_document(), admin_documents(), admin_retry_document(), admin_summary() (+73 more)

### Community 2 - "App Entry & Storage Service"
Cohesion: 0.05
Nodes (33): health(), get, readiness(), request_logging_middleware(), root(), check_storage_ready(), materialize_uploaded_file(), Yield a local path for parser libraries, downloading S3 objects to a temp file… (+25 more)

### Community 4 - "Frontend Tooling & Packages"
Cohesion: 0.05
Nodes (44): dependencies, react, react-dom, react-markdown, react-router-dom, remark-gfm, devDependencies, eslint (+36 more)

### Community 5 - "Later Schema Migrations"
Cohesion: 0.06
Nodes (18): LlmCache, Path, generate_response(), _get_client(), _messages(), _provider_failure_hint(), Stream an LLM response token by token. The function yields only non-empty text…, Chat messages for one request. Qwen3 models "think" before answering by… (+10 more)

### Community 6 - "Eval Corpus & CI Jobs"
Cohesion: 0.06
Nodes (44): CI backend job (compile + unit tests), CI rag-regression job (manual live benchmark), Equipment return policy, Northwind Analytics Employee Handbook, Remote Work policy, Access reviews, Data classification levels, Device rules (encryption, laptop wipe within 24h) (+36 more)

### Community 7 - "Reranking & Grounding Results"
Cohesion: 0.09
Nodes (16): GroundingResult, has_sufficient_confidence(), passage_windows(), Overlapping windows of a few sentences/lines from a chunk., Determine whether the strongest retrieved chunk is relevant enough to support…, ChatEntryPointTests, ConfidenceGateTests, PageReferenceTests (+8 more)

### Community 8 - "Evaluation Scoring"
Cohesion: 0.10
Nodes (29): evaluate_case(), EvaluationResult, _median_words(), Score evaluation cases against the production RAG pipeline., Aggregate scores; each metric averages only the cases it applies to., Run one case through the same pipeline chat uses, without persistence., summarize_results(), average() (+21 more)

### Community 9 - "RAG Answer Pipeline"
Cohesion: 0.13
Nodes (33): extract_document_reference(), find_documents(), Session, get_last_used_provider(), reset_last_used_provider(), answer_question(), begin_rag_request(), _bind_timings() (+25 more)

### Community 10 - "Text Extraction & OCR"
Cohesion: 0.08
Nodes (27): extract_docx(), extract_docx_images(), extract_pdf(), extract_pdf_page_blocks(), extract_pdf_pages(), extract_text(), is_usable_text(), ocr_page() (+19 more)

### Community 11 - "Conversation Routes"
Cohesion: 0.18
Nodes (26): create_new_conversation(), get_conversation_detail(), list_user_conversations(), delete, get, patch, post, Session (+18 more)

### Community 12 - "Structured Logging & Worker"
Cohesion: 0.13
Nodes (14): configure_logging(), JsonFormatter, RequestIdFilter, _bind_task_id(), _configure_worker_logging(), _unbind_task_id(), JsonLoggingTests, Tests for structured logging and request-ID propagation. (+6 more)

### Community 13 - "Migration Env & Base Models"
Cohesion: 0.28
Nodes (10): Run migrations in 'offline' mode. This configures the context with just a URL…, Run migrations in 'online' mode. In this scenario we need to create an Engine…, run_migrations_offline(), run_migrations_online(), Base, datetime, DeclarativeBase, logging_config (+2 more)

### Community 14 - "Auth Dependencies & Chat Route"
Cohesion: 0.15
Nodes (14): get_current_user(), Session, decode_access_token(), get_db(), Session, FakeDb, Account settings: username and password changes (no database)., Admin content endpoints: access control and filter validation (no database). (+6 more)

### Community 15 - "Eval Runner & LLM Cache"
Cohesion: 0.15
Nodes (16): Local cache of LLM drafts for evaluation runs. Generation is the only step of…, _fmt(), _load_resumable(), main(), _print_case(), _print_summary(), Path, Run the RAG evaluation suite. uv run python -m app.evaluation.runner # full… (+8 more)

### Community 16 - "Auth Routes & JWT"
Cohesion: 0.21
Nodes (13): login(), post, Session, register_user(), create_access_token(), hash_password(), create_user(), get_user_by_email() (+5 more)

### Community 17 - "Citation Normalization & Contract Tests"
Cohesion: 0.11
Nodes (5): normalize_citation_groups(), Rewrite "[Source 1, Source 2]" / "[1, 2]" / "[Sources 1 and 2]" as "[Source 1]…, Verify that every [Source N] citation in the answer refers to a source that…, verify_citations(), ChatContractTests

### Community 18 - "TS App Config"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 19 - "Settings & Document Processing"
Cohesion: 0.18
Nodes (14): Settings, main(), AppSetting, process_document(), Session, get_rag_config(), Session, save_rag_config() (+6 more)

### Community 20 - "Eval Metrics & Regression"
Cohesion: 0.13
Nodes (9): passage_in_text(), Whether a labelled evidence quote appears in a chunk (whitespace/case-…, compare_summaries(), _contains(), DatasetIntegrityTests, LlmCacheTests, Tests for the evaluation dataset, scoring metrics and summaries., Labels must stay valid against the committed corpus and real chunking. (+1 more)

### Community 21 - "Frontend Routing & Header"
Cohesion: 0.22
Nodes (13): login(), register(), AdminRoute(), Header(), HeaderProps, ProtectedRoute(), ProtectedRouteProps, useAuth() (+5 more)

### Community 22 - "Eval Corpus Loader"
Cohesion: 0.18
Nodes (17): asyncio, corpus_fingerprint(), CorpusScope, ensure_corpus(), _evaluation_collection(), _evaluation_user(), _ingest_file(), Path (+9 more)

### Community 23 - "Entailment Grounding Core"
Cohesion: 0.16
Nodes (17): _best_support(), _context_prefix(), _cosine(), _document_label(), entailment_scores(), _hypothesis(), _load_entailment_model(), Sentence-level grounding of generated answers. Every factual sentence in an… (+9 more)

### Community 24 - "Admin API Client"
Cohesion: 0.21
Nodes (14): AdminAnalytics, AdminSummary, AdminUser, AnalyticsPoint, DocumentStatus, EvaluationSummary, getAdminAnalytics(), getAdminSummary() (+6 more)

### Community 25 - "TS Node Config"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 26 - "User Account Routes"
Cohesion: 0.25
Nodes (13): change_password(), get_my_analytics(), patch, post, Session, update_me(), CurrentUserResponse, PasswordChange (+5 more)

### Community 27 - "Grounding Format Tests"
Cohesion: 0.16
Nodes (8): CitationFormatTests, fake_embeddings(), fake_entailment(), FinalizeAnswerTests, recording(), GroundingTestCase, Tests for sentence-level grounding (the entailment model is replaced by a stub)., unittest_mock

### Community 28 - "Frontend Auth Context"
Cohesion: 0.18
Nodes (9): AUTH_EXPIRED_EVENT, App(), AuthContext, AuthContextType, TOKEN_KEY, AuthProvider(), frontend_src_index, react (+1 more)

### Community 29 - "Chat Stream & Query Analytics"
Cohesion: 0.22
Nodes (12): chat(), chat_stream(), event_generator(), post, Session, Structured logging shared by the API and the Celery worker. Every record…, QueryEvent, get_admin_analytics() (+4 more)

### Community 30 - "Eval Dataset Format"
Cohesion: 0.21
Nodes (9): EvaluationCase, EvaluationDataset, load_dataset(), Passage, Path, Evaluation dataset format (version 2). A dataset is a JSON object:: {…, DatasetValidationTests, dataclasses (+1 more)

### Community 31 - "Admin Content Page"
Cohesion: 0.26
Nodes (13): AdminCollection, AdminDocument, deleteAdminCollection(), deleteAdminDocument(), getAdminCollections(), getAdminDocuments(), retryAdminDocument(), AdminContent() (+5 more)

### Community 32 - "Auth API Client"
Cohesion: 0.29
Nodes (12): changePassword(), CurrentUser, getCurrentUser(), LoginRequest, LoginResponse, RegisterRequest, updateUsername(), User (+4 more)

### Community 33 - "Chat Schemas & Hardening Tests"
Cohesion: 0.19
Nodes (9): _can_compare_regression(), Only compare completed case results; operational failures are not scores., ChatRequest, ChatResponse, ChatSource, BaseModel, fastapi, sqlalchemy_dialects (+1 more)

### Community 34 - "Answer Grounding Tests"
Cohesion: 0.24
Nodes (5): ground_answer(), Replace a sentence's citations with one citation, before final punctuation., Keep only answer sentences that a source entails; fix or drop the rest., _with_citation(), GroundAnswerTests

### Community 35 - "Codex Hardening Changelog"
Cohesion: 0.18
Nodes (13): Admin Analytics and Runtime RAG Settings, Authentication and Admin Access Controls, Document Ingestion and Processing Reliability, Document Intelligence and Object Storage, Evaluation Regression Workflow and Diagnostics, Frontend Lint CI Gate, Frontend Expired Session Recovery, Incomplete Evaluation Run Handling (+5 more)

### Community 36 - "Retrieval & Embedding Service"
Cohesion: 0.27
Nodes (10): DocumentChunk, generate_embedding(), embed_document_chunk(), Session, keyword_query(), Session, Page numbers a question refers to ("page 3", "p. 3", "pages 2-4", "pages 2 and…, OR-combine the question's words for websearch_to_tsquery. Stop words are… (+2 more)

### Community 37 - "Grounding Calibration"
Cohesion: 0.25
Nodes (10): argparse, is_model_refusal(), context_prefix(), corrupt(), document_label(), main(), claim_scores(), Calibrate sentence-level grounding on saved evaluation answers. Replays the… (+2 more)

### Community 38 - "Answer Sentence Segmentation"
Cohesion: 0.22
Nodes (6): _clean_claim(), evidence_units(), Sentences, adjacent sentence pairs, and table rows (with their header)., Split an answer into sentences with character spans into the original text., split_sentences(), SegmentationTests

### Community 39 - "Context Building"
Cohesion: 0.18
Nodes (10): build_context(), build_context_and_sources(), build_sources(), group_results_by_document(), prepare_results(), Remove duplicate/empty chunks while preserving relevance. This is shared by…, Group results by document and restore original chunk order., Build the final bounded LLM context and exact source metadata. Chunks are… (+2 more)

### Community 40 - "Evaluate Case Tests"
Cohesion: 0.38
Nodes (4): RagOutcome, Result of one pipeline run, before persistence or caching. status is one of:…, EvaluateCaseTests, _ranked()

### Community 41 - "Chunking & Chunk CRUD"
Cohesion: 0.36
Nodes (7): create_document_chunk(), create_document_chunks(), Session, chunk_text(), chunk_text_with_metadata(), ChunkData, tiktoken

### Community 42 - "RAG Pipeline Concepts"
Cohesion: 0.22
Nodes (10): Embedded phishing example (injection bait), Passwords and MFA rules (14-char minimum), Prompt-injection test cases, Unanswerable (should refuse) test cases, Confidence gate (refuse unrelated questions without LLM), CPU-only PyTorch backend image, Cross-encoder reranking (ms-marco-MiniLM-L-6-v2, best passage), Sentence-level grounding check (nli-deberta-v3-xsmall) (+2 more)

### Community 43 - "Evaluations Page"
Cohesion: 0.31
Nodes (9): EvaluationRun, EvaluationRunSummary, getEvaluationRun(), getEvaluationRuns(), Evaluations(), selectRun(), formatMetric(), METRICS (+1 more)

### Community 44 - "Admin Settings & Nav"
Cohesion: 0.29
Nodes (7): getRagSettings(), RagSettings, updateRagSettings(), AdminNav(), LINKS, AdminSettings(), save()

### Community 45 - "Embeddings & Redis Cache"
Cohesion: 0.47
Nodes (7): Any, cache_get(), cache_key(), cache_set(), generate_embeddings(), _load_model(), SentenceTransformer

### Community 46 - "LLM Fallback Changelog"
Cohesion: 0.25
Nodes (9): Empty Non-streaming Generation Validation, Empty Provider Response Handling, Empty-response Regression Tests, Empty Streaming Response Validation, Configured LLM Provider Fallback, LLM Provider Configuration and Docker Connectivity, Qwen3 Live Smoke Verification, RAG Retrieval, Context, Citation, and Grounding (+1 more)

### Community 48 - "Local Evaluation Script"
Cohesion: 0.38
Nodes (5): env_value(), EVAL_MEMORY, OLLAMA_MEMORY, run_evaluation.sh script, to_mb()

### Community 49 - "Auth Schemas"
Cohesion: 0.40
Nodes (4): LoginRequest, BaseModel, Token, pydantic

### Community 50 - "Lexical Support Check"
Cohesion: 0.40
Nodes (6): lexically_supported(), Crude suffix stripping so "storing"/"stores"/"stored" match "store"., Crude suffix stripping so "enables"/"enable"/"enabled" match. Numbers are…, Every number and nearly every content word of the claim appears in the source.…, _stem(), _tokens()

### Community 52 - "Auth Types"
Cohesion: 0.40
Nodes (4): LoginRequest, RegisterRequest, TokenResponse, User

### Community 54 - "Social Icons"
Cohesion: 1.00
Nodes (4): Bluesky Icon, Discord Icon, GitHub Icon, X Icon

### Community 55 - "Hero Illustration"
Cohesion: 0.67
Nodes (3): Hero illustration, Purple-accented lower layer, Stacked rounded layers visual motif

## Ambiguous Edges - Review These
- `Page-aware retrieval` → `Near-miss test cases (must-not-say values)`  [AMBIGUOUS]
  backend/evaluation/MANUAL_TEST_CASES.md · relation: conceptually_related_to

## Knowledge Gaps
- **130 isolated node(s):** `backend`, `name`, `private`, `version`, `type` (+125 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 389 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Page-aware retrieval` and `Near-miss test cases (must-not-say values)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `User` connect `Admin API Routes` to `Grounding Calibration`, `Conversation Routes`, `Migration Env & Base Models`, `Auth Dependencies & Chat Route`, `Auth Routes & JWT`, `Eval Corpus Loader`, `User Account Routes`, `Chat Stream & Query Analytics`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `Document` connect `Admin API Routes` to `Retrieval & Embedding Service`, `Grounding Calibration`, `RAG Answer Pipeline`, `Text Extraction & OCR`, `Migration Env & Base Models`, `Settings & Document Processing`, `Eval Corpus Loader`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `ground_answer()` connect `Answer Grounding Tests` to `Answer Sentence Segmentation`, `Reranking & Grounding Results`, `RAG Answer Pipeline`, `Embeddings & Redis Cache`, `Entailment Grounding Core`, `Grounding Format Tests`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Are the 41 inferred relationships involving `User` (e.g. with `get_current_user()` and `admin_analytics()`) actually correct?**
  _`User` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `Document` (e.g. with `admin_collections()` and `admin_delete_document()`) actually correct?**
  _`Document` has 25 INFERRED edges - model-reasoned connections that need verification._
- **What connects `backend`, `name`, `private` to the rest of the system?**
  _130 weakly-connected nodes found - possible documentation gaps or missing edges._