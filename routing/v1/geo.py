"""Geo estimation pipeline for bbox detections.

This module exposes FastAPI endpoints that estimate a geographic point from an
image-space bounding box and enrich the result with reverse geocoding and
panorama lookups.

References:
    - Google Street View Static API parameters (heading, fov, pitch, radius)
      and metadata endpoint. [Google for Developers][6]
    - Street View POV heading/pitch semantics. [Google for Developers][1]
    - Nominatim Reverse API usage and nearest-object behavior. [Nominatim][2]
    - Mapillary API v4 search for nearby imagery. [mapillary.com][5]
"""
from __future__ import annotations

import asyncio
import json
import math
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, HttpUrl, ValidationError, root_validator


EARTH_SEMI_MAJOR_AXIS_M = 6_378_137.0
EARTH_FLATTENING = 1 / 298.257_223_563
EARTH_SEMI_MINOR_AXIS_M = EARTH_SEMI_MAJOR_AXIS_M * (1 - EARTH_FLATTENING)
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
MAPILLARY_TOKEN = os.getenv("MAPILLARY_TOKEN")
NOMINATIM_EMAIL = os.getenv("NOMINATIM_EMAIL")
HTTP_TIMEOUT = httpx.Timeout(2.5, read=2.5, connect=2.5)
MAX_HTTP_RETRIES = 2
HTTP_BACKOFF_SECONDS = 0.5
DEFAULT_ASSUMED_DISTANCE_M = 20.0
DEFAULT_SEARCH_RADIUS_M = 50.0
SUPPORTED_PROVIDERS = {"google", "mapillary"}


def normalize_angle_deg(angle: float) -> float:
    """Normalize angle to [0, 360)."""

    return angle % 360.0


def wrap_delta_deg(delta: float) -> float:
    """Wrap angle delta to [-180, 180)."""

    wrapped = (delta + 180.0) % 360.0 - 180.0
    if wrapped == -180.0:
        return 180.0
    return wrapped


@dataclass
class RateLimiter:
    """Simple in-memory token bucket limiter for outbound requests."""

    rate: float  # tokens per second
    capacity: float

    def __post_init__(self) -> None:
        self._tokens: Dict[str, float] = {}
        self._timestamps: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def acquire(self, key: str, tokens: float = 1.0) -> None:
        """Acquire tokens for a given key, waiting if necessary."""

        if tokens > self.capacity:
            raise ValueError("tokens requested exceed bucket capacity")

        while True:
            async with self._lock:
                now = time.monotonic()
                last = self._timestamps.get(key, now)
                available = self._tokens.get(key, self.capacity)
                available = min(
                    self.capacity,
                    available + (now - last) * self.rate,
                )
                if available >= tokens:
                    self._tokens[key] = available - tokens
                    self._timestamps[key] = now
                    return
                wait_for = (tokens - available) / self.rate if self.rate else 1.0
                self._tokens[key] = available
                self._timestamps[key] = now
            await asyncio.sleep(wait_for)


rate_limiter = RateLimiter(rate=5.0, capacity=5.0)
_http_client: Optional[httpx.AsyncClient] = None
_client_lock = asyncio.Lock()


async def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        async with _client_lock:
            if _http_client is None:
                _http_client = httpx.AsyncClient(timeout=HTTP_TIMEOUT)
    return _http_client


async def http_get(
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    rate_key: str,
) -> httpx.Response:
    """Perform an HTTP GET with retries, timeout, and rate limiting."""

    last_exc: Optional[Exception] = None
    for attempt in range(MAX_HTTP_RETRIES + 1):
        await rate_limiter.acquire(rate_key)
        try:
            client = await get_http_client()
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response
        except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError) as exc:
            last_exc = exc
            if attempt >= MAX_HTTP_RETRIES:
                break
            await asyncio.sleep(HTTP_BACKOFF_SECONDS * (2**attempt))
    if last_exc:
        raise last_exc
    raise RuntimeError("HTTP GET failed without exception")


class BoundingBox(BaseModel):
    x: float
    y: float
    w: float
    h: float

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h


class GeoEstimateRequest(BaseModel):
    image_width: int = Field(..., gt=0)
    image_height: int = Field(..., gt=0)
    hfov_deg: Optional[float] = Field(None, gt=0.0, lt=360.0)
    camera_lat: float
    camera_lon: float
    camera_heading_deg: float
    bbox: BoundingBox
    fx: Optional[float] = Field(None, gt=0.0)
    fy: Optional[float] = Field(None, gt=0.0)
    cx: Optional[float]
    cy: Optional[float]
    assumed_distance_m: Optional[float] = Field(None, gt=0.0)
    provider_priority: List[str] = Field(default_factory=lambda: ["google", "mapillary"])
    radius_m: Optional[float] = Field(DEFAULT_SEARCH_RADIUS_M, gt=0.0)

    @root_validator
    def validate_fov_or_intrinsics(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        hfov, fx, cx = values.get("hfov_deg"), values.get("fx"), values.get("cx")
        if hfov is None and (fx is None or cx is None):
            raise ValueError("Either hfov_deg or both fx and cx must be provided")
        providers = values.get("provider_priority") or []
        normalized = []
        for provider in providers:
            p = provider.lower()
            if p in SUPPORTED_PROVIDERS and p not in normalized:
                normalized.append(p)
        values["provider_priority"] = normalized
        return values


class EstimatedPoint(BaseModel):
    lat: float
    lon: float
    bearing_deg: float


class AddressInfo(BaseModel):
    display_name: Optional[str]
    components: Dict[str, Any] = Field(default_factory=dict)


class PanoramaInfo(BaseModel):
    provider: Optional[str]
    meta: Dict[str, Any] = Field(default_factory=dict)
    thumbnail_url: Optional[HttpUrl]


class DebugInfo(BaseModel):
    method: str
    delta_yaw_deg: float
    assumed_distance_m: float
    notes: List[str] = Field(default_factory=list)


class GeoEstimateResponse(BaseModel):
    estimated_point: EstimatedPoint
    address: AddressInfo
    panorama: PanoramaInfo
    debug: DebugInfo


class BearingResponse(BaseModel):
    bearing_deg: float


def bbox_center(bbox: BoundingBox) -> Tuple[float, float]:
    """Return the (u, v) center of a bounding box."""

    u = bbox.x + bbox.w / 2.0
    v = bbox.y + bbox.h / 2.0
    return u, v


def bearing_from_bbox(
    u: float,
    image_width: int,
    hfov_deg: Optional[float],
    camera_heading_deg: float,
    *,
    cx: Optional[float] = None,
    fx: Optional[float] = None,
) -> float:
    """Compute absolute bearing using intrinsics or HFOV heuristics.

    Args:
        u: Horizontal pixel coordinate of the target.
        image_width: Image width in pixels.
        hfov_deg: Horizontal field of view in degrees when intrinsics are
            unavailable.
        camera_heading_deg: Compass heading of the camera (yaw).
        cx: Optional principal point offset in pixels.
        fx: Optional focal length in pixels.

    Returns:
        Absolute bearing in degrees (0-360).
    """

    if fx is not None and cx is not None:
        # Pinhole model yaw from pixel column. No undistortion applied.
        delta_yaw_rad = math.atan2(u - cx, fx)
        delta_yaw_deg = math.degrees(delta_yaw_rad)
    elif hfov_deg is not None:
        center = image_width / 2.0
        degrees_per_pixel = hfov_deg / image_width
        delta_yaw_deg = (u - center) * degrees_per_pixel
    else:
        raise ValueError("Either fx/cx or hfov_deg must be provided")

    absolute_bearing = normalize_angle_deg(camera_heading_deg + delta_yaw_deg)
    return absolute_bearing


def project_point_geodesic(
    lat: float,
    lon: float,
    bearing_deg: float,
    distance_m: float,
) -> Tuple[float, float]:
    """Project a WGS84 point along a geodesic.

    Implements Vincenty's direct method for the WGS84 ellipsoid using only the
    standard library. Suitable for short to medium distances.
    """

    if distance_m == 0:
        return lat, lon

    a = EARTH_SEMI_MAJOR_AXIS_M
    b = EARTH_SEMI_MINOR_AXIS_M
    f = EARTH_FLATTENING

    alpha1 = math.radians(bearing_deg)
    sin_alpha1 = math.sin(alpha1)
    cos_alpha1 = math.cos(alpha1)

    phi1 = math.radians(lat)
    tan_u1 = (1 - f) * math.tan(phi1)
    cos_u1 = 1.0 / math.sqrt(1 + tan_u1 * tan_u1)
    sin_u1 = tan_u1 * cos_u1

    sigma1 = math.atan2(tan_u1, cos_alpha1)
    sin_alpha = cos_u1 * sin_alpha1
    cos_sq_alpha = 1 - sin_alpha * sin_alpha
    u_sq = cos_sq_alpha * (a * a - b * b) / (b * b)
    A = 1 + u_sq / 16.0 * (4096.0 + u_sq * (-768.0 + u_sq * (320.0 - 175.0 * u_sq)))
    B = u_sq / 1024.0 * (256.0 + u_sq * (-128.0 + u_sq * (74.0 - 47.0 * u_sq)))

    sigma = distance_m / (b * A)
    sigma_prev = math.inf
    while abs(sigma - sigma_prev) > 1e-12:
        cos2_sigma_m = math.cos(2.0 * sigma1 + sigma)
        sin_sigma = math.sin(sigma)
        cos_sigma = math.cos(sigma)
        delta_sigma = B * sin_sigma * (
            cos2_sigma_m
            + B
            / 4.0
            * (
                cos_sigma * (-1 + 2 * cos2_sigma_m * cos2_sigma_m)
                - B
                / 6.0
                * cos2_sigma_m
                * (-3 + 4 * sin_sigma * sin_sigma)
                * (-3 + 4 * cos2_sigma_m * cos2_sigma_m)
            )
        )
        sigma_prev = sigma
        sigma = distance_m / (b * A) + delta_sigma

    tmp = sin_u1 * sin_sigma - cos_u1 * cos_sigma * cos_alpha1
    phi2 = math.atan2(
        sin_u1 * cos_sigma + cos_u1 * sin_sigma * cos_alpha1,
        (1 - f) * math.sqrt(sin_alpha * sin_alpha + tmp * tmp),
    )
    lamb = math.atan2(
        sin_sigma * sin_alpha1,
        cos_u1 * cos_sigma - sin_u1 * sin_sigma * cos_alpha1,
    )
    C = f / 16.0 * cos_sq_alpha * (4.0 + f * (4.0 - 3.0 * cos_sq_alpha))
    L = lamb - (1 - C) * f * sin_alpha * (
        sigma
        + C
        * sin_sigma
        * (
            cos2_sigma_m
            + C
            * cos_sigma
            * (-1 + 2 * cos2_sigma_m * cos2_sigma_m)
        )
    )

    lon2 = math.degrees(math.radians(lon) + L)
    lat2 = math.degrees(phi2)

    lon2 = ((lon2 + 180.0) % 360.0) - 180.0
    return lat2, lon2


async def reverse_geocode(lat: float, lon: float) -> AddressInfo:
    """Call Nominatim reverse geocoding (nearest feature, not guaranteed exact)."""

    headers = {
        "User-Agent": "GeoRagBackend/1.0 (contact: {})".format(NOMINATIM_EMAIL or "n/a"),
    }
    params = {
        "format": "jsonv2",
        "lat": lat,
        "lon": lon,
        "zoom": 18,
        "addressdetails": 1,
    }
    if NOMINATIM_EMAIL:
        params["email"] = NOMINATIM_EMAIL
    try:
        response = await http_get(
            "https://nominatim.openstreetmap.org/reverse",
            params=params,
            headers=headers,
            rate_key="nominatim",
        )
    except Exception as exc:  # noqa: BLE001
        return AddressInfo(display_name=None, components={"error": str(exc)})

    payload = response.json()
    address = payload.get("address") or {}
    display_name = payload.get("display_name")
    return AddressInfo(display_name=display_name, components=address)


async def street_view_metadata(lat: float, lon: float, radius_m: float) -> Optional[Dict[str, Any]]:
    """Query Street View metadata for a nearby panorama."""

    if not GOOGLE_MAPS_API_KEY:
        return None
    params = {
        "location": f"{lat},{lon}",
        "radius": radius_m,
        "key": GOOGLE_MAPS_API_KEY,
    }
    try:
        response = await http_get(
            "https://maps.googleapis.com/maps/api/streetview/metadata",
            params=params,
            headers=None,
            rate_key="google",
        )
    except Exception:
        return None
    data = response.json()
    if data.get("status") != "OK":
        return None
    return data


def street_view_thumbnail(
    pano_or_latlon: Dict[str, Any],
    heading_deg: float,
    *,
    pitch: float = 0.0,
    fov: float = 80.0,
    size: str = "640x400",
) -> str:
    """Build a Street View thumbnail URL.

    Returns an unsigned request URL compatible with the Street View Static API.
    """

    base_url = "https://maps.googleapis.com/maps/api/streetview"
    params = {
        "size": size,
        "fov": fov,
        "heading": normalize_angle_deg(heading_deg),
        "pitch": pitch,
        "key": GOOGLE_MAPS_API_KEY or "",
    }
    if "pano_id" in pano_or_latlon:
        params["pano"] = pano_or_latlon["pano_id"]
    else:
        params["location"] = f"{pano_or_latlon['lat']},{pano_or_latlon['lon']}"
    encoded = httpx.QueryParams(params)
    return f"{base_url}?{encoded}"


async def mapillary_nearby(
    lat: float,
    lon: float,
    radius_m: float,
    *,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Fetch nearby Mapillary images using API v4."""

    if not MAPILLARY_TOKEN:
        return []
    params = {
        "access_token": MAPILLARY_TOKEN,
        "fields": "id,compass_angle,captured_at,geometry,thumb_1024_url",  # noqa: E501
        "limit": limit,
        "radius": radius_m,
        "closeto": f"{lon},{lat}",
    }
    try:
        response = await http_get(
            "https://graph.mapillary.com/images",
            params=params,
            headers=None,
            rate_key="mapillary",
        )
    except Exception:
        return []
    data = response.json()
    return data.get("data", [])


async def choose_panorama(
    lat: float,
    lon: float,
    bearing_deg: float,
    providers: Iterable[str],
    radius_m: float,
) -> PanoramaInfo:
    """Select the best panorama among configured providers."""

    for provider in providers:
        if provider == "google":
            metadata = await street_view_metadata(lat, lon, radius_m)
            if metadata:
                thumb_url = street_view_thumbnail(
                    {
                        "pano_id": metadata.get("pano_id"),
                        "lat": metadata.get("location", {}).get("lat", lat),
                        "lon": metadata.get("location", {}).get("lng", lon),
                    },
                    bearing_deg,
                )
                return PanoramaInfo(
                    provider="google",
                    meta=metadata,
                    thumbnail_url=thumb_url,
                )
        elif provider == "mapillary":
            items = await mapillary_nearby(lat, lon, radius_m)
            if items:
                best = min(
                    items,
                    key=lambda item: _mapillary_score(item, bearing_deg, lat, lon),
                )
                thumb = best.get("thumb_1024_url") or best.get("thumb_256_url")
                return PanoramaInfo(
                    provider="mapillary",
                    meta=best,
                    thumbnail_url=thumb,
                )
    return PanoramaInfo(provider=None, meta={}, thumbnail_url=None)


def _mapillary_score(item: Dict[str, Any], bearing_deg: float, lat: float, lon: float) -> float:
    geometry = item.get("geometry", {})
    coordinates = geometry.get("coordinates", [lon, lat])
    ilon, ilat = coordinates[:2]
    compass = item.get("compass_angle")
    if compass is None:
        return float("inf")
    delta_heading = abs(wrap_delta_deg(bearing_deg - float(compass)))
    delta_distance = _haversine_distance(lat, lon, ilat, ilon)
    return delta_heading + delta_distance / 5.0


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


async def run_geo_pipeline(payload: GeoEstimateRequest) -> GeoEstimateResponse:
    """Execute the estimation pipeline for a detection payload."""

    u, _ = bbox_center(payload.bbox)

    method = "intrinsics" if payload.fx is not None and payload.cx is not None else "hfov"
    bearing = bearing_from_bbox(
        u,
        payload.image_width,
        payload.hfov_deg,
        payload.camera_heading_deg,
        cx=payload.cx,
        fx=payload.fx,
    )
    delta = wrap_delta_deg(bearing - payload.camera_heading_deg)

    assumed_distance = payload.assumed_distance_m or DEFAULT_ASSUMED_DISTANCE_M
    target_lat, target_lon = project_point_geodesic(
        payload.camera_lat,
        payload.camera_lon,
        bearing,
        assumed_distance,
    )

    address_task = asyncio.create_task(reverse_geocode(target_lat, target_lon))
    pano_task = asyncio.create_task(
        choose_panorama(
            target_lat,
            target_lon,
            bearing,
            payload.provider_priority,
            payload.radius_m or DEFAULT_SEARCH_RADIUS_M,
        )
    )

    address = await address_task
    panorama = await pano_task

    debug_notes = [
        "Nominatim returns nearest suitable feature to the coordinate.",
    ]
    if not panorama.provider:
        debug_notes.append("No panorama available from configured providers.")

    return GeoEstimateResponse(
        estimated_point=EstimatedPoint(lat=target_lat, lon=target_lon, bearing_deg=bearing),
        address=address,
        panorama=panorama,
        debug=DebugInfo(
            method=method,
            delta_yaw_deg=delta,
            assumed_distance_m=assumed_distance,
            notes=debug_notes,
        ),
    )


router = APIRouter(tags=["geo"])


@router.post("/estimate", response_model=GeoEstimateResponse)
async def estimate_geo(payload: GeoEstimateRequest) -> GeoEstimateResponse:
    try:
        return await asyncio.wait_for(run_geo_pipeline(payload), timeout=6.0)
    except asyncio.TimeoutError as exc:
        raise HTTPException(status_code=504, detail="Pipeline timed out") from exc
    except ValidationError as exc:  # extra safety
        raise HTTPException(status_code=400, detail=json.loads(exc.json())) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/bearing", response_model=BearingResponse)
async def estimate_bearing(payload: GeoEstimateRequest) -> BearingResponse:
    try:
        u, _ = bbox_center(payload.bbox)
        bearing = bearing_from_bbox(
            u,
            payload.image_width,
            payload.hfov_deg,
            payload.camera_heading_deg,
            cx=payload.cx,
            fx=payload.fx,
        )
        return BearingResponse(bearing_deg=bearing)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


if __name__ == "__main__":
    import doctest

    doctest.testmod()

    # bearing_from_bbox using HFOV method
    bbox = BoundingBox(x=0, y=0, w=100, h=100)
    u, _ = bbox_center(bbox)
    bearing = bearing_from_bbox(
        u,
        image_width=200,
        hfov_deg=90.0,
        camera_heading_deg=180.0,
    )
    assert abs(bearing - 180.0) < 1e-6

    # geodesic projection for small distance eastward
    lat2, lon2 = project_point_geodesic(0.0, 0.0, 90.0, 1000.0)
    assert lat2 > -1e-6 and lat2 < 1e-6
    assert 0.008 < lon2 < 0.0095

    # Pydantic round-trip
    payload = GeoEstimateRequest(
        image_width=1920,
        image_height=1080,
        hfov_deg=120.0,
        camera_lat=10.0,
        camera_lon=20.0,
        camera_heading_deg=45.0,
        bbox=BoundingBox(x=0.0, y=0.0, w=100.0, h=200.0),
        assumed_distance_m=15.0,
    )
    data = json.loads(payload.json())
    parsed = GeoEstimateRequest(**data)
    assert parsed.camera_lat == payload.camera_lat
