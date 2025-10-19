from fastapi import APIRouter

from routing.v1 import auth, geo, images, ml

router = APIRouter(prefix="/v1")

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(geo.router, prefix="/geo", tags=["geo"])
router.include_router(images.router, prefix="/images", tags=["images"])
router.include_router(ml.router, prefix="/ml", tags=["ml"])

__all__ = ["router"]
