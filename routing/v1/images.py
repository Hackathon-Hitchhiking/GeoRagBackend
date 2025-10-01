from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query, status

from dependencies import get_current_user, get_image_record_service
from models.user import User
from schemas import ImageRecordCreate, ImageRecordRead, ImageRecordUpdate
from services.image_record import ImageRecordService


router = APIRouter()


@router.get("/", response_model=List[ImageRecordRead])
async def list_images(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    image_hash: str | None = None,
    matcher_type: str | None = None,
    local_feature_type: str | None = None,
    presign: bool = False,
    expires_in: int = Query(900, ge=60, le=3600),
    image_service: ImageRecordService = Depends(get_image_record_service),
) -> List[ImageRecordRead]:
    records = await image_service.list_records(
        limit,
        offset,
        image_hash=image_hash,
        matcher_type=matcher_type,
        local_feature_type=local_feature_type,
    )
    return [
        image_service.to_read_model(
            record, include_signed_urls=presign, expires_in=expires_in
        )
        for record in records
    ]

@router.get("/{image_id}", response_model=ImageRecordRead)
async def get_image(
    image_id: int,
    presign: bool = False,
    expires_in: int = Query(900, ge=60, le=3600),
    image_service: ImageRecordService = Depends(get_image_record_service),
) -> ImageRecordRead:
    record = await image_service.get_record(image_id)
    return image_service.to_read_model(
        record, include_signed_urls=presign, expires_in=expires_in
    )

