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
    response_model=ImageIngestResponse | list[ImageIngestResponse],
    status_code=status.HTTP_201_CREATED,
)
async def ingest_image(
    payload: ImageIngestRequest | list[ImageIngestRequest],
    _: User = Depends(get_current_user),
    ml_client: MLServiceClient = Depends(get_ml_service_client),
) -> ImageIngestResponse | list[ImageIngestResponse]:
    requests = payload if isinstance(payload, list) else [payload]
    responses: list[ImageIngestResponse] = []
    for idx, request_item in enumerate(requests, start=1):
        responses.append(
            await _execute(
                lambda req=request_item: ml_client.ingest_image(req),
                error_message=f"Unable to ingest image #{idx}",
            )
        )
    return responses if isinstance(payload, list) else responses[0]


@router.post(
    "/search_by_image",
    response_model=SearchResponse | list[SearchResponse],
)
async def search_by_image(
    payload: SearchRequest | list[SearchRequest],
    _: User = Depends(get_current_user),
    ml_client: MLServiceClient = Depends(get_ml_service_client),
) -> SearchResponse | list[SearchResponse]:
    requests = payload if isinstance(payload, list) else [payload]
    responses: list[SearchResponse] = []
    for idx, request_item in enumerate(requests, start=1):
        responses.append(
            await _execute(
                lambda req=request_item: ml_client.search_by_image(req),
                error_message=f"Unable to search by image #{idx}",
            )
        )
    return responses if isinstance(payload, list) else responses[0]


@router.post(
    "/search_by_coordinates",
    response_model=LocationSearchResponse | list[LocationSearchResponse],
)
async def search_by_coordinates(
    payload: CoordinatesSearchRequest | list[CoordinatesSearchRequest],
    _: User = Depends(get_current_user),
    ml_client: MLServiceClient = Depends(get_ml_service_client),
) -> LocationSearchResponse | list[LocationSearchResponse]:
    requests = payload if isinstance(payload, list) else [payload]
    responses: list[LocationSearchResponse] = []
    for idx, request_item in enumerate(requests, start=1):
        responses.append(
            await _execute(
                lambda req=request_item: ml_client.search_by_coordinates(req),
                error_message=f"Unable to search by coordinates #{idx}",
            )
        )
    return responses if isinstance(payload, list) else responses[0]


@router.post(
    "/search_by_address",
    response_model=LocationSearchResponse | list[LocationSearchResponse],
)
async def search_by_address(
    payload: AddressSearchRequest | list[AddressSearchRequest],
    _: User = Depends(get_current_user),
    ml_client: MLServiceClient = Depends(get_ml_service_client),
) -> LocationSearchResponse | list[LocationSearchResponse]:
    requests = payload if isinstance(payload, list) else [payload]
    responses: list[LocationSearchResponse] = []
    for idx, request_item in enumerate(requests, start=1):
        responses.append(
            await _execute(
                lambda req=request_item: ml_client.search_by_address(req),
                error_message=f"Unable to search by address #{idx}",
            )
        )
    return responses if isinstance(payload, list) else responses[0]
