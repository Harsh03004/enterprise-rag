# Enterprise RAG Platform

A document question-answering application with a FastAPI backend, React frontend, PostgreSQL/pgvector storage, Redis/Celery ingestion jobs, hybrid retrieval, reranking, and Gemini or Ollama generation.

## Run locally with Docker Compose

Set a strong `SECRET_KEY`, then start the stack:

```bash
export SECRET_KEY="replace-with-a-long-random-secret"
docker compose -f infrastructure/docker/docker-compose.yml up --build
```

The frontend is served at `http://localhost:5173`; the API is at `http://localhost:8000`. PostgreSQL is published on host port `5434` by default (`POSTGRES_HOST_PORT` overrides it); containers use PostgreSQL internally on port `5432`. Compose runs PostgreSQL, Redis, the API, and a separate worker. API and worker share the `uploaded_files` volume. By default, Ollama is expected on the host at `http://localhost:11434`; set `OLLAMA_BASE_URL` to a different OpenAI-compatible Ollama endpoint when needed. Select `LLM_PROVIDER=gemini` and provide `GEMINI_API_KEY` to use Gemini. `GEMINI_MODEL` and `OLLAMA_MODEL` select provider models.

To use a local Ollama model, pull the desired model separately and set `OLLAMA_MODEL` (for example, `qwen3:8b`). The Compose stack does not install or run Ollama itself.

## Ingestion

Supported uploads are PDF, DOCX, Markdown (`.md`), and plain text (`.txt`). PDFs use text extraction with OCR fallback; DOCX extraction includes paragraphs, tables, and OCR of embedded images. Website ingestion accepts public HTTP/HTTPS pages and extracts visible page text. Processing occurs asynchronously; document status is visible in the sidebar.

## Backend checks

With the backend virtual environment/dependencies available:

```bash
cd backend
uv run python -m compileall app
uv run python -m unittest test_hardening.py -v
```

## Frontend checks

```bash
cd frontend
npm ci
npm run build
```

## Evaluation

The evaluator takes an existing indexed document or collection and a dataset JSON file:

```bash
cd backend
uv run python -m app.evaluation.runner \
  --dataset evaluation_dataset.json \
  --user-id USER_ID \
  --document-id DOCUMENT_ID \
  --output evaluation_results.json
```

To compare aggregate metrics with a prior result, add `--baseline PATH` and optionally `--max-regression 0.05`. The evaluation requires database access and a working embedding model and LLM provider. Results are not a CI gate yet.

See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment and PostgreSQL backup/restore notes.
