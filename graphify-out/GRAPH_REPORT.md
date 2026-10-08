# Graph Report - enterprise-rag  (2026-10-08)

## Corpus Check
- 144 files · ~62,720 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 20 file(s) not represented in the graph (top: (none) 8, .log 6, .css 2)

## Summary
- 740 nodes · 1598 edges · 60 communities (33 shown, 27 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 87 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

- Note: semantic extraction ran through the host agent; token usage was not exposed by that tool and is not included in the zero token counters above.

## Community Hubs (Navigation)
- Frontend API and Layout
- Document Chunk Persistence
- Database Schema Migrations
- Frontend Build Tooling
- Admin API Client
- Document API Routes
- Document Search and CRUD
- Conversation API Routes
- User Authentication API
- PDF and Office Extraction
- Collection API Routes
- Database Models and Session
- RAG Evaluation Runner
- Chat API and Health
- Frontend App Configuration
- Authentication and Chat Routes
- Citation Grounding Verification
- TypeScript Build Configuration
- Processing Schema Migrations
- Authorization and App Configuration
- Evaluation Dataset Models
- Platform Overview Documentation
- RAG Context and Sources
- Evaluation Metrics
- Admin API Routes
- RAG Roadmap Concepts
- Docker Compose Services
- Alembic Migration Runtime
- Project Change Documentation
- Citation Verification Helpers
- Authentication Request Types
- Social Platform Icons
- Continuous Integration Workflow
- Deployment Runbook
- Hero Illustration Concepts
- TypeScript Project References
- RAG Test Results
- Platform Brand Mark
- Database Backup Script
- Database Restore Script
- Backend Structure Inventory
- Backend Documentation
- Frontend Structure Inventory
- Frontend HTML Entry
- Documentation Icon
- Social Profile Icon
- Frontend Documentation
- React Logo
- Vite Logo
- Phase Three Structure Notes
- Backend Python Project

## God Nodes (most connected - your core abstractions)
1. `User` - 36 edges
2. `Sidebar()` - 34 edges
3. `Document` - 27 edges
4. `apiFetch()` - 27 edges
5. `evaluate_case()` - 24 edges
6. `answer_question()` - 22 edges
7. `stream_answer()` - 20 edges
8. `Layout()` - 20 edges
9. `Base` - 19 edges
10. `compilerOptions` - 18 edges

## Surprising Connections (you probably didn't know these)
- `admin_summary()` --uses--> `Document`  [INFERRED]
  backend/app/api/routes/admin.py → backend/app/models/document.py
- `admin_summary()` --uses--> `ProcessingJob`  [INFERRED]
  backend/app/api/routes/admin.py → backend/app/models/processing_job.py
- `admin_summary()` --uses--> `QueryEvent`  [INFERRED]
  backend/app/api/routes/admin.py → backend/app/models/query_event.py
- `admin_summary()` --uses--> `User`  [INFERRED]
  backend/app/api/routes/admin.py → backend/app/models/user.py
- `admin_users()` --uses--> `User`  [INFERRED]
  backend/app/api/routes/admin.py → backend/app/models/user.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **RAG Evaluation Workflow** — phase3_evaluation_dataset, phase3_evaluation_runner, phase3_evaluation_metrics [EXTRACTED 1.00]
- **Social and community platform icons** — frontend_public_icons_bluesky_icon, frontend_public_icons_discord_icon, frontend_public_icons_github_icon, frontend_public_icons_x_icon [INFERRED 0.75]

## Communities (60 total, 27 thin omitted)

### Community 0 - "Frontend API and Layout"
Cohesion: 0.05
Nodes (64): ChatSource, ChatStreamEvent, streamChat(), StreamChatOptions, apiFetch(), Collection, createCollection(), deleteCollection() (+56 more)

### Community 1 - "Document Chunk Persistence"
Cohesion: 0.08
Nodes (33): create_document_chunk(), create_document_chunks(), Session, DocumentChunk, chunk_text(), chunk_text_with_metadata(), ChunkData, process_document() (+25 more)

### Community 3 - "Frontend Build Tooling"
Cohesion: 0.05
Nodes (42): dependencies, react, react-dom, react-markdown, react-router-dom, remark-gfm, devDependencies, eslint (+34 more)

### Community 4 - "Admin API Client"
Cohesion: 0.09
Nodes (28): AdminSummary, AdminUser, getAdminSummary(), getAdminUsers(), login(), LoginRequest, LoginResponse, register() (+20 more)

### Community 5 - "Document API Routes"
Cohesion: 0.14
Nodes (32): ingest_url(), list_documents(), delete, get, patch, post, Session, UploadFile (+24 more)

### Community 6 - "Document Search and CRUD"
Cohesion: 0.14
Nodes (27): add_message(), extract_document_reference(), find_documents(), Session, generate_response(), _get_client(), Return the configured LLM client and model. Supported providers: - gemini -…, Stream an LLM response token by token. The function yields only non-empty text… (+19 more)

### Community 7 - "Conversation API Routes"
Cohesion: 0.19
Nodes (24): create_new_conversation(), get_conversation_detail(), list_user_conversations(), delete, get, patch, post, Session (+16 more)

### Community 8 - "User Authentication API"
Cohesion: 0.18
Nodes (20): login(), post, Session, register_user(), create_access_token(), hash_password(), verify_password(), create_user() (+12 more)

### Community 9 - "PDF and Office Extraction"
Cohesion: 0.12
Nodes (23): extract_docx(), extract_docx_images(), extract_pdf(), extract_pdf_pages(), extract_text(), is_usable_text(), ocr_page(), ocr_pdf() (+15 more)

### Community 10 - "Collection API Routes"
Cohesion: 0.20
Nodes (20): create_new_collection(), list_user_collections(), delete, get, patch, post, Session, remove_collection() (+12 more)

### Community 11 - "Database Models and Session"
Cohesion: 0.32
Nodes (9): Base, Message, ProcessingJob, process_document_task(), datetime, DeclarativeBase, sqlalchemy, sqlalchemy_orm (+1 more)

### Community 12 - "RAG Evaluation Runner"
Cohesion: 0.20
Nodes (18): evaluate_case(), EvaluationResult, _extract_citation_ids(), _is_fallback(), Evaluate one RAG case without creating a conversation. Retrieval and reranking…, summarize_results(), average(), citation_precision() (+10 more)

### Community 13 - "Chat API and Health"
Cohesion: 0.15
Nodes (17): health(), get, readiness(), request_logging_middleware(), root(), ChatRequest, ChatResponse, ChatSource (+9 more)

### Community 14 - "Frontend App Configuration"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 15 - "Authentication and Chat Routes"
Cohesion: 0.18
Nodes (17): get_current_user(), Session, chat(), chat_stream(), event_generator(), post, Session, get_me() (+9 more)

### Community 16 - "Citation Grounding Verification"
Cohesion: 0.19
Nodes (10): _cosine_similarity(), Verify that cited factual claims are semantically supported by their cited…, Attach citations to uncited claims when retrieved sources support them., _remove_citations(), repair_missing_citations(), _split_claims(), verify_answer_grounding(), generate_embeddings() (+2 more)

### Community 17 - "TypeScript Build Configuration"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 19 - "Authorization and App Configuration"
Cohesion: 0.19
Nodes (9): get_current_admin(), is_admin_email(), Settings, decode_access_token(), BaseSettings, celery, fastapi_security, jose (+1 more)

### Community 20 - "Evaluation Dataset Models"
Cohesion: 0.24
Nodes (8): argparse, EvaluationCase, load_dataset(), Path, compare_summaries(), main(), json, pathlib

### Community 21 - "Platform Overview Documentation"
Cohesion: 0.15
Nodes (13): Asynchronous Document Ingestion, Enterprise RAG Platform, FastAPI Backend, Gemini Generation, Hybrid Retrieval, Ollama Generation, PDF OCR Fallback, PostgreSQL and pgvector (+5 more)

### Community 22 - "RAG Context and Sources"
Cohesion: 0.18
Nodes (10): build_context(), build_context_and_sources(), build_sources(), group_results_by_document(), prepare_results(), Remove duplicate/empty chunks while preserving relevance. This is shared by…, Group results by document and restore original chunk order., Build the final bounded LLM context and exact source metadata. Chunks are… (+2 more)

### Community 23 - "Evaluation Metrics"
Cohesion: 0.24
Nodes (10): Fallback Accuracy, Keyword Recall, Retrieval Precision, Retrieval Recall, Token Answer F1, Phase 3.1 RAG Evaluation File Bundle, Evaluation Baseline Comparison, Evaluation Dataset (+2 more)

### Community 24 - "Admin API Routes"
Cohesion: 0.36
Nodes (6): admin_summary(), admin_users(), get, Session, get_db(), Session

### Community 25 - "RAG Roadmap Concepts"
Cohesion: 0.33
Nodes (7): Citation Verification, Conversation Persistence, Phase 3 Evaluation Context, Grounded RAG Generation, Reciprocal Rank Fusion, Reranking Stage, Semantic and Keyword Retrieval Pipeline

### Community 26 - "Docker Compose Services"
Cohesion: 0.33
Nodes (7): Backend Service, Frontend Service, PostgreSQL Service, Redis Service, Uploaded Files Volume, Worker Service, Docker Compose Stack

### Community 27 - "Alembic Migration Runtime"
Cohesion: 0.33
Nodes (5): Run migrations in 'offline' mode. This configures the context with just a URL…, Run migrations in 'online' mode. In this scenario we need to create an Engine…, run_migrations_offline(), run_migrations_online(), logging_config

### Community 28 - "Project Change Documentation"
Cohesion: 0.33
Nodes (6): Codex Changes Record, Citation and Grounding Verification, Configurable LLM Provider, Shared Uploaded Files Volume, Persisted Citation Sources, Validated Streaming Responses

### Community 29 - "Citation Verification Helpers"
Cohesion: 0.40
Nodes (4): extract_citation_ids(), Extract all [Source N] citation IDs from an answer., Verify that every [Source N] citation in the answer refers to a source that…, verify_citations()

### Community 30 - "Authentication Request Types"
Cohesion: 0.40
Nodes (4): LoginRequest, RegisterRequest, TokenResponse, User

### Community 31 - "Social Platform Icons"
Cohesion: 1.00
Nodes (4): Bluesky Icon, Discord Icon, GitHub Icon, X Icon

### Community 32 - "Continuous Integration Workflow"
Cohesion: 0.67
Nodes (3): Continuous Integration Workflow, Backend Compile and Focused Tests, Frontend Production Build

### Community 33 - "Deployment Runbook"
Cohesion: 0.67
Nodes (3): Alembic Startup Migrations, Celery Document Processing Worker, Deployment Runbook

### Community 34 - "Hero Illustration Concepts"
Cohesion: 0.67
Nodes (3): Hero illustration, Purple-accented lower layer, Stacked rounded layers visual motif

## Knowledge Gaps
- **126 isolated node(s):** `backend`, `name`, `private`, `version`, `type` (+121 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 280 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `Authentication and Chat Routes` to `Document API Routes`, `Conversation API Routes`, `User Authentication API`, `Collection API Routes`, `Database Models and Session`, `Chat API and Health`, `Authorization and App Configuration`, `Admin API Routes`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Why does `Document` connect `Document API Routes` to `Document Chunk Persistence`, `Document Search and CRUD`, `PDF and Office Extraction`, `Database Models and Session`, `Admin API Routes`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Why does `react` connect `Admin API Client` to `Frontend API and Layout`, `Frontend Build Tooling`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `User` (e.g. with `get_current_user()` and `admin_summary()`) actually correct?**
  _`User` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `Document` (e.g. with `admin_summary()` and `list_documents()`) actually correct?**
  _`Document` has 14 INFERRED edges - model-reasoned connections that need verification._
- **What connects `backend`, `name`, `private` to the rest of the system?**
  _126 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Frontend API and Layout` be split into smaller, more focused modules?**
  _Cohesion score 0.05303030303030303 - nodes in this community are weakly interconnected._