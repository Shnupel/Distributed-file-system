from datetime import datetime

from pydantic import BaseModel, Field


class StorageHealthResponse(BaseModel):
    status: str = "ok"
    node_name: str
    total_space: int | None = Field(default=None, ge=0)
    free_space: int | None = Field(default=None, ge=0)
    timestamp: datetime


class ChunkUploadResponse(BaseModel):
    chunk_id: int
    size: int = Field(..., ge=0)
    sha256: str = Field(..., min_length=64, max_length=64)
    stored: bool = True
