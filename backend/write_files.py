import os

files = {}

files["app/services/document_service.py"] = '''import re
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
                pages.append(f"[第{i+1}页]\\n{text}")
        doc.close()
        return "\\n\\n".join(pages)

    def _parse_docx(self, file_path: str) -> str:
        doc = DocxDoc(file_path)
        paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        return "\\n\\n".join(paras)

    def _parse_txt(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def clean_text(self, text: str) -> str:
        text = re.sub(r"[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f\\x7f]", "", text)
        text = re.sub(r"\\n{3,}", "\\n\\n", text)
        text = re.sub(r"[ \\t]{2,}", " ", text)
        return text.strip()


class TextChunker:

    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\\n\\n", "\\n", "。", "！", "？", "；", "，", " ", ""],
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
'''

files["app/services/embedding_service.py"] = '''from openai import OpenAI
from typing import List
from app.config import settings


class EmbeddingService:

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.EMBEDDING_API_KEY,
            base_url=settings.EMBEDDING_BASE_URL,
        )
        self.model = settings.EMBEDDING_MODEL

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        cleaned = [t.replace("\\n", " ") for t in texts if t.strip()]
        if not cleaned:
            return []
        response = self.client.embeddings.create(
            model=self.model,
            input=cleaned,
        )
        return [item.embedding for item in response.data]

    def embed_query(self, query: str) -> List[float]:
        results = self.embed_texts([query])
        return results[0] if results else []
'''

files["app/services/vector_store_service.py"] = '''import uuid
from typing import List, Optional
import chromadb
from app.config import settings
from app.services.embedding_service import EmbeddingService


class VectorStoreService:

    def __init__(self):
        self.embedding_svc = EmbeddingService()
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: List[dict]) -> int:
        if not chunks:
            return 0
        texts     = [c["content"]  for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        ids       = [str(uuid.uuid4()) for _ in chunks]
        batch_size = 100
        total = 0
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_metas = metadatas[i:i+batch_size]
            batch_ids   = ids[i:i+batch_size]
            embeddings  = self.embedding_svc.embed_texts(batch_texts)
            self.collection.add(
                ids=batch_ids,
                embeddings=embeddings,
                documents=batch_texts,
                metadatas=batch_metas,
            )
            total += len(batch_texts)
        return total

    def search(self, query: str, top_k: int = None, doc_ids: Optional[List[str]] = None) -> List[dict]:
        k = top_k or settings.TOP_K
        query_embedding = self.embedding_svc.embed_query(query)
        where = None
        if doc_ids and len(doc_ids) == 1:
            where = {"doc_id": doc_ids[0]}
        elif doc_ids and len(doc_ids) > 1:
            where = {"doc_id": {"$in": doc_ids}}
        count = self.collection.count()
        if count == 0:
            return []
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, count),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        output = []
        if not results["documents"] or not results["documents"][0]:
            return output
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            output.append({
                "content":  doc,
                "metadata": meta,
                "score":    round(1 - dist, 4),
            })
        return output

    def delete_by_doc_id(self, doc_id: str) -> bool:
        try:
            results = self.collection.get(where={"doc_id": doc_id})
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
            return True
        except Exception:
            return False

    def get_stats(self) -> dict:
        return {
            "total_chunks":    self.collection.count(),
            "collection_name": settings.CHROMA_COLLECTION,
        }
'''

files["app/services/llm_service.py"] = '''from openai import OpenAI
from typing import List, Iterator
from app.config import settings

SYSTEM_PROMPT = """你是一个专业的知识库问答助手。

【核心规则】
1. 只能基于下方提供的【参考资料】回答问题
2. 如果参考资料中没有相关信息，明确回答"根据现有文档，我无法找到相关信息"
3. 禁止编造任何不在参考资料中的内容
4. 回答要结构清晰、语言准确

【回答格式】
- 使用 Markdown 格式
- 关键内容使用**加粗**
- 列举时使用有序或无序列表
- 最后在"📚 参考来源"部分列出引用的文件名
"""


def build_rag_prompt(query: str, contexts: List[dict]) -> str:
    if not contexts:
        context_str = "（未检索到相关文档，请先上传文档）"
    else:
        parts = []
        for i, ctx in enumerate(contexts, 1):
            meta = ctx["metadata"]
            fname = meta.get("original_name", meta.get("filename", "未知文件"))
            chunk_idx = meta.get("chunk_index", "?")
            score = ctx.get("score", 0)
            parts.append(
                f"【资料{i}】来源：{fname}（第{chunk_idx}块，相关度：{score:.2f}）\\n"
                f"{ctx[\'content\']}"
            )
        context_str = "\\n\\n---\\n\\n".join(parts)
    return f"""【参考资料】
{context_str}

【用户问题】
{query}

请基于以上参考资料回答："""


class LLMService:

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.model = settings.LLM_MODEL

    def _build_messages(self, query: str, contexts: List[dict], history: List[dict]) -> List[dict]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in history[-12:]:
            messages.append(msg)
        rag_prompt = build_rag_prompt(query, contexts)
        messages.append({"role": "user", "content": rag_prompt})
        return messages

    def chat(self, query: str, contexts: List[dict], history: List[dict] = None) -> str:
        messages = self._build_messages(query, contexts, history or [])
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
        )
        return response.choices[0].message.content

    def chat_stream(self, query: str, contexts: List[dict], history: List[dict] = None) -> Iterator[str]:
        messages = self._build_messages(query, contexts, history or [])
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
'''

# 写入所有文件
for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    size = os.path.getsize(path)
    print(f"✅ 写入成功: {path} ({size} bytes)")

print("\n🎉 所有文件写入完成！")