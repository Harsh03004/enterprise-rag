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

    tokens = ENCODING.encode(text)
    step = chunk_size - chunk_overlap
    chunks: list[ChunkData] = []
    section_heading: str | None = None
    start = 0

    while start < len(tokens):
        content = ENCODING.decode(tokens[start : start + chunk_size]).strip()

        if content:
            headings = [
                line.strip().lstrip("#").strip()
                for line in content.splitlines()
                if line.lstrip().startswith("#")
            ]

            if headings:
                section_heading = headings[-1][:500]

            chunks.append(
                ChunkData(
                    content=content,
                    page_number=page_number,
                    section_heading=section_heading,
                    block_type="section" if section_heading else "text",
                    token_count=len(ENCODING.encode(content)),
                )
            )

        start += step

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
