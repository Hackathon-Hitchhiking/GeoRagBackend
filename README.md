## GeoRAG Backend Service

This service provides an authenticated API for managing georeferenced image records that mirror the assets used by the GeoRAG machine learning service. It exposes endpoints for registering users, issuing JWT access tokens, browsing the shared image catalogue, and retrieving signed URLs for the underlying S3 objects. All model-generation requests are proxied to the dedicated ML backend.

### Features

- FastAPI application with versioned routing under `/core/v1`.
- JWT based authentication for protected endpoints.
- Image catalogue APIs backed by the shared `images` table from the ML service (filter by hash, matcher type, or local feature type).
- Optional S3 presigned URLs for the original image and preview objects.
- Authenticated proxy endpoints that forward generation requests to the GeoRAG ML service.

### Configuration

Copy `configs/.env.example` to `configs/.env` and fill in the required values:

```env
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=
POSTGRES_DB=
POSTGRES_PORT=
DEBUG=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=
AWS_S3_BUCKET=
AWS_S3_ENDPOINT_URL=
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ML_SERVICE_BASE_URL=
```

### Running Locally

Install dependencies with [uv](https://github.com/astral-sh/uv) or your preferred tool, then start the development server:

```bash
uv run uvicorn app:app --reload --port 8000
```

The OpenAPI schema is available at `http://localhost:8000/core/openapi.json` and interactive docs at `http://localhost:8000/core/docs`.

### ML Service Integration

The `/core/v1/ml` namespace now exposes typed endpoints that call the GeoRAG ML service using structured request/response models. Common operations such as health checks, image ingestion, catalogue queries, and the various search flows are mapped to explicit FastAPI routes that validate payloads before calling the upstream `/v1/*` API. Authentication is still enforced at the gateway level, and any error returned by the ML backend is propagated with the original status code and message.

### Testing

Run the test suite with:

```bash
uv run pytest
```
