"""PDF parser for financial disclosures and other PDF documents."""

from typing import List, Optional
import pdfplumber


def extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from a PDF file."""
    text_parts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_tables_from_pdf(file_path: str) -> List[List[List[str]]]:
    """Extract all tables from a PDF file."""
    all_tables = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if tables:
                all_tables.extend(tables)
    return all_tables
