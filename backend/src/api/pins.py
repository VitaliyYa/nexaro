from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from src.auth.jwt import get_current_user
from src.auth.models import CurrentUser
from src.auth.supabase import get_supabase_client
from src.schemas.dtos import PinCreateRequest, PinUpdateRequest
from src.schemas.generated.api.pin import PropertyPinSchema
from src.services.pin_crypto import encrypt_pin

router = APIRouter(prefix="/properties/{property_id}/locks/{device_id}/pins", tags=["Smart Lock PINs"])


@router.get("", response_model=list[PropertyPinSchema])
async def list_lock_pins(
    property_id: UUID,
    device_id: str,
    db: Client = Depends(get_supabase_client),
):
    """List active and historical PIN codes for a lock (enforced via RLS)."""
    response = (
        db.table("property_pins")
        .select("id, property_id, device_id, pin_name, valid_from, valid_to, is_active, created_at")
        .eq("property_id", str(property_id))
        .eq("device_id", device_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [
        {
            "id": r["id"],
            "property_id": r["property_id"],
            "device_id": r["device_id"],
            "name": r.get("pin_name") or r.get("name", ""),
            "valid_from": r["valid_from"],
            "valid_to": r["valid_to"],
            "is_active": r.get("is_active", True),
            "created_at": r["created_at"],
        }
        for r in response.data
    ]


@router.post("", response_model=PropertyPinSchema, status_code=status.HTTP_201_CREATED)
async def create_lock_pin(
    property_id: UUID,
    device_id: str,
    body: PinCreateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_supabase_client),
):
    """
    Create an encrypted PIN code for a smart lock.
    Encrypts PIN at rest and creates an entry in audit_logs.
    """
    encrypted_pin_val = encrypt_pin(body.pin)

    insert_payload = {
        "property_id": str(property_id),
        "device_id": device_id,
        "pin_name": body.name,
        "pin_encrypted": encrypted_pin_val,
        "valid_from": body.valid_from.isoformat(),
        "valid_to": body.valid_to.isoformat(),
        "is_active": True,
    }

    response = db.table("property_pins").insert(insert_payload).execute()
    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create lock PIN or property access denied",
        )

    pin_record = response.data[0]

    # Create Audit Log Entry
    audit_entry = {
        "user_id": str(current_user.id),
        "property_id": str(property_id),
        "action": "PIN_CREATED",
        "details": {
            "pin_id": pin_record["id"],
            "device_id": device_id,
            "pin_name": body.name,
            "valid_from": body.valid_from.isoformat(),
            "valid_to": body.valid_to.isoformat(),
        },
    }
    db.table("audit_logs").insert(audit_entry).execute()

    return {
        "id": pin_record["id"],
        "property_id": pin_record["property_id"],
        "device_id": pin_record["device_id"],
        "name": pin_record.get("pin_name") or pin_record.get("name", ""),
        "valid_from": pin_record["valid_from"],
        "valid_to": pin_record["valid_to"],
        "is_active": pin_record["is_active"],
        "created_at": pin_record["created_at"],
    }


@router.patch("/{pin_id}", response_model=PropertyPinSchema)
async def update_lock_pin(
    property_id: UUID,
    device_id: str,
    pin_id: UUID,
    body: PinUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_supabase_client),
):
    """Update PIN label, active status, or validity window."""
    update_data = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided to update")

    if "name" in update_data:
        update_data["pin_name"] = update_data.pop("name")

    # Format datetimes if present
    if "valid_from" in update_data and hasattr(update_data["valid_from"], "isoformat"):
        update_data["valid_from"] = update_data["valid_from"].isoformat()
    if "valid_to" in update_data and hasattr(update_data["valid_to"], "isoformat"):
        update_data["valid_to"] = update_data["valid_to"].isoformat()

    response = (
        db.table("property_pins")
        .update(update_data)
        .eq("property_id", str(property_id))
        .eq("device_id", device_id)
        .eq("id", str(pin_id))
        .execute()
    )

    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PIN not found or access denied",
        )

    # Log audit event
    audit_entry = {
        "user_id": str(current_user.id),
        "property_id": str(property_id),
        "action": "PIN_UPDATED",
        "details": {
            "pin_id": str(pin_id),
            "device_id": device_id,
            "updated_fields": list(update_data.keys()),
        },
    }
    db.table("audit_logs").insert(audit_entry).execute()

    r = response.data[0]
    return {
        "id": r["id"],
        "property_id": r["property_id"],
        "device_id": r["device_id"],
        "name": r.get("pin_name") or r.get("name", ""),
        "valid_from": r["valid_from"],
        "valid_to": r["valid_to"],
        "is_active": r.get("is_active", True),
        "created_at": r["created_at"],
    }


@router.delete("/{pin_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lock_pin(
    property_id: UUID,
    device_id: str,
    pin_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_supabase_client),
):
    """Deactivate or remove a PIN code."""
    response = (
        db.table("property_pins")
        .delete()
        .eq("property_id", str(property_id))
        .eq("device_id", device_id)
        .eq("id", str(pin_id))
        .execute()
    )

    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PIN not found or access denied",
        )

    # Log audit event
    audit_entry = {
        "user_id": str(current_user.id),
        "property_id": str(property_id),
        "action": "PIN_DELETED",
        "details": {
            "pin_id": str(pin_id),
            "device_id": device_id,
        },
    }
    db.table("audit_logs").insert(audit_entry).execute()

    return None
