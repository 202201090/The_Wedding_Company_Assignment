from datetime import datetime, timezone
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import build_org_collection_name
from app.models.organization import OrganizationCreate, OrganizationResponse, OrganizationUpdate
from app.utils.security import PasswordHasher


class OrganizationService:
    """Business logic around organization lifecycle management."""

    def __init__(self, master_db: AsyncIOMotorDatabase) -> None:
        self.db = master_db
        self.organizations = master_db["organizations"]

    async def create_organization(self, payload: OrganizationCreate) -> OrganizationResponse:
        """Create a new organization with admin credentials and tenant collection."""
        normalized_name = payload.organization_name.lower().strip()
        existing = await self.organizations.find_one({"name_lower": normalized_name})
        if existing:
            raise ValueError("Organization already exists")

        now = datetime.now(timezone.utc)
        collection_name = build_org_collection_name(payload.organization_name)

        # Create the tenant collection
        await self._ensure_collection_exists(collection_name)

        # Hash password
        password_hash = PasswordHasher.hash_password(payload.password)

        # Create organization document in master collection
        org_doc: Dict[str, Any] = {
            "name": payload.organization_name,
            "name_lower": normalized_name,
            "email": payload.email.lower(),
            "password_hash": password_hash,
            "collection_name": collection_name,
            "created_at": now,
            "updated_at": now,
        }

        org_insert = await self.organizations.insert_one(org_doc)
        org_doc["_id"] = org_insert.inserted_id

        return self._serialize_org(org_doc)

    async def get_organization(self, organization_name: str) -> Optional[OrganizationResponse]:
        """Retrieve organization by name."""
        normalized_name = organization_name.lower().strip()
        org_doc = await self.organizations.find_one({"name_lower": normalized_name})
        if org_doc:
            return self._serialize_org(org_doc)
        return None

    async def get_organization_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve organization by admin email."""
        org_doc = await self.organizations.find_one({"email": email.lower().strip()})
        return org_doc

    async def update_organization(
        self, current_org_name: str, payload: OrganizationUpdate
    ) -> OrganizationResponse:
        """Update organization metadata and migrate collection if name changes."""
        # Find current organization
        normalized_name = current_org_name.lower().strip()
        org_doc = await self.organizations.find_one({"name_lower": normalized_name})
        if org_doc is None:
            raise ValueError("Organization not found")

        updates: Dict[str, Any] = {}
        old_collection_name = org_doc["collection_name"]
        new_collection_name: Optional[str] = None

        # Check if organization name is being changed
        if payload.organization_name and payload.organization_name.lower().strip() != normalized_name:
            new_normalized = payload.organization_name.lower().strip()
            # Check if new name already exists
            existing = await self.organizations.find_one({"name_lower": new_normalized})
            if existing:
                raise ValueError("Organization name already exists")
            updates["name"] = payload.organization_name
            updates["name_lower"] = new_normalized
            new_collection_name = build_org_collection_name(payload.organization_name)
            updates["collection_name"] = new_collection_name

        if payload.email:
            updates["email"] = payload.email.lower().strip()

        if payload.password:
            updates["password_hash"] = PasswordHasher.hash_password(payload.password)

        now = datetime.now(timezone.utc)
        if updates:
            updates["updated_at"] = now
            await self.organizations.update_one({"_id": org_doc["_id"]}, {"$set": updates})
            org_doc.update(updates)

        # Migrate collection if name changed
        if new_collection_name and new_collection_name != old_collection_name:
            await self._migrate_collection(old_collection_name, new_collection_name)

        return self._serialize_org(org_doc)

    async def delete_organization(self, organization_name: str) -> bool:
        """Delete organization and its tenant collection."""
        normalized_name = organization_name.lower().strip()
        org_doc = await self.organizations.find_one({"name_lower": normalized_name})
        if org_doc is None:
            raise ValueError("Organization not found")

        # Drop the tenant collection
        await self._drop_collection(org_doc["collection_name"])
        # Delete from master collection
        await self.organizations.delete_one({"_id": org_doc["_id"]})
        return True

    async def _ensure_collection_exists(self, collection_name: str) -> None:
        existing_collections = await self.db.list_collection_names()
        if collection_name not in existing_collections:
            await self.db.create_collection(collection_name)

    async def _drop_collection(self, collection_name: str) -> None:
        existing_collections = await self.db.list_collection_names()
        if collection_name in existing_collections:
            await self.db.drop_collection(collection_name)

    async def _migrate_collection(self, old_collection_name: str, new_collection_name: str) -> None:
        if old_collection_name == new_collection_name:
            return

        await self._ensure_collection_exists(new_collection_name)
        old_collection = self.db[old_collection_name]
        new_collection = self.db[new_collection_name]

        documents = await old_collection.find().to_list(length=None)
        if documents:
            await new_collection.delete_many({})
            await new_collection.insert_many(documents)

        await old_collection.drop()

    def _serialize_org(self, org_doc: Dict[str, Any]) -> OrganizationResponse:
        """Serialize organization document to response model (excludes password_hash)."""
        return OrganizationResponse(
            id=str(org_doc["_id"]),
            organization_name=org_doc["name"],
            email=org_doc["email"],
            collection_name=org_doc["collection_name"],
            created_at=org_doc["created_at"],
            updated_at=org_doc["updated_at"],
        )
