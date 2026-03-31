import re


NOISE_PATTERNS = [
    re.compile(r"^\s*(home|about|contact|privacy|terms)(\s*[|/-]\s*\w+)*\s*$", re.I),
    re.compile(r"^\s*(accept|allow|manage)\s+cookies?\s*$", re.I),
    re.compile(r"^\s*subscribe\s*(now|for updates)?\s*$", re.I),
    re.compile(r"^\s*(all rights reserved|copyright)\b", re.I),
]


def _is_noise_line(line: str) -> bool:
    text = line.strip()
    if not text:
        return False
    for pattern in NOISE_PATTERNS:
        if pattern.search(text):
            return True
    return False


def clean_markdown_content(raw_content: str) -> str:
    """Lightly clean markdown while preserving structure and images."""
    if not raw_content:
        return ""

    kept_lines: list[str] = []
    for line in raw_content.splitlines():
        if _is_noise_line(line):
            continue
        kept_lines.append(line.rstrip())

    cleaned = "\n".join(kept_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned
