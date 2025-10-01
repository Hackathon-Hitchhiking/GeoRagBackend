from fastapi import APIRouter

from routing.v1 import auth, datasets, documents, ml

router = APIRouter(prefix="/v1")

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
router.include_router(documents.router, prefix="/documents", tags=["documents"])
router.include_router(ml.router, prefix="/ml", tags=["ml"])

__all__ = ["router"]
