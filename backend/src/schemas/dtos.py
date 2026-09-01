from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.schemas.generated.api.device import DeviceType


class PropertyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    address: str | None = None
    timezone: str = "UTC"


class PropertyUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    address: str | None = None
    timezone: str | None = None


class DeviceCreateRequest(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    device_type: DeviceType
    name: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True
    settings: dict[str, Any] = Field(default_factory=dict)


class DeviceUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    is_active: bool | None = None
    settings: dict[str, Any] | None = None


class PinCreateRequest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=100, description="Guest or staff label")
    pin: str = Field(..., min_length=4, max_length=32, description="Plain text PIN code to be encrypted")
    valid_from: datetime
    valid_to: datetime


class PinUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    is_active: bool | None = None
    valid_from: datetime | None = None
    valid_to: datetime | None = None


class DeviceCommandRequest(BaseModel):
    model_config = ConfigDict(extra="allow")
    command: str = Field(..., description="Action to perform, e.g. ON, OFF, LOCK, UNLOCK")
    duration_seconds: int | None = Field(None, description="Optional delay or duration")
    target_temperature: float | None = None
    hvac_mode: str | None = None
    fan_mode: str | None = None


class AuditLogResponse(BaseModel):
    id: int
    user_id: UUID | None = None
    property_id: UUID | None = None
    action: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class DeviceLogResponse(BaseModel):
    id: int
    property_id: UUID
    device_id: str | None = None
    topic: str
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
