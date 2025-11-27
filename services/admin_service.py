from typing import Dict

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.organization import AdminLoginRequest, TokenResponse
from app.utils.jwt_handler import JWTHandler
from app.utils.security import PasswordHasher


class AdminService:
    """Handle admin authentication and token issuance."""

    def __init__(self, master_db: AsyncIOMotorDatabase) -> None:
        self.organizations = master_db["organizations"]

    async def login(self, payload: AdminLoginRequest) -> TokenResponse:
        """Authenticate admin and generate JWT token with admin_email and organization_name."""
        org_doc = await self.organizations.find_one({"email": payload.email.lower().strip()})
        if org_doc is None:
            raise ValueError("Invalid credentials")

        if not PasswordHasher.verify_password(payload.password, org_doc["password_hash"]):
            raise ValueError("Invalid credentials")

        # JWT payload must include admin_email and organization_name as per requirements
        claims: Dict[str, str] = {
            "admin_email": org_doc["email"],
            "organization_name": org_doc["name"],
        }

        access_token = JWTHandler.create_access_token(claims)
        return TokenResponse(
            access_token=access_token,
            admin_email=org_doc["email"],
            organization_name=org_doc["name"],
        )
