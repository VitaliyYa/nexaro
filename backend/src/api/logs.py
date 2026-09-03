from uuid import UUID

from fastapi import APIRouter, Depends, Query
from supabase import Client

from src.auth.supabase import get_supabase_client
from src.schemas.dtos import AuditLogResponse, DeviceLogResponse

router = APIRouter(prefix="/properties/{property_id}/logs", tags=["Logs & History"])


@router.get("/devices", response_model=list[DeviceLogResponse])
async def get_device_logs(
    property_id: UUID,
    device_id: str | None = Query(None, description="Filter by device ID"),
    event_type: str | None = Query(None, description="Filter by event type"),
    limit: int = Query(50, ge=1, le=200, description="Max logs to return"),
    db: Client = Depends(get_supabase_client),
):
    """Retrieve telemetry and event logs for devices in this property (RLS enforced)."""
    query = (
        db.table("device_logs")
        .select("id, property_id, device_id, topic, event_type, payload, created_at")
        .eq("property_id", str(property_id))
    )

    if device_id:
        query = query.eq("device_id", device_id)
    if event_type:
        query = query.eq("event_type", event_type)

    response = query.order("created_at", desc=True).limit(limit).execute()
    return response.data


@router.get("/audit", response_model=list[AuditLogResponse])
async def get_audit_logs(
    property_id: UUID,
    limit: int = Query(50, ge=1, le=200, description="Max audit logs to return"),
    db: Client = Depends(get_supabase_client),
):
    """Retrieve security audit logs for physical access and configuration changes (RLS enforced)."""
    response = (
        db.table("audit_logs")
        .select("id, user_id, property_id, action, details, created_at")
        .eq("property_id", str(property_id))
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data
