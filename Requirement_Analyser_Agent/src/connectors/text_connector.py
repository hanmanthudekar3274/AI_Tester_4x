import io
import docx
import pypdf


class TextConnector:
    """Converts uploaded files or pasted text into a plain-text block."""

    def from_paste(self, text: str) -> str:
        return f"=== PASTED TEXT ===\n{text.strip()}"

    def from_file(self, file_bytes: bytes, filename: str) -> str:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext in ("txt", "md"):
            return f"=== FILE: {filename} ===\n{file_bytes.decode('utf-8', errors='replace').strip()}"
        if ext == "pdf":
            return self._read_pdf(file_bytes, filename)
        if ext == "docx":
            return self._read_docx(file_bytes, filename)
        return f"=== FILE: {filename} ===\n(unsupported format — paste content manually)"

    # ------------------------------------------------------------------

    def _read_pdf(self, file_bytes: bytes, filename: str) -> str:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return f"=== FILE: {filename} ===\n" + "\n".join(pages).strip()

    def _read_docx(self, file_bytes: bytes, filename: str) -> str:
        doc = docx.Document(io.BytesIO(file_bytes))
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return f"=== FILE: {filename} ===\n{text.strip()}"
