import uuid

from fastapi import APIRouter, Depends, Query, status

from dependencies import get_current_user, get_document_service
from models.user import User
from schemas import DocumentCreate, DocumentRead, DocumentUpdate
from services.document import DocumentService


router = APIRouter()


@router.post("/", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def create_document(
    payload: DocumentCreate,
    document_service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_current_user),
) -> DocumentRead:
    document = await document_service.create_document(payload, current_user.id)
    return DocumentRead.model_validate(document)


@router.get("/{document_id}", response_model=DocumentRead)
async def retrieve_document(
    document_id: uuid.UUID,
    presign: bool = False,
    expires_in: int = Query(900, ge=60, le=3600),
    document_service: DocumentService = Depends(get_document_service),
) -> DocumentRead:
    document = await document_service.get_document(document_id)
    response = DocumentRead.model_validate(document)
    if presign:
        response.signed_url = document_service.generate_presigned_url(
            document, expires_in=expires_in
        )
    return response


@router.patch("/{document_id}", response_model=DocumentRead)
async def update_document(
    document_id: uuid.UUID,
    payload: DocumentUpdate,
    document_service: DocumentService = Depends(get_document_service),
    _: User = Depends(get_current_user),
) -> DocumentRead:
    document = await document_service.update_document(document_id, payload)
    return DocumentRead.model_validate(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    document_service: DocumentService = Depends(get_document_service),
    _: User = Depends(get_current_user),
) -> None:
    await document_service.delete_document(document_id)
    return None
