# Graph Report - enterprise-rag  (2026-11-11)

## Corpus Check
- 149 files · ~98,797 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 17 file(s) not represented in the graph (top: (none) 9, .css 2, .example 1)

## Summary
- 1107 nodes · 2509 edges · 88 communities (55 shown, 33 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 123 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `601677b4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- apiFetch
- User
- App.tsx
- test_hardening.py
- Chat.tsx
- runner.py
- package.json
- routes/auth.py
- grounding.py
- conversations.py
- stream_answer
- admin.ts
- text_extraction.py
- compilerOptions
- Layout
- compilerOptions
- collections_abc
- routes/chat.py
- typing
- Remaining Product Acceptance Work
- sqlalchemy
- Evaluation Metrics
- Empty Provider Response Handling
- Enterprise RAG Platform
- evaluator.py
- Phase 3 Evaluation Context
- test_grounding.py
- GitHub Actions CI and Benchmark Workflow
- ground_answer
- calibrate_grounding.py
- Northwind Analytics Employee Handbook
- types/auth.ts
- Bluesky Icon
- RagOutcome
- document_service.py
- rag.py
- split_sentences
- ResumeTests
- collections.py
- run_evaluation.sh
- Evaluations.tsx
- GroundingResult
- Stacked rounded layers visual motif
- tsconfig.json
- maintenance/__init__.py
- RAG Test Results
- Graphify Output Refresh and Integrity Verification
- Abstract Gradient Lightning Mark
- Backend Readiness Gate for Dependent Services
- Internal Persistent Redis with Cache-Only Eviction
- backup_postgres.sh
- restore_postgres.sh
- test_evaluation.py
- _patch_pipeline
- Backend Structure Inventory
- Backend Documentation
- Frontend Structure Inventory
- Enterprise RAG Application Metadata
- Documentation Icon
- Social Profile Icon
- Frontend Documentation
- React Logo
- Vite Logo
- Phase 3 Project Structure
- backend
- ChatContractTests
- llm.py
- dataset.py
- llm_cache.py
- build_context_and_sources
- run_rag_pipeline
- crud/document.py
- Manual RAG test cases
- compare_summaries
- schemas/user.py
- verify_citations
- LoginRequest
- schemas/chat.py
- _record_processing_failure
- LexicalSupportTests
- chat

## God Nodes (most connected - your core abstractions)
1. `User` - 48 edges
2. `Document` - 36 edges
3. `apiFetch()` - 34 edges
4. `Sidebar()` - 34 edges
5. `ChatContractTests` - 30 edges
6. `Base` - 23 edges
7. `ground_answer()` - 22 edges
8. `stream_answer()` - 22 edges
9. `Layout()` - 20 edges
10. `answer_question()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `get_current_user()` --uses--> `User`  [INFERRED]
  backend/app/api/dependencies.py → backend/app/models/user.py
- `admin_summary()` --uses--> `User`  [INFERRED]
  backend/app/api/routes/admin.py → backend/app/models/user.py
- `admin_users()` --uses--> `User`  [INFERRED]
  backend/app/api/routes/admin.py → backend/app/models/user.py
- `validate_user_status_change()` --uses--> `User`  [INFERRED]
  backend/app/api/routes/admin.py → backend/app/models/user.py
- `update_admin_user_status()` --uses--> `User`  [INFERRED]
  backend/app/api/routes/admin.py → backend/app/models/user.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **RAG Evaluation Workflow** — phase3_evaluation_dataset, phase3_evaluation_runner, phase3_evaluation_metrics [EXTRACTED 1.00]
- **Document Ingestion and Storage Lifecycle** — codex_changes_document_ingestion_and_processing, codex_changes_document_intelligence_and_object_storage, codex_changes_website_ingestion_response_limit [EXTRACTED 1.00]
- **Identity and Access Lifecycle** — codex_changes_authentication_and_admin_access, codex_changes_registration_conflict_handling, codex_changes_frontend_session_expiry_handling [EXTRACTED 1.00]
- **RAG Quality, Evaluation, and Provider Response Lifecycle** — codex_changes_rag_retrieval_context_citation_grounding, codex_changes_evaluation_regression_workflow, codex_changes_admin_analytics_and_runtime_settings, codex_changes_empty_provider_response_handling, codex_changes_empty_generation_validation, codex_changes_empty_stream_validation, codex_changes_llm_provider_fallback, codex_changes_empty_response_regression_tests, codex_changes_qwen3_live_smoke_verification [EXTRACTED 1.00]
- **Deployment, Readiness, and Data Recovery Operations** — deployment_local_compose_stack, deployment_readiness_checks, deployment_production_topology, deployment_backup_restore [EXTRACTED 1.00]
- **CI Quality Checks and Optional RAG Regression** — github_workflows_ci_backend_checks, github_workflows_ci_frontend_lint, github_workflows_ci_frontend_build, github_workflows_ci_manual_rag_benchmark, github_workflows_ci_benchmark_transcript_artifact [EXTRACTED 1.00]
- **Production Deployment Components** — infrastructure_docker_docker_compose_production_production_stack [EXTRACTED 1.00]
- **Social and community platform icons** — frontend_public_icons_bluesky_icon, frontend_public_icons_discord_icon, frontend_public_icons_github_icon, frontend_public_icons_x_icon [INFERRED 0.75]
- **Local Application Stack** — infrastructure_docker_docker_compose_local_compose_services, infrastructure_docker_docker_compose_backend_readiness_gate [INFERRED 0.95]

## Communities (88 total, 33 thin omitted)

### Community 0 - "apiFetch"
Cohesion: 0.12
Nodes (34): apiFetch(), Collection, createCollection(), deleteCollection(), getCollections(), renameCollection(), deleteConversation(), renameConversation() (+26 more)

### Community 1 - "User"
Cohesion: 0.20
Nodes (22): ingest_url(), list_documents(), delete, get, patch, post, Session, UploadFile (+14 more)

### Community 2 - "App.tsx"
Cohesion: 0.10
Nodes (27): CurrentUser, getCurrentUser(), login(), LoginRequest, LoginResponse, register(), RegisterRequest, User (+19 more)

### Community 3 - "test_hardening.py"
Cohesion: 0.11
Nodes (14): chunk_text(), chunk_text_with_metadata(), sanitize_filename(), validate_upload_filename(), _read_bounded_html(), validate_url(), IngestionBoundaryTests, bs4 (+6 more)

### Community 4 - "Chat.tsx"
Cohesion: 0.13
Nodes (22): ChatSource, ChatStreamEvent, streamChat(), StreamChatOptions, Conversation, ConversationDetail, createConversation(), getConversation() (+14 more)

### Community 5 - "runner.py"
Cohesion: 0.13
Nodes (20): argparse, evaluate_case(), EvaluationResult, Aggregate scores; each metric averages only the cases it applies to., Run one case through the same pipeline chat uses, without persistence., summarize_results(), _can_compare_regression(), _fmt() (+12 more)

### Community 6 - "package.json"
Cohesion: 0.05
Nodes (42): dependencies, react, react-dom, react-markdown, react-router-dom, remark-gfm, devDependencies, eslint (+34 more)

### Community 7 - "routes/auth.py"
Cohesion: 0.22
Nodes (14): login(), post, Session, register_user(), create_access_token(), hash_password(), verify_password(), create_user() (+6 more)

### Community 8 - "grounding.py"
Cohesion: 0.12
Nodes (23): _best_support(), _context_prefix(), _cosine(), _document_label(), entailment_scores(), _hypothesis(), lexically_supported(), _load_entailment_model() (+15 more)

### Community 9 - "conversations.py"
Cohesion: 0.18
Nodes (23): create_new_conversation(), get_conversation_detail(), list_user_conversations(), delete, get, patch, post, Session (+15 more)

### Community 10 - "stream_answer"
Cohesion: 0.20
Nodes (17): add_message(), reset_last_used_provider(), answer_question(), begin_rag_request(), build_conversation_context(), public_sources(), Session, _query_cache_key() (+9 more)

### Community 11 - "admin.ts"
Cohesion: 0.17
Nodes (17): AdminAnalytics, AdminSummary, AdminUser, AnalyticsPoint, EvaluationSummary, getAdminAnalytics(), getAdminSummary(), getAdminUsers() (+9 more)

### Community 12 - "text_extraction.py"
Cohesion: 0.08
Nodes (29): extract_docx(), extract_docx_images(), extract_pdf(), extract_pdf_page_blocks(), extract_pdf_pages(), extract_text(), is_usable_text(), ocr_page() (+21 more)

### Community 13 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 14 - "Layout"
Cohesion: 0.13
Nodes (8): getConversations(), Layout(), handleCollectionCreated(), handleSelectCollection(), loadCollections(), loadConversations(), loadDocuments(), readPersistedChatSelection()

### Community 15 - "compilerOptions"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 17 - "routes/chat.py"
Cohesion: 0.08
Nodes (31): get_current_admin(), get_current_user(), Session, get_me(), get_my_analytics(), get, Session, is_admin_email() (+23 more)

### Community 19 - "Remaining Product Acceptance Work"
Cohesion: 0.18
Nodes (13): Admin Analytics and Runtime RAG Settings, Authentication and Admin Access Controls, Document Ingestion and Processing Reliability, Document Intelligence and Object Storage, Evaluation Regression Workflow and Diagnostics, Frontend Lint CI Gate, Frontend Expired Session Recovery, Incomplete Evaluation Run Handling (+5 more)

### Community 20 - "sqlalchemy"
Cohesion: 0.07
Nodes (70): asyncio, Run migrations in 'offline' mode. This configures the context with just a URL…, Run migrations in 'online' mode. In this scenario we need to create an Engine…, run_migrations_offline(), run_migrations_online(), admin_analytics(), admin_summary(), admin_users() (+62 more)

### Community 21 - "Evaluation Metrics"
Cohesion: 0.24
Nodes (10): Fallback Accuracy, Keyword Recall, Retrieval Precision, Retrieval Recall, Token Answer F1, Phase 3.1 RAG Evaluation File Bundle, Evaluation Baseline Comparison, Evaluation Dataset (+2 more)

### Community 22 - "Empty Provider Response Handling"
Cohesion: 0.25
Nodes (9): Empty Non-streaming Generation Validation, Empty Provider Response Handling, Empty-response Regression Tests, Empty Streaming Response Validation, Configured LLM Provider Fallback, LLM Provider Configuration and Docker Connectivity, Qwen3 Live Smoke Verification, RAG Retrieval, Context, Citation, and Grounding (+1 more)

### Community 23 - "Enterprise RAG Platform"
Cohesion: 0.13
Nodes (15): PostgreSQL Backup and Isolated Restore Procedure, Local Docker Compose Stack, Manual CI RAG Benchmark Configuration, Single-Host Production Topology with Managed PostgreSQL and S3 Storage, Backend Readiness and Cold-Start Model Loading, Deployment and Operations Runbook, Production Environment and Secret Configuration, FastAPI, React, PostgreSQL pgvector, Redis and Celery Application Stack (+7 more)

### Community 24 - "evaluator.py"
Cohesion: 0.12
Nodes (22): Score evaluation cases against the production RAG pipeline., average(), chunk_relevance(), citation_scores(), contains_phrase(), forbidden_hits(), matched_facts(), normalize_text() (+14 more)

### Community 25 - "Phase 3 Evaluation Context"
Cohesion: 0.33
Nodes (7): Citation Verification, Conversation Persistence, Phase 3 Evaluation Context, Grounded RAG Generation, Reciprocal Rank Fusion, Reranking Stage, Semantic and Keyword Retrieval Pipeline

### Community 26 - "test_grounding.py"
Cohesion: 0.11
Nodes (13): CitationFormatTests, fake_embeddings(), fake_entailment(), FinalizeAnswerTests, recording(), GroundingTestCase, Tests for sentence-level grounding (the entailment model is replaced by a stub)., ConfidenceGateTests (+5 more)

### Community 27 - "GitHub Actions CI and Benchmark Workflow"
Cohesion: 0.33
Nodes (6): Backend Compilation and Focused Tests, Benchmark JSON Result and Text Transcript Artifacts, Frontend Production Build, Frontend ESLint Check, Manually Dispatched RAG Regression Benchmark, GitHub Actions CI and Benchmark Workflow

### Community 28 - "ground_answer"
Cohesion: 0.24
Nodes (5): ground_answer(), Replace a sentence's citations with one citation, before final punctuation., Keep only answer sentences that a source entails; fix or drop the rest., _with_citation(), GroundAnswerTests

### Community 29 - "calibrate_grounding.py"
Cohesion: 0.20
Nodes (16): Any, cache_get(), cache_key(), cache_set(), generate_embeddings(), _load_model(), is_model_refusal(), context_prefix() (+8 more)

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
Cohesion: 0.38
Nodes (4): RagOutcome, Result of one pipeline run, before persistence or caching. status is one of:…, EvaluateCaseTests, _ranked()

### Community 34 - "document_service.py"
Cohesion: 0.21
Nodes (11): check_storage_ready(), materialize_uploaded_file(), UploadFile, Yield a local path for parser libraries, downloading S3 objects to a temp file…, _s3_client(), save_uploaded_file(), boto3, botocore_config (+3 more)

### Community 35 - "rag.py"
Cohesion: 0.19
Nodes (12): extract_document_reference(), find_documents(), Session, passes_confidence_gate(), has_sufficient_confidence(), Determine whether the strongest retrieved chunk is relevant enough to support…, rerank_chunks(), score_chunks() (+4 more)

### Community 36 - "split_sentences"
Cohesion: 0.22
Nodes (6): _clean_claim(), evidence_units(), Sentences, adjacent sentence pairs, and table rows (with their header)., Split an answer into sentences with character spans into the original text., split_sentences(), SegmentationTests

### Community 38 - "collections.py"
Cohesion: 0.20
Nodes (20): create_new_collection(), list_user_collections(), delete, get, patch, post, Session, remove_collection() (+12 more)

### Community 39 - "run_evaluation.sh"
Cohesion: 0.38
Nodes (5): env_value(), EVAL_MEMORY, OLLAMA_MEMORY, run_evaluation.sh script, to_mb()

### Community 40 - "Evaluations.tsx"
Cohesion: 0.31
Nodes (9): EvaluationRun, EvaluationRunSummary, getEvaluationRun(), getEvaluationRuns(), Evaluations(), selectRun(), formatMetric(), METRICS (+1 more)

### Community 42 - "Stacked rounded layers visual motif"
Cohesion: 0.67
Nodes (3): Hero illustration, Purple-accented lower layer, Stacked rounded layers visual motif

### Community 57 - "test_evaluation.py"
Cohesion: 0.15
Nodes (6): _contains(), DatasetIntegrityTests, GeminiOptionsTests, LlmCacheTests, Tests for the evaluation dataset, scoring metrics and summaries., Labels must stay valid against the committed corpus and real chunking.

### Community 59 - "_patch_pipeline"
Cohesion: 0.28
Nodes (5): ChatEntryPointTests, _patch_pipeline(), PipelineTestCase, Patch retrieval, generation and grounding around the real orchestration., RunRagPipelineTests

### Community 72 - "ChatContractTests"
Cohesion: 0.14
Nodes (4): patch, update_admin_user_status(), validate_user_status_change(), ChatContractTests

### Community 73 - "llm.py"
Cohesion: 0.20
Nodes (15): generate_response(), _get_client(), get_last_used_provider(), _messages(), _provider_failure_hint(), Stream an LLM response token by token. The function yields only non-empty text…, Chat messages for one request. Qwen3 models "think" before answering by…, Provider-specific request parameters. Gemini 2.5 Flash/Flash-Lite think by… (+7 more)

### Community 74 - "dataset.py"
Cohesion: 0.23
Nodes (8): EvaluationCase, EvaluationDataset, load_dataset(), Passage, Path, Evaluation dataset format (version 2). A dataset is a JSON object:: {…, DatasetValidationTests, json

### Community 75 - "llm_cache.py"
Cohesion: 0.22
Nodes (6): LlmCache, Path, Local cache of LLM drafts for evaluation runs. Generation is the only step of…, hashlib, os, tempfile

### Community 76 - "build_context_and_sources"
Cohesion: 0.18
Nodes (10): build_context(), build_context_and_sources(), build_sources(), group_results_by_document(), prepare_results(), Remove duplicate/empty chunks while preserving relevance. This is shared by…, Group results by document and restore original chunk order., Build the final bounded LLM context and exact source metadata. Chunks are… (+2 more)

### Community 77 - "run_rag_pipeline"
Cohesion: 0.22
Nodes (11): build_rag_prompt(), finalize_answer(), prepare_generation(), Build the grounded RAG prompt used by both normal and streaming answers., Hybrid retrieval followed by cross-encoder reranking., Build the bounded context, its source metadata and the grounded prompt., Verify citations and sentence-level grounding. Returns (answer,…, Answer one question end to end without persistence or caching. generate… (+3 more)

### Community 78 - "crud/document.py"
Cohesion: 0.50
Nodes (7): delete_document(), get_document(), Session, update_document_collection(), update_document_filename(), Remove an uploaded file only when its resolved path is inside storage., remove_uploaded_file()

### Community 79 - "Manual RAG test cases"
Cohesion: 0.25
Nodes (7): Employee handbook, Employee handbook + IT security policy, IT security policy, Manual RAG test cases, Orion spec (PDF), Should refuse (not in any document), StuMeet report

### Community 81 - "schemas/user.py"
Cohesion: 0.57
Nodes (5): CurrentUserResponse, BaseModel, UserBase, UserLogin, UserResponse

### Community 82 - "verify_citations"
Cohesion: 0.29
Nodes (4): normalize_citation_groups(), Rewrite "[Source 1, Source 2]" / "[1, 2]" / "[Sources 1 and 2]" as "[Source 1]…, Verify that every [Source N] citation in the answer refers to a source that…, verify_citations()

### Community 83 - "LoginRequest"
Cohesion: 0.40
Nodes (4): LoginRequest, BaseModel, Token, pydantic

### Community 84 - "schemas/chat.py"
Cohesion: 0.47
Nodes (4): ChatRequest, ChatResponse, ChatSource, BaseModel

### Community 85 - "_record_processing_failure"
Cohesion: 0.40
Nodes (3): Update job/document state and return retries left after this attempt., _record_processing_failure(), Exception

### Community 87 - "chat"
Cohesion: 0.67
Nodes (4): chat(), chat_stream(), post, Session

## Knowledge Gaps
- **159 isolated node(s):** `backend`, `name`, `private`, `version`, `type` (+154 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 392 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **33 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `collections.py`, `routes/auth.py`, `ChatContractTests`, `conversations.py`, `routes/chat.py`, `sqlalchemy`, `chat`, `calibrate_grounding.py`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `Document` connect `sqlalchemy` to `User`, `rag.py`, `stream_answer`, `text_extraction.py`, `crud/document.py`, `calibrate_grounding.py`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Why does `ground_answer()` connect `ground_answer` to `rag.py`, `split_sentences`, `grounding.py`, `GroundingResult`, `run_rag_pipeline`, `test_grounding.py`, `calibrate_grounding.py`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Are the 33 inferred relationships involving `User` (e.g. with `get_current_user()` and `admin_analytics()`) actually correct?**
  _`User` has 33 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `Document` (e.g. with `admin_summary()` and `list_documents()`) actually correct?**
  _`Document` has 20 INFERRED edges - model-reasoned connections that need verification._
- **What connects `backend`, `name`, `private` to the rest of the system?**
  _159 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `apiFetch` be split into smaller, more focused modules?**
  _Cohesion score 0.11962833914053426 - nodes in this community are weakly interconnected._