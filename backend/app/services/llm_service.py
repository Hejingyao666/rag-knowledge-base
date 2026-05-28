from openai import OpenAI
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
                f"【资料{i}】来源：{fname}（第{chunk_idx}块，相关度：{score:.2f}）\n"
                f"{ctx['content']}"
            )
        context_str = "\n\n---\n\n".join(parts)
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
