from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def extract_text(file_path: str) -> str:
    path = PROJECT_ROOT / file_path

    suffix = path.suffix.lower()

    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8")

    if suffix == ".pdf":
        return extract_pdf(path)

    if suffix == ".docx":
        return extract_docx(path)

    raise ValueError(
        f"Unsupported file type: {suffix}"
    )


def extract_pdf(path: Path) -> str:
    reader = PdfReader(path)

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n\n".join(pages)


def extract_docx(path: Path) -> str:
    document = DocxDocument(path)

    paragraphs = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(paragraph.text)

    return "\n\n".join(paragraphs)