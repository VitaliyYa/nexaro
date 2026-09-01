from uuid import UUID

from pydantic import BaseModel, Field


class CurrentUser(BaseModel):
    id: UUID = Field(..., description="User unique identifier (sub claim)")
    email: str | None = None
    role: str | None = "authenticated"
    token: str = Field(..., description="Raw JWT bearer token for RLS propagation")
