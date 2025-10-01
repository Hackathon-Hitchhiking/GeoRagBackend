from fastapi import APIRouter, Depends, Request, Response

from dependencies import get_current_user, get_ml_proxy_service
from models.user import User
from services.ml_proxy import MLProxyService

router = APIRouter()


@router.api_route(
    "/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def proxy_to_ml_service(
    full_path: str,
    request: Request,
    _: User = Depends(get_current_user),
    ml_proxy: MLProxyService = Depends(get_ml_proxy_service),
) -> Response:
    return await ml_proxy.forward(request, full_path)
