from __future__ import annotations

from typing import Any

import httpx

from schemas.ml import (
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


class MLServiceError(RuntimeError):
    """Represents a non-success response from the ML backend."""

    def __init__(self, status_code: int, detail: Any) -> None:
        super().__init__(str(detail))
        self.status_code = status_code
        self.detail = detail


class MLServiceClient:
    def __init__(self, base_url: str, timeout_seconds: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = httpx.Timeout(timeout_seconds)

    async def health(self) -> MLHealthResponse:
        payload = await self._request("GET", "/v1/health")
        return MLHealthResponse.model_validate(payload)

    async def ingest_image(self, request: ImageIngestRequest) -> ImageIngestResponse:
        payload = await self._request(
            "PUT", "/v1/images", json=request.model_dump(mode="json")
        )
        return ImageIngestResponse.model_validate(payload)

    async def search_by_image(self, request: SearchRequest) -> SearchResponse:
        payload = await self._request(
            "POST", "/v1/search_by_image", json=request.model_dump(mode="json")
        )
        return SearchResponse.model_validate(payload)

    async def search_by_coordinates(
        self, request: CoordinatesSearchRequest
    ) -> LocationSearchResponse:
        payload = await self._request(
            "POST",
            "/v1/search_by_coordinates",
            json=request.model_dump(mode="json"),
        )
        return LocationSearchResponse.model_validate(payload)

    async def search_by_address(
        self, request: AddressSearchRequest
    ) -> LocationSearchResponse:
        payload = await self._request(
            "POST", "/v1/search_by_address", json=request.model_dump(mode="json")
        )
        return LocationSearchResponse.model_validate(payload)

    async def _request(
        self, method: str, path: str, *, json: dict[str, Any] | None = None
    ) -> Any:
        url = f"{self._base_url}{path}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.request(method, url, json=json)

        if response.status_code >= 400:
            raise MLServiceError(response.status_code, self._extract_detail(response))

        if response.headers.get("content-type", "").startswith("application/json"):
            return response.json()
        return response.text

    @staticmethod
    def _extract_detail(response: httpx.Response) -> Any:
        try:
            data = response.json()
        except ValueError:
            return response.text or "Upstream service error"

        if isinstance(data, dict) and "detail" in data:
            return data["detail"]
        return data


__all__ = ["MLServiceClient", "MLServiceError"]
