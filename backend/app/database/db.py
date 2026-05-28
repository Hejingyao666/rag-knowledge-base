from sqlalchemy import (
    create_engine, Column, String,
    Integer, DateTime, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class DocumentModel(Base):
    __tablename__ = "documents"

    id            = Column(String,  primary_key=True, index=True)
    filename      = Column(String,  nullable=False)
    original_name = Column(String,  nullable=False)
    file_type     = Column(String,  nullable=False)
    file_size     = Column(Integer, nullable=False)
    chunk_count   = Column(Integer, default=0)
    status        = Column(String,  default="processing")
    error_msg     = Column(Text,    nullable=True)
    created_at    = Column(DateTime, default=datetime.now)
    updated_at    = Column(DateTime, default=datetime.now, onupdate=datetime.now)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()