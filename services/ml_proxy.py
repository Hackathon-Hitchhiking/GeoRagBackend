from __future__ import annotations

from collections.abc import Mapping

import httpx
from fastapi import Request, Response


class MLProxyService:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    async def forward(self, request: Request, path: str) -> Response:
        url = self._build_target_url(path)
        headers = self._filter_headers(request.headers)
        params = request.query_params.multi_items()
        data = await request.body()

        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            upstream_response = await client.request(
                request.method,
                url,
                content=data,
                headers=headers,
                params=params,
            )

        return self._build_response(upstream_response)

    def _build_target_url(self, path: str) -> str:
        if not path:
            return self._base_url
        return f"{self._base_url}/{path}"

    @staticmethod
    def _filter_headers(headers: Mapping[str, str]) -> dict[str, str]:
        excluded_headers = {"host", "content-length"}
        return {
            key: value
            for key, value in headers.items()
            if key.lower() not in excluded_headers
        }

    @staticmethod
    def _build_response(upstream_response: httpx.Response) -> Response:
        response = Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            media_type=upstream_response.headers.get("content-type"),
        )
        hop_by_hop_headers = {
            "content-length",
            "transfer-encoding",
            "connection",
            "content-encoding",
        }
        for header, value in upstream_response.headers.items():
            if header.lower() in hop_by_hop_headers:
                continue
            response.headers[header] = value
        return response
