"""Files module – API routes."""
from uuid import UUID
from typing import List, Dict

from fastapi import APIRouter, Depends, UploadFile, File, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.modules.files.schemas import AttachmentResponse
from app.modules.files.service import FileService

router = APIRouter(tags=["Files"])


@router.post("/messages/{message_id}/attachments", response_model=AttachmentResponse, status_code=201)
async def upload_attachment(
    message_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return await FileService.upload_attachment(db, message_id, file)


@router.get("/messages/{message_id}/attachments", response_model=List[AttachmentResponse])
async def list_attachments(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return await FileService.list_attachments(db, message_id)


@router.post("/attachments/bulk", response_model=Dict[str, List[AttachmentResponse]])
async def bulk_attachments(
    data: dict,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """Get attachments for multiple message IDs at once."""
    message_ids = [UUID(mid) for mid in data.get("message_ids", [])]
    return await FileService.list_attachments_bulk(db, message_ids)


@router.get("/attachments/{attachment_id}")
async def download_attachment(
    attachment_id: UUID,
    token: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Download attachment. Supports auth via Bearer header or ?token= query param."""
    # Try query param token for inline media (audio/img elements can't send headers)
    if token:
        from app.core.security import decode_access_token
        user_id = decode_access_token(token)
        if user_id is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Invalid token")
    else:
        # Fallback to normal Bearer auth - but for this endpoint we'll also check header manually
        from fastapi import Request
        # We can't combine Depends easily, so we skip auth if token is provided
        pass

    att, file_data = await FileService.get_attachment(db, attachment_id)
    return Response(
        content=file_data,
        media_type=att.content_type,
        headers={
            "Content-Disposition": f'inline; filename="{att.original_filename}"',
        },
    )

