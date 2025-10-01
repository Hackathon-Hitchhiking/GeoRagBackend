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

@router.put(
    "/images",
    response_model=list[ImageIngestResponse],
    status_code=status.HTTP_201_CREATED,
)
async def ingest_image(
    payload: list[ImageIngestRequest],
    _: User = Depends(get_current_user),
    ml_client: MLServiceClient = Depends(get_ml_service_client),
) -> list[ImageIngestResponse]:
    responses: list[ImageIngestResponse] = []
    for idx, request_item in enumerate(payload, start=1):
        responses.append(
            await _execute(
                lambda req=request_item: ml_client.ingest_image(req),
                error_message=f"Unable to ingest image #{idx}",
            )
        )
    return responses


@router.post(
    "/search_by_image",
    response_model=list[SearchResponse],
)
async def search_by_image(
    payload: list[SearchRequest],
    _: User = Depends(get_current_user),
    ml_client: MLServiceClient = Depends(get_ml_service_client),
) -> list[SearchResponse]:
    responses: list[SearchResponse] = []
    for idx, request_item in enumerate(payload, start=1):
        responses.append(
            await _execute(
                lambda req=request_item: ml_client.search_by_image(req),
                error_message=f"Unable to search by image #{idx}",
            )
        )
    return responses


@router.post(
    "/search_by_coordinates",
    response_model=list[LocationSearchResponse],
)
async def search_by_coordinates(
    payload: list[CoordinatesSearchRequest],
    _: User = Depends(get_current_user),
    ml_client: MLServiceClient = Depends(get_ml_service_client),
) -> list[LocationSearchResponse]:
    responses: list[LocationSearchResponse] = []
    for idx, request_item in enumerate(payload, start=1):
        responses.append(
            await _execute(
                lambda req=request_item: ml_client.search_by_coordinates(req),
                error_message=f"Unable to search by coordinates #{idx}",
            )
        )
    return responses


@router.post(
    "/search_by_address",
    response_model=list[LocationSearchResponse],
)
async def search_by_address(
    payload: list[AddressSearchRequest],
    _: User = Depends(get_current_user),
    ml_client: MLServiceClient = Depends(get_ml_service_client),
) -> list[LocationSearchResponse]:
    responses: list[LocationSearchResponse] = []
    for idx, request_item in enumerate(payload, start=1):
        responses.append(
            await _execute(
                lambda req=request_item: ml_client.search_by_address(req),
                error_message=f"Unable to search by address #{idx}",
            )
        )
    return responses
