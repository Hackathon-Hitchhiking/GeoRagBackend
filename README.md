## GeoRAG Backend Service

This service provides an authenticated API for managing datasets, geospatial features, and documents that are consumed by the GeoRAG machine learning service. It exposes endpoints for registering users, issuing JWT access tokens, managing datasets and their associated metadata, and retrieving content stored in S3.

### Features

- FastAPI application with versioned routing under `/core/v1`.
- JWT based authentication for protected endpoints.
- Dataset CRUD operations with optional filtering by name and region.
- Management of geospatial features tied to datasets.
- Document lifecycle management with support for S3 uploads and presigned download URLs.
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

### ML Service Proxy

All calls destined for the GeoRAG ML backend should be sent via this service. Authenticated clients can call
`/core/v1/ml/<path>` using any HTTP method, and the request will be proxied to the ML service at the same path relative to
`ML_SERVICE_BASE_URL`. Authentication is enforced before proxying and the response is transparently returned to the caller.

### Testing

Run the test suite with:

```bash
uv run pytest
```
