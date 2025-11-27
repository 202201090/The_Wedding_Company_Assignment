import re
from typing import AsyncIterator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase

from app.core.config import settings


class MongoConnectionManager:
    """Create and manage MongoDB client connections."""

    def __init__(self) -> None:
        self._client: AsyncIOMotorClient | None = None

    def get_client(self) -> AsyncIOMotorClient:
        if self._client is None:
            self._client = AsyncIOMotorClient(settings.mongo_uri)
        return self._client

    def get_master_db(self) -> AsyncIOMotorDatabase:
        return self.get_client()[settings.master_db_name]

    async def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None


def normalize_org_name(organization_name: str) -> str:
    """Create a safe slug for collection names (letters, numbers, underscore)."""

    slug = re.sub(r"[^a-zA-Z0-9]+", "_", organization_name.strip().lower())
    return slug.strip("_") or "org"


def build_org_collection_name(organization_name: str) -> str:
    return f"org_{normalize_org_name(organization_name)}"


mongo_manager = MongoConnectionManager()


async def get_master_db() -> AsyncIterator[AsyncIOMotorDatabase]:
    db = mongo_manager.get_master_db()
    try:
        yield db
    finally:
        pass  # no swallow


def get_org_collection(db: AsyncIOMotorDatabase, organization_name: str) -> AsyncIOMotorCollection:
    collection_name = build_org_collection_name(organization_name)
    return db[collection_name]
