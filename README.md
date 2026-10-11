# AUTOSAR HLD Document Analysis Assistant

This submission contains a runnable offline MVP: PDF ingestion, page/section-aware
chunking, approved-document filtering, deterministic evidence retrieval, cited answers,
duplicate detection, baseline entity extraction, and a browser UI. Provider adapters
for local Ollama, Sentence Transformers, and ChromaDB are included for extension.

## Local-only design

The application has no cloud SDKs or cloud endpoints. The LLM, embedding model, and
vector database are configured as local/private services. Provider URLs are validated
to allow only loopback or Docker-network hosts (`localhost`, `127.0.0.1`, `::1`,
`ollama`, and `chroma`).

## Quick start

```powershell
cd .\autosar-hld-assistant
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
python -m uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs`. The `/health/live` endpoint is available without
any model or database service. `/health/ready` verifies database connectivity and
reports local provider configuration.

Open `http://localhost:8501` for the browser UI. Upload the supplied case-study PDF
and ask a question such as "What is the proposed solution and what technology is used?"
The answer contains document, version, page, and section citations.

The sample evidence files `demo_answer.json` and `demo_not_found.json` show a verified
cited response and the required insufficient-evidence response.

## Docker

Prerequisite: install and start Docker Desktop, with Linux containers enabled.
Docker Desktop is not installed on the current development machine, so the
commands below must be run after you install it.

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The API is exposed on port 8000 and the browser UI on port 8501. The compose
deployment runs the API, browser UI, Ollama, and ChromaDB on a private Docker
network. SQLite data is persisted in `./data`; Ollama and ChromaDB data are
persisted in named Docker volumes.

Open these URLs after startup:

- UI: `http://localhost:8501`
- API documentation: `http://localhost:8000/docs`
- API readiness: `http://localhost:8000/health/ready`

The application can use its deterministic evidence retrieval without an LLM.
For local model-backed answers, pull the configured model into the Ollama
container using your approved internal process:

```powershell
docker compose exec ollama ollama pull llama3.1:8b
```

Do not expose Ollama, ChromaDB, or the API publicly without adding authentication
and network controls. The current compose file is intended for local/private
development and evaluation.

To stop the deployment:

```powershell
docker compose down
```

To stop it and remove the persisted model/vector volumes:

```powershell
docker compose down -v
```

If Streamlit cannot be installed because of local disk restrictions, run the
dependency-free browser fallback instead:

```powershell
.\.venv\Scripts\python.exe -m uvicorn ui.web:app --host 127.0.0.1 --port 8501
```

## Phase 1 verification

```powershell
python -m pytest
python -m ruff check app tests
```

## Phase roadmap

1. Foundation: configuration, database models, provider abstractions, and health endpoints.
2. MVP delivered: PDF parsing, chunking, persistence, approved filtering, cited retrieval,
   idempotency, browser UI, and baseline entity extraction.
3. Extension roadmap: OCR, semantic embeddings, full hybrid retrieval, review actions,
   graphs, revision comparison, RBAC, exports, and the golden evaluation harness.

## Submission documents

- `..\AUTOSAR_HLD_Assistant_Project_Synopsis.docx`
- `..\AUTOSAR_HLD_Assistant_Technical_Report.docx`

Regenerate them from the supplied templates with:

```powershell
.\.venv\Scripts\python.exe scripts\generate_reports.py
```
