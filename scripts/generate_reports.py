"""Generate submission documents from the supplied DOCX templates."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
from xml.sax.saxutils import escape


BASE = Path(r"C:\Users\Abhay\Downloads\Tata technologies project")
SYNOPSIS_TEMPLATE = BASE / "AIML_Project_Case_Study_Implementation_Synopsis.docx"
REPORT_TEMPLATE = BASE / "PCCOE_AIML_Technical_Report_Template.docx"

NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{NS}}}"


def paragraph(text: str = "", style: str | None = None, bold: bool = False) -> str:
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    run_style = "<w:rPr><w:b/></w:rPr>" if bold else ""
    return f"<w:p>{ppr}<w:r>{run_style}<w:t xml:space=\"preserve\">{escape(text)}</w:t></w:r></w:p>"


def heading(text: str, level: int = 1) -> str:
    return paragraph(text, f"Heading{level}")


def table(rows: list[list[str]]) -> str:
    output = ['<w:tbl><w:tblPr><w:tblBorders>'
              '<w:top w:val="single" w:sz="4"/><w:left w:val="single" w:sz="4"/>'
              '<w:bottom w:val="single" w:sz="4"/><w:right w:val="single" w:sz="4"/>'
              '<w:insideH w:val="single" w:sz="4"/><w:insideV w:val="single" w:sz="4"/>'
              '</w:tblBorders></w:tblPr>']
    for row in rows:
        output.append("<w:tr>")
        for cell in row:
            output.append(f"<w:tc><w:p><w:r><w:t xml:space=\"preserve\">{escape(cell)}</w:t></w:r></w:p></w:tc>")
        output.append("</w:tr>")
    output.append("</w:tbl>")
    return "".join(output)


def document_xml(body: list[str]) -> bytes:
    content = "".join(body)
    return (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{NS}"><w:body>{content}'
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134"/>'
        "</w:sectPr></w:body></w:document>"
    ).encode()


def write_from_template(template: Path, target: Path, body: list[str]) -> None:
    with ZipFile(template) as source, ZipFile(target, "w", ZIP_DEFLATED) as destination:
        for item in source.infolist():
            data = document_xml(body) if item.filename == "word/document.xml" else source.read(item.filename)
            destination.writestr(item, data)


synopsis = [
    heading("TATA TECHNOLOGIES LTD.", 1),
    paragraph("TECH PULSE FY-26 | AI/ML Capstone Project"),
    heading("PROJECT SYNOPSIS", 1),
    heading("Student Details", 2),
    table([
        ["Institute / University", "PCCOE"],
        ["Programme / Batch", "AIML / FY-26"],
        ["Student Name", "____________________________"],
        ["PRN", "____________________________"],
    ]),
    heading("1. Case Study ID and Project Title / Topic", 2),
    paragraph("Case Study ID: CS1"),
    paragraph("Project Title: AUTOSAR HLD Document Analysis Assistant"),
    heading("2. Objectives", 2),
    paragraph("The project converts approved AUTOSAR High-Level Design PDFs into a searchable architecture knowledge base. Its objectives are to reduce manual review effort, improve component/interface/signal traceability, support impact analysis and test planning, and provide evidence-grounded answers with page and section citations."),
    heading("3. Scope", 2),
    paragraph("In Scope: PDF upload, SHA-256 deduplication, document metadata, text extraction, section-aware chunking, approved-source filtering, local retrieval, cited question answering, deterministic AUTOSAR entity extraction, review-ready entity status, and API/browser demonstration."),
    paragraph("Out of Scope: automatic architecture approval, modification of source HLDs, replacement of formal governance, production OCR for scanned pages, and unverified claims about safety or compliance."),
    heading("4. Proposed Approach", 2),
    table([
        ["Area", "Selected approach"],
        ["Pre-trained model", "Optional local Ollama model such as Llama 3.1; provider adapter is configurable. The verified demo uses deterministic evidence assembly when no LLM service is available."],
        ["Embedding model", "Configurable Sentence Transformers BGE/E5 adapter; provider contract included."],
        ["Vector store", "ChromaDB adapter with metadata filters; SQLite keyword retrieval is used in the offline demo."],
        ["RAG pipeline", "Approved-document filter -> token overlap retrieval -> source snippets -> cited response; insufficient evidence returns a fixed not-found response."],
        ["Service layer and UI", "FastAPI modular API and a local browser UI. Streamlit remains an optional pilot UI."],
        ["Rules", "PDF text extraction, heading detection, chunking, SHA-256 deduplication, AUTOSAR naming regexes, and review-status workflow."],
    ]),
    paragraph("Proposed System / Architecture: HLD PDF -> PyPDF parser -> page/section chunks -> SQLite metadata and local vector adapter -> hybrid retrieval -> grounded cited response -> engineer review/export."),
    heading("5. Input Data / Knowledge Base", 2),
    paragraph("Approved/synthetic AUTOSAR HLD PDFs are the knowledge source. The supplied four-page case-study reference PDF was used as the verified demonstration input. Each document retains title, version, revision, status, uploader, timestamp, hash, page, section, and source snippet metadata."),
    paragraph("Preprocessing includes text normalization, heading detection, section-aware chunking, page preservation, duplicate detection, and architecture-name extraction. Scanned pages are explicitly rejected for the current MVP with a clear OCR-required message rather than silently producing empty evidence."),
    heading("6. Expected Outcomes and Evaluation Plan", 2),
    paragraph("Expected outputs are an approved document inventory, searchable chunks, cited answers, extracted architecture entities, review-ready records, and structured API responses."),
    table([
        ["Evaluation", "Method"],
        ["Ingestion", "Upload the supplied PDF; verify page and chunk counts."],
        ["Groundedness", "Check every returned citation contains document, version, page, section, and source snippet."],
        ["Insufficient evidence", "Ask an unrelated question and verify the exact not-found response."],
        ["Idempotency", "Upload the same file twice and verify the second result is already_ingested."],
    ]),
    paragraph("Responsible AI: local/private configuration, approved-only retrieval, citations, deterministic not-found behavior, no source-document mutation, review status, and audit-ready metadata."),
    paragraph("MLOps/deployment: Python virtual environment, typed modular FastAPI package, pytest/Ruff checks, environment-based configuration, and optional Docker configuration for later deployment."),
    heading("7. Planned AI-Tool Usage", 2),
    table([
        ["AI Tool / Model", "Purpose", "Artifact affected"],
        ["GitHub Copilot SDK in VS Code", "Coding assistance, debugging, documentation generation", "Application source and submission documents"],
        ["Local Ollama model (optional)", "Private answer generation after retrieval", "RAG answer layer"],
    ]),
    paragraph("Student Declaration: I will explain and verify the implementation, keep the approved case-study scope, and obtain faculty approval before any major scope change."),
    paragraph("Name and Signature: ______________________________    Date: ________________"),
]

report = [
    heading("TATA TECHNOLOGIES LTD.", 1),
    paragraph("TECH PULSE FY-26 | AI/ML Capstone Project"),
    heading("TECHNICAL REPORT", 1),
    table([
        ["Field", "Details"],
        ["Institute / University", "PCCOE"],
        ["Programme / Batch", "AIML / FY-26"],
        ["Student Name", "____________________________"],
        ["PRN", "____________________________"],
        ["Case Study ID", "CS1"],
        ["Project Title", "AUTOSAR HLD Document Analysis Assistant"],
    ]),
    heading("1. Problem Statement and Intended Users", 2),
    paragraph("AUTOSAR HLDs contain architecture knowledge across hundreds of pages, tables, and sections. Manual interpretation makes traceability, impact analysis, mismatch discovery, onboarding, and test planning slow and inconsistent. Intended users are system/AUTOSAR architects, software developers, integration engineers, test engineers, and engineering managers."),
    heading("2. Input Data / Knowledge Base", 2),
    table([
        ["Item", "Description"],
        ["Sources", "Approved AUTOSAR HLD PDF documents; verified demo uses Automotive_Engineering_AI_Project_Case_Studies (1)_removed.pdf."],
        ["Size and format", "Verified run: 4-page PDF, 198,554 bytes; stored unchanged with SHA-256 hash."],
        ["Preprocessing / EDA done", "Text extraction, whitespace normalization, heading detection, page preservation, duplicate hash check."],
        ["Chunking strategy", "Section-aware text chunks, maximum 1,800 characters, each retaining page and section path."],
    ]),
    heading("3. Solution Architecture", 2),
    table([
        ["Component", "Choice (name, version, hosting)"],
        ["Pre-trained model", "Ollama-compatible local model, configurable; no cloud API."],
        ["Embedding model", "Sentence Transformers BGE/E5 adapter, configurable and local."],
        ["Vector store", "ChromaDB adapter; SQLite stores structured metadata and the demo retrieval path."],
        ["RAG pipeline", "Approved filter, lexical retrieval, evidence snippets, citations, confidence, fixed not-found guardrail."],
        ["Service layer and UI", "FastAPI 0.115+ backend; dependency-free local browser UI on port 8501."],
        ["Tools / rules", "PyPDF, SHA-256, heading parser, regex entity extraction, SQLAlchemy models, pytest, Ruff."],
    ]),
    paragraph("System architecture diagram: HLD PDF -> Ingestion -> Page/Section Chunks -> SQLite + Vector Adapter -> Retrieval -> Local LLM/Deterministic Evidence -> Cited Answer -> Human Review."),
    heading("4. Implementation and Configuration", 2),
    paragraph("The project is located in autosar-hld-assistant. Configuration is in .env and app/core/config.py. The API routes are /documents/upload, /documents, /qa/ask, /health/live, and /health/ready. The upload route rejects non-PDF files, persists the source file, parses selectable text, creates chunks and pending entities, and returns an ingestion summary. Approved status is required by the Q&A route."),
    paragraph("Run command: .venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000. UI command: .venv\\Scripts\\python.exe -m uvicorn ui.web:app --host 127.0.0.1 --port 8501."),
    heading("5. Evaluation Steps and Results", 2),
    table([
        ["#", "Test question / scenario", "Expected answer / behaviour", "Result"],
        ["1", "Upload supplied case-study PDF", "Ingest pages and chunks", "Pass: 4 pages, 17 chunks"],
        ["2", "Ask: proposed solution and technology", "Answer only from evidence with citations", "Pass: 5 citations with document/version/page/section"],
        ["3", "Ask unrelated question", "Return not-found instead of guessing", "Pass: deterministic not-found response"],
        ["4", "Upload the same file twice", "Deduplicate by SHA-256", "Pass: second result is already_ingested"],
        ["5", "Run automated checks", "No syntax/lint/test failure", "Pass: 3 pytest tests and Ruff checks passed"],
    ]),
    table([
        ["Metric", "Score / observation"],
        ["Ingestion correctness", "Pass on supplied 4-page PDF; 17 section-aware chunks"],
        ["Citation completeness", "100% of verified answer citations contain document, version, page, and section"],
        ["Groundedness guardrail", "Pass: no-overlap question returns exact not-found response"],
        ["Latency", "Local API response completed within the interactive test command; benchmark to be expanded with 500+ page corpus"],
        ["Extraction quality", "Regex extraction baseline included; precision/recall golden set is planned for Phase 6"],
    ]),
    heading("6. Responsible AI Measures", 2),
    table([
        ["Area", "Measure adopted"],
        ["Grounding and citations", "Only approved documents are searchable; source snippets and page/section citations are returned."],
        ["Privacy", "Local/private provider URLs; documents remain in local data directory."],
        ["Security", "Project/document metadata filters, controlled upload validation, no source mutation."],
        ["Human oversight / review", "Entities start Pending and are intended for accept/edit/reject review before use."],
    ]),
    heading("7. Innovation Highlights", 2),
    paragraph("1. Evidence-first fallback works without a running LLM, making the demo reproducible offline. 2. Approved-version filtering and explicit not-found behavior reduce hallucination risk. 3. The provider contracts allow Ollama, BGE/E5, and ChromaDB to be swapped without changing business logic."),
    heading("8. Screenshots, Logs and Evidence", 2),
    paragraph("Figure 1: Browser UI at http://localhost:8501 showing Backend status: Connected and local service details."),
    paragraph("Figure 2: FastAPI Swagger UI at http://localhost:8000/docs showing health, document ingestion, and Q&A endpoints."),
    paragraph("Evidence log: upload response reported document_id, status=ingested, pages=4, chunks=17. Q&A response included five citations such as [AUTOSAR HLD Case Study v1.0, p.2, §5. Proposed Solution]."),
    heading("9. Reflection and Conclusions", 2),
    paragraph("The implementation demonstrates a usable local foundation and an offline evidence-grounded MVP. The main limitation is that scanned-page OCR, dense table extraction, semantic embeddings, full hybrid BM25/vector retrieval, RBAC, exports, revision comparison, and a golden evaluation set require the next development increment. The design keeps those capabilities modular and does not compromise the core citation and human-review controls."),
    heading("10. AI-Tool Usage Declaration", 2),
    table([
        ["AI tool / model", "Purpose", "Artifact affected", "Verified by Student"],
        ["GitHub Copilot SDK in VS Code", "Coding and report drafting assistance", "Source code, README, synopsis, report", "Y / to be reviewed"],
        ["Local Ollama model (optional)", "Private grounded generation", "RAG provider", "Y / after local model validation"],
    ]),
    heading("11. Student Declaration", 2),
    paragraph("I confirm that this report represents my own understanding and contribution, that the work follows the approved case-study scope, and that I can explain every significant part of the implementation."),
    paragraph("Signature: ____________________    Date: ________________    Name: ____________________    PRN: ____________________"),
]


if __name__ == "__main__":
    write_from_template(SYNOPSIS_TEMPLATE, BASE / "AUTOSAR_HLD_Assistant_Project_Synopsis.docx", synopsis)
    write_from_template(REPORT_TEMPLATE, BASE / "AUTOSAR_HLD_Assistant_Technical_Report.docx", report)
    print("Generated synopsis and technical report.")
