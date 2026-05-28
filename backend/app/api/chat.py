import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest, ChatResponse, SourceItem
from app.services.vector_store_service import VectorStoreService
from app.services.llm_service import LLMService
from app.config import settings

router  = APIRouter(prefix="/api/chat", tags=["问答"])
llm_svc = LLMService()


@router.post("/", response_model=ChatResponse, summary="普通问答")
def chat(req: ChatRequest):
    vs       = VectorStoreService()
    contexts = vs.search(req.query, doc_ids=req.doc_ids)
    answer   = llm_svc.chat(req.query, contexts, req.history)
    sources  = [
        SourceItem(content=c["content"], metadata=c["metadata"], score=c["score"])
        for c in contexts
    ]
    return ChatResponse(answer=answer, sources=sources, model=settings.LLM_MODEL)


@router.post("/stream", summary="流式问答")
async def chat_stream(req: ChatRequest):
    vs       = VectorStoreService()
    contexts = vs.search(req.query, doc_ids=req.doc_ids)

    sources_data = [
        {"content": c["content"], "metadata": c["metadata"], "score": c["score"]}
        for c in contexts
    ]

    def generate():
        yield f"data: {json.dumps({'type': 'sources', 'data': sources_data}, ensure_ascii=False)}\n\n"

        for token in llm_svc.chat_stream(req.query, contexts, req.history):
            yield f"data: {json.dumps({'type': 'token', 'data': token}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )