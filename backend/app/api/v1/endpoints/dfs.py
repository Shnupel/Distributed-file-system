from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id, get_dfs_service
from app.api.middlewares import limiter
from app.db import db_helper
from app.schemas import (
    DirectoryCreate,
    DownloadManifestRead,
    FileDeleteRead,
    FileSystemEntryRead,
    FileUploadRead,
    StorageNodeCreate,
    StorageNodeHeartbeat,
    StorageNodeRead,
)
from app.services import DFSService


router = APIRouter(prefix="/dfs", tags=["dfs"])


@router.post("/nodes", response_model=StorageNodeRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register_storage_node(
    request: Request,
    payload: StorageNodeCreate,
    _: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(db_helper.session_getter),
    service: DFSService = Depends(get_dfs_service),
):
    return await service.register_storage_node(session, payload)


@router.get("/nodes", response_model=list[StorageNodeRead])
async def list_storage_nodes(
    _: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(db_helper.session_getter),
    service: DFSService = Depends(get_dfs_service),
):
    return await service.list_storage_nodes(session)


@router.post("/nodes/{node_id}/heartbeat", response_model=StorageNodeRead)
@limiter.limit("30/minute")
async def heartbeat_storage_node(
    request: Request,
    node_id: int,
    payload: StorageNodeHeartbeat,
    _: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(db_helper.session_getter),
    service: DFSService = Depends(get_dfs_service),
):
    return await service.heartbeat_storage_node(session, node_id, payload)


@router.post(
    "/directories",
    response_model=FileSystemEntryRead,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("30/minute")
async def create_directory(
    request: Request,
    payload: DirectoryCreate,
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(db_helper.session_getter),
    service: DFSService = Depends(get_dfs_service),
):
    return await service.create_directory(
        session=session,
        owner_id=current_user_id,
        name=payload.name,
        parent_id=payload.parent_id,
    )


@router.get("/entries", response_model=list[FileSystemEntryRead])
async def list_entries(
    parent_id: int | None = Query(default=None, ge=1),
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(db_helper.session_getter),
    service: DFSService = Depends(get_dfs_service),
):
    return await service.list_entries(session, current_user_id, parent_id)


@router.post("/files/upload", response_model=FileUploadRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    parent_id: int | None = Form(default=None),
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(db_helper.session_getter),
    service: DFSService = Depends(get_dfs_service),
):
    return await service.upload_file(
        session=session,
        owner_id=current_user_id,
        parent_id=parent_id,
        upload=file,
    )


@router.get("/files/{file_id}/manifest", response_model=DownloadManifestRead)
async def get_download_manifest(
    file_id: int,
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(db_helper.session_getter),
    service: DFSService = Depends(get_dfs_service),
):
    return await service.get_download_manifest(session, current_user_id, file_id)


@router.delete("/files/{file_id}", response_model=FileDeleteRead)
@limiter.limit("20/minute")
async def delete_file(
    request: Request,
    file_id: int,
    current_user_id: int = Depends(get_current_user_id),
    session: AsyncSession = Depends(db_helper.session_getter),
    service: DFSService = Depends(get_dfs_service),
):
    return await service.delete_file(session, current_user_id, file_id)


@router.get("/chunks/{chunk_id}")
@limiter.limit("120/minute")
async def get_chunk(
    request: Request,
    chunk_id: int,
    exp: int = Query(..., ge=1),
    sig: str = Query(..., min_length=64, max_length=64),
    session: AsyncSession = Depends(db_helper.session_getter),
    service: DFSService = Depends(get_dfs_service),
):
    path = await service.resolve_local_chunk_path(session, chunk_id, exp, sig)
    return FileResponse(path=path, media_type="application/octet-stream")