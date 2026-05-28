import os
import uuid
import asyncio
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db, DocumentModel
from app.models.schemas import DocumentResponse, StatsResponse
from app.services.document_service import DocumentParser, TextChunker
from app.services.vector_store_service import VectorStoreService
from app.config import settings

router  = APIRouter(prefix="/api/documents", tags=["文档管理"])
parser  = DocumentParser()
chunker = TextChunker()


@router.post("/upload", response_model=DocumentResponse, summary="上传文档")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持 .{ext}，支持：{settings.ALLOWED_EXTENSIONS}"
        )

    doc_id    = str(uuid.uuid4())
    save_name = f"{doc_id}.{ext}"
    save_path = os.path.join(settings.UPLOAD_DIR, save_name)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    doc = DocumentModel(
        id=doc_id,
        filename=save_name,
        original_name=file.filename,
        file_type=ext,
        file_size=len(content),
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    asyncio.create_task(
        _process_document(doc_id, save_path, ext, file.filename)
    )

    return doc


async def _process_document(
    doc_id: str, file_path: str,
    file_type: str, original_name: str
):
    db = next(get_db())
    try:
        raw_text     = parser.parse(file_path, file_type)
        cleaned_text = parser.clean_text(raw_text)

        chunks = chunker.split(cleaned_text, {
            "doc_id":        doc_id,
            "filename":      f"{doc_id}.{file_type}",
            "original_name": original_name,
            "file_type":     file_type,
        })

        vs    = VectorStoreService()
        count = vs.add_chunks(chunks)

        doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
        if doc:
            doc.status      = "ready"
            doc.chunk_count = count
            db.commit()

    except Exception as e:
        doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
        if doc:
            doc.status    = "error"
            doc.error_msg = str(e)
            db.commit()
    finally:
        db.close()


@router.get("/stats/overview", response_model=StatsResponse, summary="统计")
def get_stats(db: Session = Depends(get_db)):
    doc_count = db.query(DocumentModel).filter(
        DocumentModel.status == "ready"
    ).count()
    vs    = VectorStoreService()
    stats = vs.get_stats()
    return StatsResponse(
        document_count=doc_count,
        total_chunks=stats["total_chunks"],
        collection_name=stats["collection_name"],
    )


@router.get("/", response_model=List[DocumentResponse], summary="文档列表")
def list_documents(db: Session = Depends(get_db)):
    return db.query(DocumentModel).order_by(
        DocumentModel.created_at.desc()
    ).all()


@router.delete("/{doc_id}", summary="删除文档")
def delete_document(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    vs = VectorStoreService()
    vs.delete_by_doc_id(doc_id)

    file_path = os.path.join(settings.UPLOAD_DIR, doc.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(doc)
    db.commit()
    return {"message": "删除成功", "doc_id": doc_id}