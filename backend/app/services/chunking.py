import re
from dataclasses import dataclass

import tiktoken

ENCODING = tiktoken.get_encoding("cl100k_base")


@dataclass(frozen=True)
class ChunkData:
    content: str
    page_number: int | None = None
    section_heading: str | None = None
    block_type: str | None = None
    token_count: int | None = None


def chunk_text_with_metadata(
    text: str,
    chunk_size: int = 400,
    chunk_overlap: int = 50,
    page_number: int | None = None,
    section_heading: str | None = None,
) -> list[ChunkData]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be non-negative and smaller than chunk_size."
        )

    chunks: list[ChunkData] = []
    active_heading: str | None = section_heading

    # Prefer section boundaries and paragraph boundaries over cutting text at
    # arbitrary token offsets. Large sections are still split into bounded
    # token windows, preserving the active heading as chunk metadata.
    sections = re.split(r"(?m)(?=^#{1,6}\s+)", text)
    sections = [section.strip() for section in sections if section.strip()]
    if not sections:
        sections = [text]

    for section in sections:
        heading_match = re.search(r"(?m)^#{1,6}\s+(.+?)\s*$", section)
        if heading_match:
            active_heading = heading_match.group(1).strip()[:500]
        section_tokens = ENCODING.encode(section)
        section_start = 0
        while section_start < len(section_tokens):
            window_end = min(section_start + chunk_size, len(section_tokens))
            # For windows with room to move, end at a nearby line/paragraph
            # boundary so lists and table rows stay more readable.
            if window_end < len(section_tokens):
                window = ENCODING.decode(section_tokens[section_start:window_end])
                boundary = max(window.rfind("\n\n"), window.rfind("\n"))
                if boundary >= len(window) * 0.65:
                    retained = len(ENCODING.encode(window[:boundary]))
                    if retained > 0:
                        window_end = section_start + retained
            content = ENCODING.decode(section_tokens[section_start:window_end]).strip()

            if content:
                headings = [
                    line.strip().lstrip("#").strip()
                    for line in content.splitlines()
                    if line.lstrip().startswith("#")
                ]

                if headings:
                    active_heading = headings[-1][:500]

                block_type = "table" if content.lstrip().startswith("|") else (
                    "section" if active_heading else "text"
                )
                chunks.append(
                    ChunkData(
                        content=content,
                        page_number=page_number,
                        section_heading=active_heading,
                        block_type=block_type,
                        token_count=len(ENCODING.encode(content)),
                    )
                )

            if window_end >= len(section_tokens):
                break
            section_start = max(section_start + 1, window_end - chunk_overlap)

    return chunks


def chunk_text(
    text: str,
    chunk_size: int = 400,
    chunk_overlap: int = 50,
) -> list[str]:
    return [
        chunk.content
        for chunk in chunk_text_with_metadata(
            text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    ]
