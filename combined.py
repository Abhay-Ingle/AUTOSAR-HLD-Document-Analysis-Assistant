"""Combined entry point for single-service deployment (e.g. Render.com).

Serves the backend API and the browser UI from a single FastAPI process.
The UI JavaScript URLs are rewritten to call backend routes directly,
eliminating the need for proxy endpoints or inter-service HTTP calls.
"""

from fastapi.responses import HTMLResponse

from app.main import app  # fully-configured app with all routers
from ui.web import PAGE

# Rewrite UI fetch URLs to point directly to backend API routes
# instead of going through the /api/* proxy endpoints.
_PAGE = (
    PAGE
    .replace("fetch('/api/status')", "fetch('/health/ready')")
    .replace("fetch('/api/documents')", "fetch('/documents')")
    .replace("fetch('/api/upload'", "fetch('/documents/upload'")
    .replace("fetch('/api/ask'", "fetch('/qa/ask'")
    .replace("fetch('/api/compare'", "fetch('/analysis/compare'")
    .replace("fetch('/api/validate/'", "fetch('/analysis/validate/'")
    .replace(
        "fetch('/api/entities/'+encodeURIComponent(id))",
        "fetch('/analysis/documents/'+encodeURIComponent(id)+'/entities')",
    )
    .replace("http://localhost:8000/docs", "/docs")
    .replace("http://localhost:8000", "")
    .replace("http://127.0.0.1:8000", "")
)


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    """Serve the browser UI with API paths rewritten for same-origin."""
    return _PAGE
