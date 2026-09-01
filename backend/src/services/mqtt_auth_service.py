import hashlib
import hmac
import re

from src.schemas.generated.api.mqtt_auth import Acc


def verify_password_hash(plain_password: str, stored_hash: str) -> bool:
    """
    Verifies a plain password against a stored password hash.
    Supports PBKDF2-HMAC-SHA256 (format: pbkdf2_sha256$iterations$salt$hash),
    SHA256 hex, or plain string for testing.
    """
    if not stored_hash:
        return False

    if stored_hash.startswith("pbkdf2_sha256$"):
        try:
            parts = stored_hash.split("$")
            if len(parts) == 4:
                _, iterations_str, salt, expected_hash = parts
                iterations = int(iterations_str)
                derived = hashlib.pbkdf2_hmac(
                    "sha256",
                    plain_password.encode("utf-8"),
                    salt.encode("utf-8"),
                    iterations,
                ).hex()
                return hmac.compare_digest(derived, expected_hash)
        except Exception:
            return False

    if stored_hash.startswith("sha256$"):
        try:
            parts = stored_hash.split("$")
            if len(parts) == 3:
                _, salt, expected_hash = parts
                derived = hashlib.sha256((salt + plain_password).encode("utf-8")).hexdigest()
                return hmac.compare_digest(derived, expected_hash)
        except Exception:
            return False

    # Direct SHA-256 comparison fallback
    direct_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    if hmac.compare_digest(direct_hash, stored_hash):
        return True

    # Plain text match comparison (safe timing comparison)
    return hmac.compare_digest(plain_password, stored_hash)


def hash_password_pbkdf2(plain_password: str, salt: str = "smartrent_salt") -> str:
    """Generates standard pbkdf2_sha256 hash for mqtt credentials storage."""
    iterations = 100_000
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        plain_password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()
    return f"pbkdf2_sha256${iterations}${salt}${derived}"


def match_mqtt_topic(pattern: str, topic: str) -> bool:
    """
    Matches an MQTT topic against an MQTT topic pattern (supports + and #).
    """
    if pattern == topic:
        return True

    # Escape regex special characters except + and #
    regex_pattern = "^"
    parts = pattern.split("/")
    regex_parts = []

    for part in parts:
        if part == "+":
            regex_parts.append("[^/]+")
        elif part == "#":
            # # must be at the end
            regex_parts.append(".*")
            break
        else:
            regex_parts.append(re.escape(part))

    regex_pattern = "^" + "/".join(regex_parts) + "$"
    return bool(re.match(regex_pattern, topic))


def is_topic_allowed_for_edge(property_id: str, topic: str, acc: Acc) -> bool:
    """
    Validates if an Edge node (property_id) is allowed to perform action 'acc' on 'topic'.
    - Write / Publish (acc=2):
        properties/<property_id>/+/+/state
        properties/<property_id>/+/+/event
        properties/<property_id>/node/+/availability
    - Read / Subscribe (acc in (1, 3, 4)):
        properties/<property_id>/+/+/set
    """
    prop_id_str = str(property_id)

    # 1. Write / Publish access (acc = 2)
    if acc == Acc.integer_2:
        allowed_write_patterns = [
            f"properties/{prop_id_str}/+/+/state",
            f"properties/{prop_id_str}/+/+/event",
            f"properties/{prop_id_str}/node/+/availability",
        ]
        return any(match_mqtt_topic(pattern, topic) for pattern in allowed_write_patterns)

    # 2. Read / Subscribe access (acc in 1, 3, 4)
    if acc in (Acc.integer_1, Acc.integer_3, Acc.integer_4):
        allowed_read_patterns = [
            f"properties/{prop_id_str}/+/+/set",
            # Also allow subscribing to their own state for state sync if needed
            f"properties/{prop_id_str}/+/+/state",
        ]
        return any(match_mqtt_topic(pattern, topic) for pattern in allowed_read_patterns)

    return False
