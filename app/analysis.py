import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Change:
    change_type: str
    entity_type: str
    name: str
    evidence: str


@dataclass(frozen=True)
class ValidationFinding:
    rule: str
    severity: str
    message: str
    evidence: str


def normalize_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def compare_entities(
    left: list[dict[str, object]], right: list[dict[str, object]]
) -> list[Change]:
    """Compare reviewed or extracted entity inventories without inventing relationships."""
    left_map = {
        (str(item["entity_type"]), normalize_name(str(item["name"]))): item for item in left
    }
    right_map = {
        (str(item["entity_type"]), normalize_name(str(item["name"]))): item for item in right
    }
    changes: list[Change] = []
    for key in sorted(right_map.keys() - left_map.keys()):
        item = right_map[key]
        changes.append(
            Change(
                "added",
                str(item["entity_type"]),
                str(item["name"]),
                str(item.get("citation", "")),
            )
        )
    for key in sorted(left_map.keys() - right_map.keys()):
        item = left_map[key]
        changes.append(
            Change(
                "removed",
                str(item["entity_type"]),
                str(item["name"]),
                str(item.get("citation", "")),
            )
        )
    return changes


def validate_chunks(chunks: list[dict[str, object]]) -> list[ValidationFinding]:
    """Run conservative checks and return findings only when text supplies evidence."""
    all_text = "\n".join(str(item.get("content", "")) for item in chunks)
    findings: list[ValidationFinding] = []
    defined_signals = {
        normalize_name(match.group(1))
        for match in re.finditer(
            r"\b([A-Za-z][A-Za-z0-9_]*(?:Signal|_Sig))\b", all_text, re.IGNORECASE
        )
    }
    for match in re.finditer(
        r"\b(?:uses|consumes|reads|receives)\s+([A-Za-z][A-Za-z0-9_]*(?:Signal|_Sig))\b",
        all_text,
        re.IGNORECASE,
    ):
        signal = normalize_name(match.group(1))
        if signal not in defined_signals:
            findings.append(
                ValidationFinding(
                    "undefined_signal",
                    "High",
                    f"Signal {match.group(1)} is referenced but not defined in the supplied text.",
                    match.group(0),
                )
            )
    if re.search(r"\b(required|RPort)\b", all_text, re.IGNORECASE) and not re.search(
        r"\b(provided|PPort|provider)\b", all_text, re.IGNORECASE
    ):
        findings.append(
            ValidationFinding(
                "unmatched_required_port",
                "Medium",
                "A required-port reference is present, but no provider reference was found.",
                "required/RPort",
            )
        )
    return findings
