"""Pydantic schemas and DTOs for SmartRent Backend."""

from .dtos import (
    AuditLogResponse,
    DeviceCommandRequest,
    DeviceCreateRequest,
    DeviceLogResponse,
    DeviceUpdateRequest,
    PinCreateRequest,
    PinUpdateRequest,
    PropertyCreateRequest,
    PropertyUpdateRequest,
)
from .generated.api.device import DeviceSchema, DeviceType
from .generated.api.mqtt_auth import (
    Acc,
    AclCheckRequest,
    SuperuserAuthRequest,
    UserAuthRequest,
)
from .generated.api.pin import PropertyPinSchema
from .generated.api.property import PropertySchema
from .generated.mqtt.availability import NodeAvailabilityPayload
from .generated.mqtt.climate_command import ClimateCommandPayload
from .generated.mqtt.climate_state import ClimateStatePayload
from .generated.mqtt.lock_command import LockCommandPayload
from .generated.mqtt.lock_state import LockStatePayload
from .generated.mqtt.relay_command import RelayCommandPayload
from .generated.mqtt.relay_state import RelayStatePayload
from .generated.mqtt.valve_event import ValveEventPayload

__all__ = [
    "Acc",
    "AclCheckRequest",
    "AuditLogResponse",
    "ClimateCommandPayload",
    "ClimateStatePayload",
    "DeviceCommandRequest",
    "DeviceCreateRequest",
    "DeviceLogResponse",
    "DeviceSchema",
    "DeviceType",
    "DeviceUpdateRequest",
    "LockCommandPayload",
    "LockStatePayload",
    "NodeAvailabilityPayload",
    "PinCreateRequest",
    "PinUpdateRequest",
    "PropertyCreateRequest",
    "PropertyPinSchema",
    "PropertySchema",
    "PropertyUpdateRequest",
    "RelayCommandPayload",
    "RelayStatePayload",
    "SuperuserAuthRequest",
    "UserAuthRequest",
    "ValveEventPayload",
]
