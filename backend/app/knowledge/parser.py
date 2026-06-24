import io
import fitz  # PyMuPDF
import docx
import csv
import json
import markdown
from bs4 import BeautifulSoup
from typing import Any

class DocumentParser:
    """Extracts raw text from various document formats."""
    
    @staticmethod
    def parse_pdf(file_bytes: bytes) -> str:
        text = []
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page in doc:
                text.append(page.get_text())
        return "\n".join(text)
        
    @staticmethod
    def parse_docx(file_bytes: bytes) -> str:
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n".join([p.text for p in doc.paragraphs])
        
    @staticmethod
    def parse_txt(file_bytes: bytes) -> str:
        return file_bytes.decode('utf-8', errors='ignore')
        
    @staticmethod
    def parse_csv(file_bytes: bytes) -> str:
        content = file_bytes.decode('utf-8', errors='ignore')
        reader = csv.reader(io.StringIO(content))
        lines = []
        for row in reader:
            lines.append(" ".join(row))
        return "\n".join(lines)
        
    @staticmethod
    def parse_json(file_bytes: bytes) -> str:
        content = json.loads(file_bytes.decode('utf-8', errors='ignore'))
        return json.dumps(content, indent=2)
        
    @staticmethod
    def parse_markdown(file_bytes: bytes) -> str:
        content = file_bytes.decode('utf-8', errors='ignore')
        html = markdown.markdown(content)
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text()

    @classmethod
    def parse(cls, file_bytes: bytes, filename: str) -> str:
        ext = filename.split(".")[-1].lower()
        if ext == "pdf":
            return cls.parse_pdf(file_bytes)
        elif ext == "docx":
            return cls.parse_docx(file_bytes)
        elif ext in ["txt", "log"]:
            return cls.parse_txt(file_bytes)
        elif ext == "csv":
            return cls.parse_csv(file_bytes)
        elif ext == "json":
            return cls.parse_json(file_bytes)
        elif ext in ["md", "markdown"]:
            return cls.parse_markdown(file_bytes)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
