from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from src.auth.supabase import get_supabase_client
from src.schemas.dtos import DeviceCreateRequest, DeviceUpdateRequest
from src.schemas.generated.api.device import DeviceSchema

router = APIRouter(prefix="/properties/{property_id}/devices", tags=["Devices"])


@router.get("", response_model=list[DeviceSchema])
async def list_devices(
    property_id: UUID,
    db: Client = Depends(get_supabase_client),
):
    """List all IoT devices registered to this property (enforced via RLS)."""
    response = db.table("devices").select("*").eq("property_id", str(property_id)).order("created_at").execute()
    return response.data


@router.post("", response_model=DeviceSchema, status_code=status.HTTP_201_CREATED)
async def create_device(
    property_id: UUID,
    body: DeviceCreateRequest,
    db: Client = Depends(get_supabase_client),
):
    """Register a new IoT device in this property."""
    payload = {
        "id": body.id,
        "property_id": str(property_id),
        "device_type": body.device_type.value,
        "name": body.name,
        "is_active": body.is_active,
        "settings": body.settings,
    }
    response = db.table("devices").insert(payload).execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to register device or property access denied",
        )
    return response.data[0]


@router.get("/{device_id}", response_model=DeviceSchema)
async def get_device(
    property_id: UUID,
    device_id: str,
    db: Client = Depends(get_supabase_client),
):
    """Retrieve device details."""
    response = db.table("devices").select("*").eq("property_id", str(property_id)).eq("id", device_id).execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found or access denied",
        )
    return response.data[0]


@router.patch("/{device_id}", response_model=DeviceSchema)
async def update_device(
    property_id: UUID,
    device_id: str,
    body: DeviceUpdateRequest,
    db: Client = Depends(get_supabase_client),
):
    """Update device settings or metadata."""
    update_data = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided to update")

    response = db.table("devices").update(update_data).eq("property_id", str(property_id)).eq("id", device_id).execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found or access denied",
        )
    return response.data[0]


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(
    property_id: UUID,
    device_id: str,
    db: Client = Depends(get_supabase_client),
):
    """Delete a device."""
    response = db.table("devices").delete().eq("property_id", str(property_id)).eq("id", device_id).execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found or access denied",
        )
    return None
