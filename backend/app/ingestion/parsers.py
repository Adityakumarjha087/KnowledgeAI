import io
from pypdf import PdfReader
from docx import Document as DocxDocument


def parse_pdf(file_bytes: bytes) -> tuple[str, int]:
    """Extracts text from PDF page-by-page using pypdf. Returns (text, page_count)."""
    text_content = []
    pdf_file = io.BytesIO(file_bytes)
    reader = PdfReader(pdf_file)
    page_count = len(reader.pages)
    
    for page_num in range(page_count):
        page = reader.pages[page_num]
        page_text = page.extract_text() or ""
        # Embed page indicators for citation reference extraction downstream
        text_content.append(f"[PAGE_{page_num + 1}]\n{page_text}")
        
    return "\n\n".join(text_content), page_count


def parse_docx(file_bytes: bytes) -> tuple[str, int]:
    """Extracts text from a Word DOCX document. Returns (text, page_count)."""
    docx_file = io.BytesIO(file_bytes)
    doc = DocxDocument(docx_file)
    
    paragraphs_text = []
    for para in doc.paragraphs:
        paragraphs_text.append(para.text)
        
    text = "\n".join(paragraphs_text)
    # Word docx layout varies; estimate page count (1 page per 3000 characters)
    page_count = max(1, len(text) // 3000)
    return text, page_count


def parse_txt_or_md(file_bytes: bytes) -> tuple[str, int]:
    """Decodes plain text or Markdown files to UTF-8. Returns (text, page_count)."""
    text = file_bytes.decode("utf-8", errors="ignore")
    # Estimate page count (1 page per 3000 characters)
    page_count = max(1, len(text) // 3000)
    return text, page_count


def parse_document(file_bytes: bytes, file_extension: str) -> tuple[str, int]:
    """Router to parse document content based on its extension"""
    ext = file_extension.lower().strip(".")
    if ext == "pdf":
        return parse_pdf(file_bytes)
    elif ext in ("docx", "doc"):
        return parse_docx(file_bytes)
    elif ext in ("txt", "md"):
        return parse_txt_or_md(file_bytes)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")
