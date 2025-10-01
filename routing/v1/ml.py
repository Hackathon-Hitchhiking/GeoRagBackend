from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import get_current_user, get_ml_service_client
from models.user import User
from schemas import (
    AddressSearchRequest,
    CoordinatesSearchRequest,
    ImageDetailsResponse,
    ImageIngestRequest,
    ImageIngestResponse,
    ImageSummaryResponse,
    LocationSearchResponse,
    MLHealthResponse,
    SearchRequest,
    SearchResponse,
)
from services.ml_client import MLServiceClient, MLServiceError


T = TypeVar("T")


router = APIRouter()


async def _execute(callable_: Callable[[], Awaitable[T]], *, error_message: str) -> T:
    try:
        return await callable_()
    except MLServiceError as exc:
        detail = exc.detail or error_message
        raise HTTPException(status_code=exc.status_code, detail=detail) from exc


@router.get("/health", response_model=MLHealthResponse)
async def healthcheck(
    _: User = Depends(get_current_user),
    ml_client: MLServiceClient = Depends(get_ml_service_client),
) -> MLHealthResponse:
    return await _execute(ml_client.health, error_message="Unable to reach ML service")


@router.get("/images/summary", response_model=ImageSummaryResponse)
async def get_images_summary(
    _: User = Depends(get_current_user),
    ml_client: MLServiceClient = Depends(get_ml_service_client),
) -> ImageSummaryResponse:
    return await _execute(
        ml_client.get_summary,
        error_message="Unable to fetch ML summary",
    )


@router.get("/images/{image_id}", response_model=ImageDetailsResponse)
async def get_image_details(
    image_id: int,
    _: User = Depends(get_current_user),
    ml_client: MLServiceClient = Depends(get_ml_service_client),
) -> ImageDetailsResponse:
    return await _execute(
        lambda: ml_client.get_image(image_id),
        error_message="Unable to fetch image details",
    )


@router.put(
    "/images",
    response_model=ImageIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_image(
    payload: ImageIngestRequest,
    _: User = Depends(get_current_user),
    ml_client: MLServiceClient = Depends(get_ml_service_client),
) -> ImageIngestResponse:
    return await _execute(
        lambda: ml_client.ingest_image(payload),
        error_message="Unable to ingest image",
    )


@router.post("/search_by_image", response_model=SearchResponse)
async def search_by_image(
    payload: SearchRequest,
    _: User = Depends(get_current_user),
    ml_client: MLServiceClient = Depends(get_ml_service_client),
) -> SearchResponse:
    return await _execute(
        lambda: ml_client.search_by_image(payload),
        error_message="Unable to search by image",
    )


@router.post(
    "/search_by_coordinates", response_model=LocationSearchResponse
)
async def search_by_coordinates(
    payload: CoordinatesSearchRequest,
    _: User = Depends(get_current_user),
    ml_client: MLServiceClient = Depends(get_ml_service_client),
) -> LocationSearchResponse:
    return await _execute(
        lambda: ml_client.search_by_coordinates(payload),
        error_message="Unable to search by coordinates",
    )


@router.post("/search_by_address", response_model=LocationSearchResponse)
async def search_by_address(
    payload: AddressSearchRequest,
    _: User = Depends(get_current_user),
    ml_client: MLServiceClient = Depends(get_ml_service_client),
) -> LocationSearchResponse:
    return await _execute(
        lambda: ml_client.search_by_address(payload),
        error_message="Unable to search by address",
    )
