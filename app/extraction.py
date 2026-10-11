import re
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractedEntity:
    entity_type: str
    name: str
    confidence: float
    source_page: int = 1
    section_path: str = "Unclassified"
    source_snippet: str = ""


PATTERNS = {
    "SW Component": re.compile(
        r"\b([A-Za-z][A-Za-z0-9_]*(?:Swc|SWC|Component|_SWC))\b"
    ),
    "Port": re.compile(r"\b([A-Za-z][A-Za-z0-9_]*(?:PPort|RPort|Port))\b"),
    "Interface": re.compile(r"\b([A-Za-z][A-Za-z0-9_]*(?:Interface|If))\b"),
    "Signal": re.compile(r"\b([A-Za-z][A-Za-z0-9_]*(?:Signal|_Sig))\b"),
}


def extract_entities(text: str) -> list[ExtractedEntity]:
    seen: set[tuple[str, str]] = set()
    entities: list[ExtractedEntity] = []
    for entity_type, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            key = (entity_type, match.group(1))
            if key not in seen:
                seen.add(key)
                entities.append(ExtractedEntity(entity_type, match.group(1), 0.82))
    return entities


def extract_entities_from_chunks(
    chunks: Iterable[object],
) -> list[ExtractedEntity]:
    """Extract entities while retaining the chunk that supplied each match."""
    seen: set[tuple[str, str, int, str]] = set()
    entities: list[ExtractedEntity] = []
    for chunk in chunks:
        content = str(getattr(chunk, "content", ""))
        page = int(getattr(chunk, "page_number", 1))
        section = str(getattr(chunk, "section_path", "Unclassified"))
        for entity_type, pattern in PATTERNS.items():
            for match in pattern.finditer(content):
                name = match.group(1)
                key = (entity_type, name.lower(), page, section)
                if key in seen:
                    continue
                seen.add(key)
                start = max(0, match.start() - 100)
                end = min(len(content), match.end() + 160)
                entities.append(
                    ExtractedEntity(
                        entity_type=entity_type,
                        name=name,
                        confidence=0.82,
                        source_page=page,
                        section_path=section,
                        source_snippet=content[start:end].strip(),
                    )
                )
    return entities
