from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from src.auth.jwt import get_current_user
from src.auth.models import CurrentUser
from src.auth.supabase import get_supabase_client
from src.schemas.dtos import PropertyCreateRequest, PropertyUpdateRequest
from src.schemas.generated.api.property import PropertySchema

router = APIRouter(prefix="/properties", tags=["Properties"])


@router.get("", response_model=list[PropertySchema])
async def list_properties(
    db: Client = Depends(get_supabase_client),
):
    """List all properties accessible to the authenticated user (enforced via Supabase RLS)."""
    response = db.table("properties").select("*").order("created_at").execute()
    return response.data


@router.post("", response_model=PropertySchema, status_code=status.HTTP_201_CREATED)
async def create_property(
    body: PropertyCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_supabase_client),
):
    """Create a new property belonging to current user."""
    payload = {
        "name": body.name,
        "address": body.address,
        "timezone": body.timezone,
        "owner_id": str(current_user.id),
    }
    response = db.table("properties").insert(payload).execute()
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create property",
        )
    return response.data[0]


@router.get("/{property_id}", response_model=PropertySchema)
async def get_property(
    property_id: UUID,
    db: Client = Depends(get_supabase_client),
):
    """Retrieve property by ID."""
    response = db.table("properties").select("*").eq("id", str(property_id)).execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found or access denied",
        )
    return response.data[0]


@router.patch("/{property_id}", response_model=PropertySchema)
async def update_property(
    property_id: UUID,
    body: PropertyUpdateRequest,
    db: Client = Depends(get_supabase_client),
):
    """Update property fields."""
    update_data = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided to update")

    response = db.table("properties").update(update_data).eq("id", str(property_id)).execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found or access denied",
        )
    return response.data[0]


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(
    property_id: UUID,
    db: Client = Depends(get_supabase_client),
):
    """Delete property."""
    response = db.table("properties").delete().eq("id", str(property_id)).execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found or access denied",
        )
    return None
