# Graph Report - enterprise-rag  (2026-11-14)

## Corpus Check
- 154 files · ~74,771 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: (none) 8, .css 2, .example 1)

## Summary
- 1187 nodes · 2773 edges · 84 communities (56 shown, 28 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 151 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `aaa5b0bc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- apiFetch
- documents.py
- react
- IngestionBoundaryTests
- logging.py
- runner.py
- package.json
- test_hardening.py
- grounding.py
- conversations.py
- stream_answer
- admin.ts
- text_extraction.py
- compilerOptions
- Document
- compilerOptions
- collections_abc
- main.py
- typing
- Remaining Product Acceptance Work
- sqlalchemy
- DocumentChunk
- Empty Provider Response Handling
- Enterprise RAG Platform
- test_evaluation.py
- corpus.py
- test_grounding.py
- GitHub Actions CI and Benchmark Workflow
- ground_answer
- config.py
- Northwind Analytics Employee Handbook
- types/auth.ts
- Bluesky Icon
- RagOutcome
- document_service.py
- rag.py
- split_sentences
- _load_resumable
- User
- run_evaluation.sh
- Evaluations.tsx
- App.tsx
- Stacked rounded layers visual motif
- tsconfig.json
- maintenance/__init__.py
- api/auth.ts
- Graphify Output Refresh and Integrity Verification
- Abstract Gradient Lightning Mark
- Backend Readiness Gate for Dependent Services
- Internal Persistent Redis with Cache-Only Eviction
- backup_postgres.sh
- restore_postgres.sh
- pathlib
- AdminContent.tsx
- test_rag_pipeline.py
- AdminSettings.tsx
- reranking.py
- Frontend Structure Inventory
- Enterprise RAG Application Metadata
- Documentation Icon
- Social Profile Icon
- Frontend Documentation
- React Logo
- Vite Logo
- 9f6316708db3_add_embeddings_to_document_chunks.py
- backend
- lexically_supported
- llm.py
- evaluator.py
- web_extraction.py
- build_context_and_sources
- evidence_units
- crud/document.py
- Manual RAG test cases
- compare_summaries
- Register.tsx
- verify_citations
- LexicalSupportTests

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
- `get_current_user()` --uses--> `User`  [INFERRED]
  backend/app/api/dependencies.py → backend/app/models/user.py
- `admin_summary()` --uses--> `Document`  [INFERRED]
  backend/app/api/routes/admin.py → backend/app/models/document.py
- `admin_summary()` --uses--> `ProcessingJob`  [INFERRED]
  backend/app/api/routes/admin.py → backend/app/models/processing_job.py
- `_document_payload()` --uses--> `Document`  [INFERRED]
  backend/app/api/routes/admin.py → backend/app/models/document.py
- `admin_documents()` --uses--> `DocumentChunk`  [INFERRED]
  backend/app/api/routes/admin.py → backend/app/models/document_chunk.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Document Ingestion and Storage Lifecycle** — codex_changes_document_ingestion_and_processing, codex_changes_document_intelligence_and_object_storage, codex_changes_website_ingestion_response_limit [EXTRACTED 1.00]
- **Identity and Access Lifecycle** — codex_changes_authentication_and_admin_access, codex_changes_registration_conflict_handling, codex_changes_frontend_session_expiry_handling [EXTRACTED 1.00]
- **RAG Quality, Evaluation, and Provider Response Lifecycle** — codex_changes_rag_retrieval_context_citation_grounding, codex_changes_evaluation_regression_workflow, codex_changes_admin_analytics_and_runtime_settings, codex_changes_empty_provider_response_handling, codex_changes_empty_generation_validation, codex_changes_empty_stream_validation, codex_changes_llm_provider_fallback, codex_changes_empty_response_regression_tests, codex_changes_qwen3_live_smoke_verification [EXTRACTED 1.00]
- **Deployment, Readiness, and Data Recovery Operations** — deployment_local_compose_stack, deployment_readiness_checks, deployment_production_topology, deployment_backup_restore [EXTRACTED 1.00]
- **CI Quality Checks and Optional RAG Regression** — github_workflows_ci_backend_checks, github_workflows_ci_frontend_lint, github_workflows_ci_frontend_build, github_workflows_ci_manual_rag_benchmark, github_workflows_ci_benchmark_transcript_artifact [EXTRACTED 1.00]
- **Production Deployment Components** — infrastructure_docker_docker_compose_production_production_stack [EXTRACTED 1.00]
- **Social and community platform icons** — frontend_public_icons_bluesky_icon, frontend_public_icons_discord_icon, frontend_public_icons_github_icon, frontend_public_icons_x_icon [INFERRED 0.75]
- **Local Application Stack** — infrastructure_docker_docker_compose_local_compose_services, infrastructure_docker_docker_compose_backend_readiness_gate [INFERRED 0.95]

## Communities (84 total, 28 thin omitted)

### Community 0 - "apiFetch"
Cohesion: 0.05
Nodes (66): ChatSource, ChatStreamEvent, streamChat(), StreamChatOptions, apiFetch(), Collection, createCollection(), deleteCollection() (+58 more)

### Community 1 - "documents.py"
Cohesion: 0.19
Nodes (20): ingest_url(), list_documents(), delete, get, patch, post, Session, UploadFile (+12 more)

### Community 2 - "react"
Cohesion: 0.20
Nodes (8): AUTH_EXPIRED_EVENT, App(), AuthContext, AuthContextType, TOKEN_KEY, AuthProvider(), frontend_src_index, react

### Community 3 - "IngestionBoundaryTests"
Cohesion: 0.11
Nodes (9): chunk_text(), chunk_text_with_metadata(), _read_bounded_html(), validate_url(), Update job/document state and return retries left after this attempt., _record_processing_failure(), IngestionBoundaryTests, Exception (+1 more)

### Community 4 - "logging.py"
Cohesion: 0.12
Nodes (18): configure_logging(), JsonFormatter, Structured logging shared by the API and the Celery worker. Every record…, RequestIdFilter, _bind_task_id(), _configure_worker_logging(), _unbind_task_id(), JsonLoggingTests (+10 more)

### Community 5 - "runner.py"
Cohesion: 0.13
Nodes (16): LlmCache, Path, Local cache of LLM drafts for evaluation runs. Generation is the only step of…, _can_compare_regression(), _fmt(), main(), _print_case(), _print_summary() (+8 more)

### Community 6 - "package.json"
Cohesion: 0.05
Nodes (45): dependencies, react, react-dom, react-markdown, react-router-dom, remark-gfm, devDependencies, eslint (+37 more)

### Community 7 - "test_hardening.py"
Cohesion: 0.05
Nodes (52): get_current_user(), Session, login(), post, Session, register_user(), change_password(), get_me() (+44 more)

### Community 8 - "grounding.py"
Cohesion: 0.16
Nodes (17): _best_support(), _context_prefix(), _cosine(), _document_label(), entailment_scores(), _hypothesis(), _load_entailment_model(), Sentence-level grounding of generated answers. Every factual sentence in an… (+9 more)

### Community 9 - "conversations.py"
Cohesion: 0.19
Nodes (24): create_new_conversation(), get_conversation_detail(), list_user_conversations(), delete, get, patch, post, Session (+16 more)

### Community 10 - "stream_answer"
Cohesion: 0.16
Nodes (20): build_conversation_context(), build_rag_prompt(), finalize_answer(), passes_confidence_gate(), prepare_generation(), Session, _query_cache_key(), Load recent conversation messages and format them for inclusion in the LLM… (+12 more)

### Community 11 - "admin.ts"
Cohesion: 0.18
Nodes (16): AdminAnalytics, AdminCollection, AdminDocument, AdminSummary, AdminUser, AnalyticsPoint, DocumentStatus, EvaluationSummary (+8 more)

### Community 12 - "text_extraction.py"
Cohesion: 0.13
Nodes (23): extract_docx(), extract_docx_images(), extract_pdf(), extract_pdf_page_blocks(), extract_pdf_pages(), extract_text(), is_usable_text(), ocr_page() (+15 more)

### Community 13 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 14 - "Document"
Cohesion: 0.17
Nodes (17): argparse, main(), Document, ProcessingJob, process_document(), Session, extract_text_blocks(), extract_webpage_text() (+9 more)

### Community 15 - "compilerOptions"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 17 - "main.py"
Cohesion: 0.18
Nodes (12): health(), get, readiness(), request_logging_middleware(), root(), fastapi_middleware_cors, fastapi_responses, middleware (+4 more)

### Community 19 - "Remaining Product Acceptance Work"
Cohesion: 0.18
Nodes (13): Admin Analytics and Runtime RAG Settings, Authentication and Admin Access Controls, Document Ingestion and Processing Reliability, Document Intelligence and Object Storage, Evaluation Regression Workflow and Diagnostics, Frontend Lint CI Gate, Frontend Expired Session Recovery, Incomplete Evaluation Run Handling (+5 more)

### Community 20 - "sqlalchemy"
Cohesion: 0.23
Nodes (13): Run migrations in 'offline' mode. This configures the context with just a URL…, Run migrations in 'online' mode. In this scenario we need to create an Engine…, run_migrations_offline(), run_migrations_online(), Base, AppSetting, Message, copy (+5 more)

### Community 21 - "DocumentChunk"
Cohesion: 0.19
Nodes (15): create_document_chunk(), create_document_chunks(), Session, DocumentChunk, ChunkData, generate_embedding(), embed_document_chunk(), Session (+7 more)

### Community 22 - "Empty Provider Response Handling"
Cohesion: 0.25
Nodes (9): Empty Non-streaming Generation Validation, Empty Provider Response Handling, Empty-response Regression Tests, Empty Streaming Response Validation, Configured LLM Provider Fallback, LLM Provider Configuration and Docker Connectivity, Qwen3 Live Smoke Verification, RAG Retrieval, Context, Citation, and Grounding (+1 more)

### Community 23 - "Enterprise RAG Platform"
Cohesion: 0.13
Nodes (15): PostgreSQL Backup and Isolated Restore Procedure, Local Docker Compose Stack, Manual CI RAG Benchmark Configuration, Single-Host Production Topology with Managed PostgreSQL and S3 Storage, Backend Readiness and Cold-Start Model Loading, Deployment and Operations Runbook, Production Environment and Secret Configuration, FastAPI, React, PostgreSQL pgvector, Redis and Celery Application Stack (+7 more)

### Community 24 - "test_evaluation.py"
Cohesion: 0.09
Nodes (24): chunk_relevance(), citation_scores(), contains_phrase(), forbidden_hits(), matched_facts(), normalize_text(), passage_in_text(), Deterministic scoring functions for RAG evaluation. (+16 more)

### Community 25 - "corpus.py"
Cohesion: 0.23
Nodes (14): asyncio, corpus_fingerprint(), CorpusScope, ensure_corpus(), _evaluation_collection(), _evaluation_user(), _ingest_file(), Path (+6 more)

### Community 26 - "test_grounding.py"
Cohesion: 0.19
Nodes (7): CitationFormatTests, fake_embeddings(), fake_entailment(), FinalizeAnswerTests, recording(), GroundingTestCase, Tests for sentence-level grounding (the entailment model is replaced by a stub).

### Community 27 - "GitHub Actions CI and Benchmark Workflow"
Cohesion: 0.33
Nodes (6): Backend Compilation and Focused Tests, Benchmark JSON Result and Text Transcript Artifacts, Frontend Production Build, Frontend ESLint Check, Manually Dispatched RAG Regression Benchmark, GitHub Actions CI and Benchmark Workflow

### Community 28 - "ground_answer"
Cohesion: 0.24
Nodes (5): ground_answer(), Replace a sentence's citations with one citation, before final punctuation., Keep only answer sentences that a source entails; fix or drop the rest., _with_citation(), GroundAnswerTests

### Community 29 - "config.py"
Cohesion: 0.28
Nodes (10): Any, Settings, cache_get(), cache_key(), cache_set(), generate_embeddings(), _load_model(), BaseSettings (+2 more)

### Community 30 - "Northwind Analytics Employee Handbook"
Cohesion: 0.17
Nodes (11): Annual Leave, Equipment, Expenses, Leave, Northwind Analytics Employee Handbook, Parental Leave, Probation and Notice, Remote Work (+3 more)

### Community 31 - "types/auth.ts"
Cohesion: 0.40
Nodes (4): LoginRequest, RegisterRequest, TokenResponse, User

### Community 32 - "Bluesky Icon"
Cohesion: 1.00
Nodes (4): Bluesky Icon, Discord Icon, GitHub Icon, X Icon

### Community 33 - "RagOutcome"
Cohesion: 0.22
Nodes (7): EvaluationCase, Passage, RagOutcome, Result of one pipeline run, before persistence or caching. status is one of:…, DatasetValidationTests, EvaluateCaseTests, _ranked()

### Community 34 - "document_service.py"
Cohesion: 0.22
Nodes (12): check_storage_ready(), materialize_uploaded_file(), UploadFile, Yield a local path for parser libraries, downloading S3 objects to a temp file…, _s3_client(), sanitize_filename(), save_uploaded_file(), validate_upload_filename() (+4 more)

### Community 35 - "rag.py"
Cohesion: 0.24
Nodes (13): add_message(), extract_document_reference(), find_documents(), Session, get_last_used_provider(), reset_last_used_provider(), answer_question(), begin_rag_request() (+5 more)

### Community 36 - "split_sentences"
Cohesion: 0.38
Nodes (4): _clean_claim(), Split an answer into sentences with character spans into the original text., split_sentences(), SegmentationTests

### Community 37 - "_load_resumable"
Cohesion: 0.53
Nodes (3): _load_resumable(), Completed results from an earlier run with identical settings, if any., ResumeTests

### Community 38 - "User"
Cohesion: 0.06
Nodes (64): get_current_admin(), admin_analytics(), admin_collections(), admin_delete_collection(), admin_delete_document(), admin_documents(), admin_retry_document(), admin_summary() (+56 more)

### Community 39 - "run_evaluation.sh"
Cohesion: 0.38
Nodes (5): env_value(), EVAL_MEMORY, OLLAMA_MEMORY, run_evaluation.sh script, to_mb()

### Community 40 - "Evaluations.tsx"
Cohesion: 0.31
Nodes (9): EvaluationRun, EvaluationRunSummary, getEvaluationRun(), getEvaluationRuns(), Evaluations(), selectRun(), formatMetric(), METRICS (+1 more)

### Community 41 - "App.tsx"
Cohesion: 0.28
Nodes (10): login(), AdminRoute(), Header(), HeaderProps, ProtectedRoute(), ProtectedRouteProps, useAuth(), Login() (+2 more)

### Community 42 - "Stacked rounded layers visual motif"
Cohesion: 0.67
Nodes (3): Hero illustration, Purple-accented lower layer, Stacked rounded layers visual motif

### Community 45 - "api/auth.ts"
Cohesion: 0.29
Nodes (12): changePassword(), CurrentUser, getCurrentUser(), LoginRequest, LoginResponse, RegisterRequest, updateUsername(), User (+4 more)

### Community 53 - "pathlib"
Cohesion: 0.18
Nodes (6): build(), Document, Generate the Orion product specification PDF used by the evaluation corpus. The…, Writer, fitz, pathlib

### Community 57 - "AdminContent.tsx"
Cohesion: 0.33
Nodes (11): deleteAdminCollection(), deleteAdminDocument(), getAdminCollections(), getAdminDocuments(), retryAdminDocument(), AdminContent(), removeCollection(), removeDocument() (+3 more)

### Community 59 - "test_rag_pipeline.py"
Cohesion: 0.10
Nodes (12): GroundingResult, ChatEntryPointTests, ConfidenceGateTests, LlmMessageTests, PageReferenceTests, PassageRerankTests, _patch_pipeline(), PipelineTestCase (+4 more)

### Community 61 - "AdminSettings.tsx"
Cohesion: 0.29
Nodes (7): getRagSettings(), RagSettings, updateRagSettings(), AdminNav(), LINKS, AdminSettings(), save()

### Community 62 - "reranking.py"
Cohesion: 0.25
Nodes (7): has_sufficient_confidence(), passage_windows(), Overlapping windows of a few sentences/lines from a chunk., Rank chunks by their best-matching passage. A 400-token chunk often mixes…, Determine whether the strongest retrieved chunk is relevant enough to support…, rerank_chunks(), sentence_transformers

### Community 72 - "lexically_supported"
Cohesion: 0.40
Nodes (6): lexically_supported(), Crude suffix stripping so "storing"/"stores"/"stored" match "store"., Crude suffix stripping so "enables"/"enable"/"enabled" match. Numbers are…, Every number and nearly every content word of the claim appears in the source.…, _stem(), _tokens()

### Community 73 - "llm.py"
Cohesion: 0.20
Nodes (14): generate_response(), _get_client(), _messages(), _provider_failure_hint(), Stream an LLM response token by token. The function yields only non-empty text…, Chat messages for one request. Qwen3 models "think" before answering by…, Provider-specific request parameters. Gemini 2.5 Flash/Flash-Lite think by…, Return the configured LLM client and model. Supported providers: - gemini -… (+6 more)

### Community 74 - "evaluator.py"
Cohesion: 0.13
Nodes (20): EvaluationDataset, load_dataset(), Path, Evaluation dataset format (version 2). A dataset is a JSON object:: {…, evaluate_case(), EvaluationResult, _median_words(), Score evaluation cases against the production RAG pipeline. (+12 more)

### Community 75 - "web_extraction.py"
Cohesion: 0.33
Nodes (5): bs4, httpx, ipaddress, socket, urllib_parse

### Community 76 - "build_context_and_sources"
Cohesion: 0.18
Nodes (10): build_context(), build_context_and_sources(), build_sources(), group_results_by_document(), prepare_results(), Remove duplicate/empty chunks while preserving relevance. This is shared by…, Group results by document and restore original chunk order., Build the final bounded LLM context and exact source metadata. Chunks are… (+2 more)

### Community 78 - "crud/document.py"
Cohesion: 0.44
Nodes (8): create_document(), delete_document(), get_document(), Session, update_document_collection(), update_document_filename(), Remove an uploaded file only when its resolved path is inside storage., remove_uploaded_file()

### Community 79 - "Manual RAG test cases"
Cohesion: 0.25
Nodes (7): Employee handbook, Employee handbook + IT security policy, IT security policy, Manual RAG test cases, Orion spec (PDF), Should refuse (not in any document), StuMeet report

### Community 81 - "Register.tsx"
Cohesion: 0.83
Nodes (3): register(), Register(), handleSubmit()

### Community 82 - "verify_citations"
Cohesion: 0.29
Nodes (4): normalize_citation_groups(), Rewrite "[Source 1, Source 2]" / "[1, 2]" / "[Sources 1 and 2]" as "[Source 1]…, Verify that every [Source N] citation in the answer refers to a source that…, verify_citations()

## Knowledge Gaps
- **151 isolated node(s):** `backend`, `name`, `private`, `version`, `type` (+146 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 409 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `documents.py`, `test_hardening.py`, `conversations.py`, `evaluator.py`, `Document`, `sqlalchemy`, `corpus.py`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `Document` connect `Document` to `documents.py`, `rag.py`, `User`, `stream_answer`, `evaluator.py`, `text_extraction.py`, `crud/document.py`, `sqlalchemy`, `DocumentChunk`, `corpus.py`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `ground_answer()` connect `ground_answer` to `rag.py`, `split_sentences`, `grounding.py`, `stream_answer`, `evidence_units`, `test_grounding.py`, `test_rag_pipeline.py`, `config.py`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Are the 41 inferred relationships involving `User` (e.g. with `get_current_user()` and `admin_analytics()`) actually correct?**
  _`User` has 41 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `Document` (e.g. with `admin_collections()` and `admin_delete_document()`) actually correct?**
  _`Document` has 25 INFERRED edges - model-reasoned connections that need verification._
- **What connects `backend`, `name`, `private` to the rest of the system?**
  _151 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `apiFetch` be split into smaller, more focused modules?**
  _Cohesion score 0.053235653235653234 - nodes in this community are weakly interconnected._