import re
from typing import List
import fitz
from docx import Document as DocxDoc
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.config import settings


class DocumentParser:

    def parse(self, file_path: str, file_type: str) -> str:
        dispatch = {
            "pdf":  self._parse_pdf,
            "docx": self._parse_docx,
            "txt":  self._parse_txt,
            "md":   self._parse_txt,
        }
        parser_fn = dispatch.get(file_type.lower())
        if not parser_fn:
            raise ValueError(f"不支持的文件类型: {file_type}")
        return parser_fn(file_path)

    def _parse_pdf(self, file_path: str) -> str:
        doc = fitz.open(file_path)
        pages = []
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()
            if text:
                pages.append(f"[第{i+1}页]\n{text}")
        doc.close()
        return "\n\n".join(pages)

    def _parse_docx(self, file_path: str) -> str:
        doc = DocxDoc(file_path)
        paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paras)

    def _parse_txt(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def clean_text(self, text: str) -> str:
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()


class TextChunker:

    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
            length_function=len,
        )

    def split(self, text: str, metadata: dict) -> List[dict]:
        raw_chunks = self.splitter.split_text(text)
        result = []
        valid_idx = 0
        for chunk in raw_chunks:
            if not chunk.strip():
                continue
            result.append({
                "content": chunk,
                "metadata": {
                    **metadata,
                    "chunk_index": valid_idx,
                    "doc_id":      str(metadata.get("doc_id", "")),
                    "filename":    str(metadata.get("filename", "")),
                },
            })
            valid_idx += 1
        for item in result:
            item["metadata"]["chunk_total"] = valid_idx
        return result
