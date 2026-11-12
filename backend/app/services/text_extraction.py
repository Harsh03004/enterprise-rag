import logging
import re
from io import BytesIO
from pathlib import Path
from typing import cast

import fitz
import pytesseract
from docx import Document as load_docx
from docx.document import Document as DocxDocumentType
from PIL import Image
from pypdf import PdfReader

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def extract_text_blocks(file_path: str) -> list[tuple[str, int | None]]:
    path = PROJECT_ROOT / file_path
    suffix = path.suffix.lower()

    if suffix in {".md", ".txt", ".docx"}:
        return [(extract_text(file_path), None)]

    if suffix == ".pdf":
        return extract_pdf_page_blocks(path)

    raise ValueError(f"Unsupported file type: {suffix}")


def extract_text(file_path: str) -> str:
    path = PROJECT_ROOT / file_path

    suffix = path.suffix.lower()

    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8")

    if suffix == ".pdf":
        return extract_pdf(path)

    if suffix == ".docx":
        return extract_docx(path)

    raise ValueError(f"Unsupported file type: {suffix}")


def is_usable_text(text: str) -> bool:
    """
    Determine whether extracted text is usable.

    Very short or heavily corrupted text is considered
    unsuitable and will be replaced with OCR output.
    """

    if not text.strip():
        return False

    if len(text.strip()) < 30:
        return False

    alphanumeric_count = sum(character.isalnum() for character in text)

    printable_count = sum(character.isprintable() for character in text)

    if printable_count == 0:
        return False

    alphanumeric_ratio = alphanumeric_count / len(text)

    printable_ratio = printable_count / len(text)

    return alphanumeric_ratio >= 0.45 and printable_ratio >= 0.85


def extract_pdf(path: Path) -> str:
    """
    Extract text from a PDF.

    Uses normal PDF text extraction when the extracted
    text appears usable. If a page has no text or the
    extracted text appears corrupted/garbled, that page
    is sent through OCR.

    This allows normal, scanned, and mixed PDFs to work.
    """

    return "\n\n".join(extract_pdf_pages(path))


def extract_pdf_pages(path: Path) -> list[str]:
    return [text for text, _page_number in extract_pdf_page_blocks(path)]


def extract_pdf_page_blocks(path: Path) -> list[tuple[str, int]]:
    reader = PdfReader(path)
    normal_pages = [(page.extract_text() or "").strip() for page in reader.pages]
    document = fitz.open(path)
    pages: list[tuple[str, int]] = []

    try:
        for index, normal_text in enumerate(normal_pages):
            if is_usable_text(normal_text):
                page_text = normal_text
            else:
                page = cast(fitz.Page, document[index])
                page_text = ocr_page(page)

            # Preserve detected PDF tables in a stable, chunkable markdown
            # representation alongside normal page text.
            if is_usable_text(normal_text):
                try:
                    table_blocks = []
                    for table in cast(fitz.Page, document[index]).find_tables().tables:
                        rows = table.extract()
                        for row in rows:
                            cells = [str(cell or "").replace("\n", " / ").strip() for cell in row]
                            if any(cells):
                                table_blocks.append("| " + " | ".join(cells) + " |")
                    if table_blocks:
                        page_text = f"{page_text}\n\n" + "\n".join(table_blocks)
                except (AttributeError, RuntimeError, ValueError):
                    # Some PDFs contain vector layouts that are not tables.
                    pass

            if page_text.strip():
                pages.append((page_text.strip(), index + 1))

    finally:
        document.close()

    return pages


def ocr_pdf(path: Path) -> str:
    """
    OCR every page of a PDF.
    """

    document = fitz.open(path)

    pages = []

    try:
        for raw_page in document:
            page = cast(fitz.Page, raw_page)
            text = ocr_page(page)

            if text:
                pages.append(text)

    finally:
        document.close()

    return "\n\n".join(pages)


def ocr_page(page: fitz.Page) -> str:
    """
    Render a PDF page to an image and run Tesseract OCR.
    """

    pixmap = page.get_pixmap(
        matrix=fitz.Matrix(2, 2),
        alpha=False,
    )

    image = pixmap.tobytes("png")

    pil_image = Image.open(BytesIO(image))

    text = pytesseract.image_to_string(
        pil_image,
        lang="eng",
    )

    return text.strip()


def extract_docx(path: Path) -> str:
    """
    Extract text from a DOCX document.

    Extracts:
    - Normal paragraphs
    - Tables
    - Text contained inside embedded images
    """

    document = load_docx(str(path))

    sections = []

    # ---------------------------------------------------------
    # Paragraphs
    # ---------------------------------------------------------

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()

        if text:
            style_name = paragraph.style.name if paragraph.style is not None else ""
            heading = re.fullmatch(r"Heading\s+(\d+)", style_name, flags=re.IGNORECASE)
            if heading:
                level = min(6, max(1, int(heading.group(1))))
                sections.append(f"{'#' * level} {text}")
            else:
                sections.append(text)

    # ---------------------------------------------------------
    # Tables
    # ---------------------------------------------------------

    for table in document.tables:
        rows = []

        for row in table.rows:
            cells = [cell.text.strip().replace("\n", " / ") for cell in row.cells]

            if any(cells):
                rows.append("| " + " | ".join(cells) + " |")

        if rows:
            sections.append("\n".join(rows))

    # ---------------------------------------------------------
    # Embedded images
    # ---------------------------------------------------------

    image_text = extract_docx_images(document)

    if image_text:
        sections.append(image_text)

    return "\n\n".join(sections)


def extract_docx_images(
    document: DocxDocumentType,
) -> str:
    """
    Extract embedded images from a DOCX document
    and run OCR on them.
    """

    image_sections = []

    image_index = 0

    for relationship in document.part.rels.values():
        if "image" not in relationship.reltype:
            continue

        image_index += 1

        try:
            image_part = relationship.target_part
            image_bytes = image_part.blob

            image = Image.open(BytesIO(image_bytes))

            text = pytesseract.image_to_string(
                image,
                lang="eng",
            ).strip()

            if text:
                image_sections.append(f"[Image {image_index}]\n{text}")

        except (OSError, RuntimeError, ValueError) as error:
            logger.warning("docx_image_ocr_failed", extra={"image_index": image_index, "error": str(error)})

    return "\n\n".join(image_sections)
