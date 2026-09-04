from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from supabase import Client

from src.auth.supabase import get_supabase_client
from src.schemas.dtos import AuditLogResponse, DeviceLogResponse, UnifiedLogResponse

router = APIRouter(prefix="/properties/{property_id}/logs", tags=["Logs & History"])


@router.get("", response_model=list[UnifiedLogResponse])
@router.get("/", response_model=list[UnifiedLogResponse], include_in_schema=False)
async def get_property_logs(
    property_id: UUID,
    source: str = Query("all", description="Filter source: 'all', 'devices', or 'audit'"),
    device_id: str | None = Query(None, description="Filter by device ID"),
    limit: int = Query(50, ge=1, le=200, description="Max logs to return"),
    db: Client = Depends(get_supabase_client),
):
    """Retrieve unified activity and audit logs for this property (RLS enforced)."""
    unified_entries: list[dict[str, Any]] = []

    # 1. Device Telemetry Logs
    if source in ("all", "devices"):
        d_query = (
            db.table("device_logs")
            .select("id, property_id, device_id, topic, event_type, payload, created_at")
            .eq("property_id", str(property_id))
        )
        if device_id:
            d_query = d_query.eq("device_id", device_id)
        dev_logs = d_query.order("created_at", desc=True).limit(limit).execute().data or []
        for d in dev_logs:
            unified_entries.append(
                {
                    "id": f"dev_{d['id']}",
                    "property_id": d["property_id"],
                    "device_id": d.get("device_id"),
                    "topic": d.get("topic") or "iot/device",
                    "event_type": d.get("event_type", "state"),
                    "payload": d.get("payload") or {},
                    "created_at": d["created_at"],
                }
            )

    # 2. Security & Operation Audit Logs
    if source in ("all", "audit"):
        a_query = (
            db.table("audit_logs")
            .select("id, user_id, property_id, action, details, created_at")
            .eq("property_id", str(property_id))
        )
        audit_logs_data = a_query.order("created_at", desc=True).limit(limit).execute().data or []
        for a in audit_logs_data:
            details = a.get("details") or {}
            audit_dev_id = details.get("device_id")
            if device_id and audit_dev_id != device_id:
                continue
            unified_entries.append(
                {
                    "id": f"audit_{a['id']}",
                    "property_id": a["property_id"],
                    "device_id": audit_dev_id,
                    "topic": "security/audit",
                    "event_type": a.get("action", "AUDIT"),
                    "payload": details,
                    "created_at": a["created_at"],
                }
            )

    # Sort combined entries by created_at descending
    unified_entries.sort(key=lambda x: str(x.get("created_at", "")), reverse=True)
    return unified_entries[:limit]


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
