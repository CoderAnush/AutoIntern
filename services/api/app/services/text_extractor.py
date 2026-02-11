"""Text extraction service for multiple file formats."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_text_from_file(file_content: bytes, file_type: str) -> str:
    """
    Extract text from PDF, DOCX, or TXT files.

    Args:
        file_content: Raw file bytes
        file_type: File type (pdf, docx, txt)

    Returns:
        Extracted text

    Raises:
        ValueError: If file type not supported or extraction fails
    """
    file_type = file_type.lower()

    if file_type == 'pdf':
        return _extract_from_pdf(file_content)
    elif file_type == 'docx':
        return _extract_from_docx(file_content)
    elif file_type == 'txt':
        return _extract_from_txt(file_content)
    else:
        raise ValueError(f"Unsupported file type: {file_type}. Supported: pdf, docx, txt")


def _extract_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF using pdfplumber."""
    try:
        import pdfplumber
        import io

        all_text = []
        with pdfplumber.open(io.BytesIO(file_content)) as pdf:
            for page_num, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text()
                    if text:
                        all_text.append(text)
                except Exception as e:
                    logger.warning(f"Error extracting text from PDF page {page_num}: {e}")

        result = "\n".join(all_text)
        if not result:
            raise ValueError("No text could be extracted from PDF")
        return _clean_text(result)
    except ImportError:
        raise ValueError("pdfplumber not installed. Install with: pip install pdfplumber")
    except Exception as e:
        raise ValueError(f"PDF extraction failed: {str(e)}")


def _extract_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX using python-docx."""
    try:
        from docx import Document
        import io

        doc = Document(io.BytesIO(file_content))
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]

        if not paragraphs:
            raise ValueError("No text could be extracted from DOCX")

        result = "\n".join(paragraphs)
        return _clean_text(result)
    except ImportError:
        raise ValueError("python-docx not installed. Install with: pip install python-docx")
    except Exception as e:
        raise ValueError(f"DOCX extraction failed: {str(e)}")


def _extract_from_txt(file_content: bytes) -> str:
    """Extract text from plain TXT file."""
    try:
        text = file_content.decode('utf-8')
        if not text.strip():
            raise ValueError("No text found in TXT file")
        return _clean_text(text)
    except UnicodeDecodeError:
        raise ValueError("Could not decode TXT file. Please ensure it's UTF-8 encoded")
    except Exception as e:
        raise ValueError(f"TXT extraction failed: {str(e)}")


def _clean_text(text: str) -> str:
    """Clean extracted text: remove extra whitespace, normalize line endings."""
    # Remove multiple blank lines
    lines = text.split('\n')
    cleaned = [line.strip() for line in lines if line.strip()]
    return '\n'.join(cleaned)
