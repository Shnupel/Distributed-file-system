from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StorageNodeCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=128)
    base_url: str | None = Field(default=None, max_length=512)
    total_space: int | None = Field(default=None, ge=0)
    free_space: int | None = Field(default=None, ge=0)


class StorageNodeHeartbeat(BaseModel):
    total_space: int | None = Field(default=None, ge=0)
    free_space: int | None = Field(default=None, ge=0)


class StorageNodeRead(BaseModel):
    id: int
    name: str
    base_url: str | None
    is_active: bool
    is_local: bool
    total_space: int | None
    free_space: int | None
    last_heartbeat: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StorageNodeResolvedRead(StorageNodeRead):
    already_exists: bool = False


class DirectoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: int | None = Field(default=None, ge=1)


class FileSystemEntryRead(BaseModel):
    id: int
    owner_id: int
    parent_id: int | None
    name: str
    is_dir: bool
    size: int
    mime_type: str | None
    file_sha256: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FileUploadRead(BaseModel):
    file_id: int
    file_name: str
    size: int
    chunks_count: int
    file_sha256: str
    status: str


class FileDeleteRead(BaseModel):
    file_id: int
    deleted: bool = True


class ChunkReplicaURLRead(BaseModel):
    node_id: int
    node_name: str
    url: str


class ChunkManifestRead(BaseModel):
    chunk_id: int
    index: int
    size: int
    sha256: str
    replicas: list[ChunkReplicaURLRead]


class DownloadManifestRead(BaseModel):
    file_id: int
    file_name: str
    size: int
    file_sha256: str
    expires_at_unix: int
    chunks: list[ChunkManifestRead]
