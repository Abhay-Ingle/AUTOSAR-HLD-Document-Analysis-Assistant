import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass(frozen=True)
class ParsedChunk:
    page_number: int
    section_path: str
    content: str
    chunk_type: str = "text"


def file_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _clean_text(value: str) -> str:
    """Repair common UTF-8 bytes decoded as Latin-1 by PDF text extractors."""
    if any(marker in value for marker in ("Â", "â", "ð", "Ã")):
        try:
            return value.encode("latin1").decode("utf-8")
        except UnicodeError:
            pass
    return value


def _is_heading(line: str) -> bool:
    stripped = line.strip()
    return bool(
        stripped
        and len(stripped) <= 160
        and (
            re.match(r"^(?:\d+(?:\.\d+)*|[A-Z])[\s.)-]+", stripped)
            or stripped.isupper()
        )
    )


def parse_pdf(path: Path, max_chars: int = 1800) -> list[ParsedChunk]:
    reader = PdfReader(str(path))
    chunks: list[ParsedChunk] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = _clean_text((page.extract_text() or "").replace("\x00", "").strip())
        if not text:
            text = _clean_text(_ocr_page(path, page_number))
        if not text:
            continue
        section = "Unclassified"
        buffer: list[str] = []
        for raw_line in text.splitlines():
            line = " ".join(raw_line.split())
            if not line:
                continue
            if _is_heading(line):
                if buffer:
                    chunks.extend(_flush(buffer, page_number, section, max_chars))
                    buffer = []
                section = line
            else:
                buffer.append(line)
        if buffer:
            chunks.extend(_flush(buffer, page_number, section, max_chars))
    return chunks


def _ocr_page(path: Path, page_number: int) -> str:
    """OCR a scanned page when the optional local OCR stack is installed."""
    try:
        import fitz  # type: ignore[import-not-found]
        import pytesseract  # type: ignore[import-not-found]
        from PIL import Image  # type: ignore[import-not-found]
    except ImportError:
        return ""
    try:
        document = fitz.open(path)
        page = document[page_number - 1]
        pixels = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        image = Image.frombytes("RGB", [pixels.width, pixels.height], pixels.samples)
        return pytesseract.image_to_string(image).replace("\x00", "").strip()
    except (OSError, RuntimeError, IndexError):
        return ""


def _flush(lines: list[str], page_number: int, section: str, max_chars: int) -> list[ParsedChunk]:
    content = " ".join(lines)
    return [
        ParsedChunk(page_number, section, content[start : start + max_chars])
        for start in range(0, len(content), max_chars)
    ]
