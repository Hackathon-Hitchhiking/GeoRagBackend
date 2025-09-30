import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from errors.errors import ErrEntityConflict
from models.document import Document
from repositories.dataset_repository import DatasetRepository
from repositories.document_repository import DocumentRepository
from schemas.document import DocumentCreate, DocumentUpdate
from services.storage import S3StorageService, get_storage_service


class DocumentService:
    def __init__(
        self,
        db: AsyncSession,
        storage_service: Optional[S3StorageService] = None,
    ):
        self._db = db
        self._repo = DocumentRepository(db)
        self._dataset_repo = DatasetRepository(db)
        self._storage = storage_service or get_storage_service()

    async def list_documents(
        self, dataset_id: uuid.UUID, limit: int, offset: int
    ) -> list[Document]:
        await self._dataset_repo.get(dataset_id)
        return await self._repo.list_by_dataset(dataset_id, limit, offset)

    async def get_document(self, document_id: uuid.UUID) -> Document:
        return await self._repo.get(document_id)

    async def create_document(
        self, payload: DocumentCreate, owner_id: Optional[uuid.UUID]
    ) -> Document:
        await self._dataset_repo.get(payload.dataset_id)

        if payload.inline_content:
            s3_key = payload.s3_key or f"datasets/{payload.dataset_id}/{uuid.uuid4()}.txt"
            await self._storage.upload_text(
                s3_key,
                payload.inline_content,
                content_type=payload.content_type or "text/plain",
            )
        else:
            assert payload.s3_key is not None  # for mypy
            existing = await self._repo.get_by_s3_key(payload.s3_key)
            if existing is not None:
                raise ErrEntityConflict("A document with this storage key already exists")
            await self._storage.ensure_object_exists(payload.s3_key)
            s3_key = payload.s3_key

        document = Document(
            dataset_id=payload.dataset_id,
            owner_id=owner_id,
            title=payload.title,
            summary=payload.summary,
            s3_key=s3_key,
            metadata=payload.metadata,
        )
        document.id = uuid.uuid4()
        return await self._repo.create(document)

    async def update_document(
        self, document_id: uuid.UUID, payload: DocumentUpdate
    ) -> Document:
        document = await self._repo.get(document_id)
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(document, key, value)
        return await self._repo.update(document)

    async def delete_document(self, document_id: uuid.UUID) -> None:
        await self._repo.delete(document_id)

    def generate_presigned_url(self, document: Document, expires_in: int = 900) -> str:
        return self._storage.generate_presigned_url(document.s3_key, expires_in)
