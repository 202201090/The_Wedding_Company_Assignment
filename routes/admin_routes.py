from fastapi import APIRouter, Depends, HTTPException, status

from app.core.database import get_master_db
from app.models.organization import AdminLoginRequest, TokenResponse
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])


async def get_service(master_db=Depends(get_master_db)) -> AdminService:
    return AdminService(master_db)


@router.post("/login", response_model=TokenResponse)
async def admin_login(payload: AdminLoginRequest, service: AdminService = Depends(get_service)):
    try:
        return await service.login(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
