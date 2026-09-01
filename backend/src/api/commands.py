import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from src.auth.jwt import get_current_user
from src.auth.models import CurrentUser
from src.auth.supabase import get_supabase_client
from src.mqtt.client import MqttService, get_mqtt_service
from src.schemas.dtos import DeviceCommandRequest
from src.schemas.generated.mqtt.climate_command import ClimateCommandPayload
from src.schemas.generated.mqtt.lock_command import Command as LockCommandEnum
from src.schemas.generated.mqtt.lock_command import LockCommandPayload
from src.schemas.generated.mqtt.relay_command import Command as RelayCommandEnum
from src.schemas.generated.mqtt.relay_command import RelayCommandPayload

router = APIRouter(prefix="/properties/{property_id}/devices/{device_id}/command", tags=["Commands"])


@router.post("", status_code=status.HTTP_200_OK)
async def send_device_command(
    property_id: UUID,
    device_id: str,
    body: DeviceCommandRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Client = Depends(get_supabase_client),
    mqtt: MqttService = Depends(get_mqtt_service),
):
    """
    Sends a control command to an IoT device via MQTT topic `properties/{property_id}/{device_type}/{device_id}/set`.
    Enforces QoS=1 and retain=false.
    """
    # 1. Verify device exists and is accessible to current user (RLS check)
    device_resp = (
        db.table("devices")
        .select("id, property_id, device_type, is_active")
        .eq("property_id", str(property_id))
        .eq("id", device_id)
        .execute()
    )

    if not device_resp.data or len(device_resp.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found or access denied",
        )

    device_info = device_resp.data[0]
    device_type = device_info["device_type"]
    request_id = uuid.uuid4()

    # 2. Build and validate payload based on device_type
    if device_type == "relay":
        try:
            cmd_enum = RelayCommandEnum(body.command.upper())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid relay command '{body.command}'. Must be ON, OFF, or TOGGLE.",
            ) from None
        payload_obj = RelayCommandPayload(
            command=cmd_enum,
            request_id=request_id,
        )
    elif device_type == "lock":
        try:
            cmd_enum = LockCommandEnum(body.command.upper())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid lock command '{body.command}'. Must be LOCK or UNLOCK.",
            ) from None
        payload_obj = LockCommandPayload(
            command=cmd_enum,
            duration_seconds=body.duration_seconds,
            requested_by=str(current_user.id),
            request_id=request_id,
        )
    elif device_type == "climate":
        payload_obj = ClimateCommandPayload(
            request_id=request_id,
            target_temperature=body.target_temperature,
            hvac_mode=body.hvac_mode,
            fan_mode=body.fan_mode,
        )
    else:
        # Generic command structure
        payload_obj = {
            "command": body.command,
            "request_id": str(request_id),
            "requested_by": str(current_user.id),
        }

    payload_dict = payload_obj.model_dump(mode="json") if hasattr(payload_obj, "model_dump") else payload_obj
    topic = f"properties/{property_id}/{device_type}/{device_id}/set"

    # 3. Publish to MQTT Broker
    publish_success = mqtt.publish_command(topic=topic, payload=payload_dict, qos=1, retain=False)

    # 4. Record audit entry for security-relevant operations (e.g. lock commands)
    if device_type == "lock":
        audit_entry = {
            "user_id": str(current_user.id),
            "property_id": str(property_id),
            "action": f"LOCK_COMMAND_{body.command.upper()}",
            "details": {
                "device_id": device_id,
                "request_id": str(request_id),
                "topic": topic,
            },
        }
        try:
            db.table("audit_logs").insert(audit_entry).execute()
        except Exception:
            pass

    return {
        "status": "published" if publish_success else "queued_offline",
        "request_id": str(request_id),
        "topic": topic,
        "payload": payload_dict,
    }
