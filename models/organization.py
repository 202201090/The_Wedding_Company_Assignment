from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, constr


class OrganizationCreate(BaseModel):
    """Schema for creating a new organization."""
    organization_name: constr(min_length=3, max_length=64) = Field(..., description="Canonical organization name")
    email: EmailStr = Field(..., description="Primary admin email")
    password: constr(min_length=8, max_length=128) = Field(..., description="Admin password")


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""
    organization_name: Optional[constr(min_length=3, max_length=64)] = Field(None, description="New organization name")
    email: Optional[EmailStr] = Field(None, description="New admin email")
    password: Optional[constr(min_length=8, max_length=128)] = Field(None, description="New admin password")


class OrganizationResponse(BaseModel):
    """Response schema for organization data."""
    id: str
    organization_name: str
    email: EmailStr
    collection_name: str
    created_at: datetime
    updated_at: datetime


class AdminLoginRequest(BaseModel):
    """Schema for admin login."""
    email: EmailStr = Field(..., description="Admin email")
    password: constr(min_length=8, max_length=128) = Field(..., description="Admin password")


class TokenResponse(BaseModel):
    """Response schema for JWT token."""
    access_token: str
    token_type: str = "bearer"
    admin_email: str
    organization_name: str
