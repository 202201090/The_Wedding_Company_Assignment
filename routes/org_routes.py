import traceback

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import get_master_db
from app.models.organization import OrganizationCreate, OrganizationResponse, OrganizationUpdate
from app.services.organization_service import OrganizationService
from app.utils.dependencies import get_current_admin

router = APIRouter(prefix="/org", tags=["organizations"])


async def get_service(master_db=Depends(get_master_db)) -> OrganizationService:
    """Dependency to get OrganizationService instance."""
    try:
        return OrganizationService(master_db)
    except Exception:
        traceback.print_exc()
        raise


@router.post("/create", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(payload: OrganizationCreate, service: OrganizationService = Depends(get_service)):
    try:
        return await service.create_organization(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        # TEMP logging to surface the real error
        traceback.print_exc()
        raise


@router.get("/get", response_model=OrganizationResponse)
async def get_organization(
    organization_name: str = Query(..., min_length=3, max_length=64, description="Organization name to retrieve"),
    service: OrganizationService = Depends(get_service),
):
    """Retrieve organization details by name."""
    organization = await service.get_organization(organization_name)
    if organization is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return organization


@router.put("/update", response_model=OrganizationResponse)
async def update_organization(
    payload: OrganizationUpdate,
    current_admin: dict = Depends(get_current_admin),
    service: OrganizationService = Depends(get_service),
):
    """Update organization metadata. Requires authentication. Uses JWT to identify current organization."""
    try:
        # Get current organization name from JWT
        current_org_name = current_admin["organization_name"]
        return await service.update_organization(current_org_name, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    organization_name: str = Query(..., min_length=3, max_length=64, description="Organization name to delete"),
    current_admin: dict = Depends(get_current_admin),
    service: OrganizationService = Depends(get_service),
):
    """Delete organization and its tenant collection. Requires authentication."""
    try:
        # Verify the organization_name matches the JWT
        jwt_org_name = current_admin["organization_name"]
        if organization_name.lower().strip() != jwt_org_name.lower().strip():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own organization",
            )

        org = await service.get_organization(organization_name)
        if org is None:
            raise ValueError("Organization not found")

        await service.delete_organization(organization_name)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
