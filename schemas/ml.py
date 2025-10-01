from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, PositiveInt, field_validator


class MLHealthResponse(BaseModel):
    status: str = Field(..., description="Upstream service status")


class ImageIngestRequest(BaseModel):
    image_base64: str = Field(..., description="Source image encoded as base64")
    latitude: float | None = Field(default=None, description="Capture latitude")
    longitude: float | None = Field(default=None, description="Capture longitude")
    metadata: dict[str, Any] | None = Field(
        default=None, description="User-provided metadata payload"
    )

    @field_validator("image_base64")
    @classmethod
    def _validate_image(cls, value: str) -> str:
        if not value:
            raise ValueError("image_base64 must not be empty")
        return value


class ImageIngestResponse(BaseModel):
    id: int
    image_uri: str
    local_feature_uri: str
    global_descriptor_uri: str
    latitude: float | None
    longitude: float | None
    address: str | None
    metadata: dict[str, Any] | None
    descriptor_count: int
    descriptor_dim: int
    keypoint_count: int
    global_descriptor_dim: int
    local_feature_type: str
    global_descriptor_type: str
    matcher_type: str
    created_at: datetime
    updated_at: datetime


class ImageDetailsResponse(ImageIngestResponse):
    image_base64: str


class SearchRequest(BaseModel):
    image_base64: str = Field(..., description="Query image encoded as base64")
    plot_dots: bool = Field(
        default=False, description="Whether to annotate keypoints on images"
    )
    top_k: PositiveInt = Field(default=5, description="Number of matches to return")

    @field_validator("image_base64")
    @classmethod
    def _validate_query_image(cls, value: str) -> str:
        if not value:
            raise ValueError("image_base64 must not be empty")
        return value

    @field_validator("top_k")
    @classmethod
    def _validate_top_k(cls, value: int) -> int:
        if value > 50:
            raise ValueError("top_k must not exceed 50")
        return value


class SearchMatch(BaseModel):
    image_id: int
    confidence: float
    global_similarity: float
    local_matches: int
    local_match_ratio: float
    local_mean_score: float
    geometry_inliers: int
    geometry_inlier_ratio: float
    geometry_score: float
    image_uri: str
    feature_uri: str
    latitude: float | None
    longitude: float | None
    address: str | None
    metadata: dict[str, Any] | None
    image_base64: str


class SearchResponse(BaseModel):
    query_image_base64: str
    matches: list[SearchMatch]


class CoordinatesSearchRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude to search")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude to search")
    plot_dots: bool = Field(
        default=False, description="Whether to annotate keypoints on images"
    )
    top_k: PositiveInt = Field(default=5, description="Number of matches to return")

    @field_validator("top_k")
    @classmethod
    def _validate_top_k(cls, value: int) -> int:
        if value > 50:
            raise ValueError("top_k must not exceed 50")
        return value


class AddressSearchRequest(BaseModel):
    address: str = Field(..., min_length=3, description="Human readable address")
    plot_dots: bool = Field(
        default=False, description="Whether to annotate keypoints on images"
    )
    top_k: PositiveInt = Field(default=5, description="Number of matches to return")

    @field_validator("address")
    @classmethod
    def _validate_address(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("address must not be blank")
        return value

    @field_validator("top_k")
    @classmethod
    def _validate_top_k(cls, value: int) -> int:
        if value > 50:
            raise ValueError("top_k must not exceed 50")
        return value


class LocationSearchMatch(BaseModel):
    image_id: int
    distance_meters: float = Field(..., ge=0)
    image_uri: str
    feature_uri: str
    latitude: float | None
    longitude: float | None
    address: str | None
    metadata: dict[str, Any] | None
    image_base64: str


class LocationSearchResponse(BaseModel):
    matches: list[LocationSearchMatch]


class ImageSummaryResponse(BaseModel):
    total_images: int = Field(..., ge=0)
    latest_image_id: int | None = None
    latest_created_at: datetime | None = None


__all__ = [
    "AddressSearchRequest",
    "CoordinatesSearchRequest",
    "ImageDetailsResponse",
    "ImageIngestRequest",
    "ImageIngestResponse",
    "ImageSummaryResponse",
    "LocationSearchMatch",
    "LocationSearchResponse",
    "MLHealthResponse",
    "SearchMatch",
    "SearchRequest",
    "SearchResponse",
]
