import uuid
from typing import List

from fastapi import APIRouter, Depends, Query, status

from dependencies import (
    get_current_user,
    get_dataset_service,
    get_document_service,
)
from models.user import User
from schemas import (
    DatasetCreate,
    DatasetRead,
    DatasetUpdate,
    DocumentRead,
    GeoFeatureCreate,
    GeoFeatureRead,
    GeoFeatureUpdate,
)
from services.dataset import DatasetService
from services.document import DocumentService


router = APIRouter()


@router.get("/", response_model=List[DatasetRead])
async def list_datasets(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    name: str | None = None,
    region: str | None = None,
    dataset_service: DatasetService = Depends(get_dataset_service),
) -> List[DatasetRead]:
    datasets = await dataset_service.list_datasets(
        limit, offset, name=name, region=region
    )
    return [DatasetRead.model_validate(dataset) for dataset in datasets]


@router.post("/", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    payload: DatasetCreate,
    dataset_service: DatasetService = Depends(get_dataset_service),
    _: User = Depends(get_current_user),
) -> DatasetRead:
    dataset = await dataset_service.create_dataset(payload)
    return DatasetRead.model_validate(dataset)


@router.get("/{dataset_id}", response_model=DatasetRead)
async def retrieve_dataset(
    dataset_id: uuid.UUID,
    dataset_service: DatasetService = Depends(get_dataset_service),
) -> DatasetRead:
    dataset = await dataset_service.get_dataset(dataset_id)
    return DatasetRead.model_validate(dataset)


@router.patch("/{dataset_id}", response_model=DatasetRead)
async def update_dataset(
    dataset_id: uuid.UUID,
    payload: DatasetUpdate,
    dataset_service: DatasetService = Depends(get_dataset_service),
    _: User = Depends(get_current_user),
) -> DatasetRead:
    dataset = await dataset_service.update_dataset(dataset_id, payload)
    return DatasetRead.model_validate(dataset)


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: uuid.UUID,
    dataset_service: DatasetService = Depends(get_dataset_service),
    _: User = Depends(get_current_user),
) -> None:
    await dataset_service.delete_dataset(dataset_id)
    return None


@router.get(
    "/{dataset_id}/features",
    response_model=List[GeoFeatureRead],
)
async def list_dataset_features(
    dataset_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    category: str | None = None,
    dataset_service: DatasetService = Depends(get_dataset_service),
) -> List[GeoFeatureRead]:
    features = await dataset_service.list_features(
        dataset_id, limit, offset, category=category
    )
    return [GeoFeatureRead.model_validate(feature) for feature in features]


@router.post(
    "/{dataset_id}/features",
    response_model=GeoFeatureRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_dataset_feature(
    dataset_id: uuid.UUID,
    payload: GeoFeatureCreate,
    dataset_service: DatasetService = Depends(get_dataset_service),
    _: User = Depends(get_current_user),
) -> GeoFeatureRead:
    feature_payload = payload.model_copy(update={"dataset_id": dataset_id})
    feature = await dataset_service.create_feature(feature_payload)
    return GeoFeatureRead.model_validate(feature)


@router.patch(
    "/features/{feature_id}",
    response_model=GeoFeatureRead,
)
async def update_dataset_feature(
    feature_id: uuid.UUID,
    payload: GeoFeatureUpdate,
    dataset_service: DatasetService = Depends(get_dataset_service),
    _: User = Depends(get_current_user),
) -> GeoFeatureRead:
    feature = await dataset_service.update_feature(feature_id, payload)
    return GeoFeatureRead.model_validate(feature)


@router.delete(
    "/features/{feature_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_dataset_feature(
    feature_id: uuid.UUID,
    dataset_service: DatasetService = Depends(get_dataset_service),
    _: User = Depends(get_current_user),
) -> None:
    await dataset_service.delete_feature(feature_id)
    return None


@router.get(
    "/{dataset_id}/documents",
    response_model=List[DocumentRead],
)
async def list_dataset_documents(
    dataset_id: uuid.UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    presign: bool = False,
    expires_in: int = Query(900, ge=60, le=3600),
    document_service: DocumentService = Depends(get_document_service),
) -> List[DocumentRead]:
    documents = await document_service.list_documents(dataset_id, limit, offset)
    result: List[DocumentRead] = []
    for document in documents:
        response = DocumentRead.model_validate(document)
        if presign:
            response.signed_url = document_service.generate_presigned_url(
                document, expires_in=expires_in
            )
        result.append(response)
    return result
