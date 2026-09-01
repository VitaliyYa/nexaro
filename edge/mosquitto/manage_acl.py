#!/usr/bin/env python3
"""Mosquitto ACL and Password Management Utility for SmartRent.

Provides CLI and programmatic helpers to manage multi-tenant Edge credentials,
system service users, and strictly scoped ACL rules.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import os
import re
import secrets
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

# Regex validation for safe identifiers
PROPERTY_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,64}$")
USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,64}$")


def hash_mosquitto_password(password: str, iterations: int = 100) -> str:
    """Generate Mosquitto 2.x compatible PBKDF2-SHA512 password hash ($7$).

    Format: $7$<base64_iterations_4bytes><base64_salt><base64_digest>
    """
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha512",
        password.encode("utf-8"),
        salt,
        iterations,
    )

    # Mosquitto encodes iteration count in 4-byte big-endian base64 (without trailing '=')
    iter_bytes = iterations.to_bytes(4, byteorder="big")
    iter_b64 = base64.b64encode(iter_bytes).decode("ascii").rstrip("=")
    salt_b64 = base64.b64encode(salt).decode("ascii").rstrip("=")
    digest_b64 = base64.b64encode(digest).decode("ascii").rstrip("=")

    return f"$7${iter_b64}${salt_b64}${digest_b64}"


def generate_edge_acl_block(property_id: str) -> str:
    """Generate scoped ACL block for a property Edge node."""
    if not PROPERTY_ID_PATTERN.match(property_id):
        raise ValueError(
            f"Invalid property_id '{property_id}'. Allowed characters: [a-zA-Z0-9_-], length: 3-64."
        )

    username = f"edge_{property_id}"
    return (
        f"# Tenant Edge Node: {property_id}\n"
        f"user {username}\n"
        f"topic write properties/{property_id}/+/+/state\n"
        f"topic write properties/{property_id}/+/+/event\n"
        f"topic write properties/{property_id}/node/+/availability\n"
        f"topic read properties/{property_id}/+/+/set\n"
    )


def generate_backend_acl_block(username: str = "backend_worker") -> str:
    """Generate full broker ACL block for Cloud Backend Worker."""
    if not USERNAME_PATTERN.match(username):
        raise ValueError(f"Invalid backend username '{username}'.")

    return (
        f"# Cloud Backend Service: {username}\n"
        f"user {username}\n"
        f"topic read properties/+/+/+/state\n"
        f"topic read properties/+/+/+/event\n"
        f"topic read properties/+/node/+/availability\n"
        f"topic write properties/+/+/+/set\n"
    )


class AclManager:
    """Manages reading and updating Mosquitto passwd and acl files."""

    def __init__(self, acl_path: Path, passwd_path: Path):
        self.acl_path = Path(acl_path)
        self.passwd_path = Path(passwd_path)

    def read_passwords(self) -> Dict[str, str]:
        """Read users and password hashes."""
        if not self.passwd_path.exists():
            return {}
        users = {}
        for line in self.passwd_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                user, pwd_hash = line.split(":", 1)
                users[user.strip()] = pwd_hash.strip()
        return users

    def write_passwords(self, users: Dict[str, str]) -> None:
        """Write users and password hashes."""
        self.passwd_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"{u}:{h}" for u, h in sorted(users.items())]
        self.passwd_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def list_properties(self) -> Set[str]:
        """Extract property IDs from existing ACL file."""
        if not self.acl_path.exists():
            return set()
        props = set()
        for line in self.acl_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("user edge_"):
                user = line.split("user ", 1)[1].strip()
                props.add(user.removeprefix("edge_"))
        return props

    def add_edge_node(self, property_id: str, password: Optional[str] = None) -> str:
        """Add or update an Edge node with generated or provided password."""
        if not PROPERTY_ID_PATTERN.match(property_id):
            raise ValueError(f"Invalid property_id '{property_id}'.")

        username = f"edge_{property_id}"
        generated_pwd = password or secrets.token_urlsafe(24)
        pwd_hash = hash_mosquitto_password(generated_pwd)

        # Update passwd file
        users = self.read_passwords()
        users[username] = pwd_hash
        self.write_passwords(users)

        # Rebuild ACL file
        self.sync_acl()

        return generated_pwd

    def remove_edge_node(self, property_id: str) -> bool:
        """Remove edge node from password and ACL files."""
        username = f"edge_{property_id}"
        users = self.read_passwords()
        if username not in users:
            return False

        del users[username]
        self.write_passwords(users)
        self.sync_acl()
        return True

    def add_backend_worker(self, username: str = "backend_worker", password: Optional[str] = None) -> str:
        """Add or update backend service credentials."""
        if not USERNAME_PATTERN.match(username):
            raise ValueError(f"Invalid backend username '{username}'.")

        generated_pwd = password or secrets.token_urlsafe(32)
        pwd_hash = hash_mosquitto_password(generated_pwd)

        users = self.read_passwords()
        users[username] = pwd_hash
        self.write_passwords(users)
        self.sync_acl()

        return generated_pwd

    def sync_acl(self) -> None:
        """Regenerate acl file based on users in passwd file."""
        users = self.read_passwords()
        self.acl_path.parent.mkdir(parents=True, exist_ok=True)

        header = (
            "# Auto-generated Mosquitto ACL Configuration for SmartRent\n"
            "# DO NOT EDIT DIRECTLY. Use manage_acl.py\n\n"
        )
        blocks: List[str] = [header]

        # Backend workers
        backend_users = [u for u in users if not u.startswith("edge_")]
        for u in sorted(backend_users):
            blocks.append(generate_backend_acl_block(u))
            blocks.append("\n")

        # Edge nodes
        edge_users = [u for u in users if u.startswith("edge_")]
        for u in sorted(edge_users):
            prop_id = u.removeprefix("edge_")
            blocks.append(generate_edge_acl_block(prop_id))
            blocks.append("\n")

        self.acl_path.write_text("".join(blocks), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mosquitto ACL and Passwd Manager for SmartRent")
    parser.add_argument("--acl", default="edge/mosquitto/acl", help="Path to acl file")
    parser.add_argument("--passwd", default="edge/mosquitto/passwd", help="Path to passwd file")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # add-edge
    p_edge = subparsers.add_parser("add-edge", help="Add or update an Edge Node for a property")
    p_edge.add_argument("property_id", help="Property ID (e.g. prop_01J6XYZ)")
    p_edge.add_argument("--password", help="Specific password (auto-generated if omitted)")

    # remove-edge
    p_rm = subparsers.add_parser("remove-edge", help="Remove an Edge Node by property ID")
    p_rm.add_argument("property_id", help="Property ID")

    # add-backend
    p_be = subparsers.add_parser("add-backend", help="Add or update Cloud Backend worker credentials")
    p_be.add_argument("--username", default="backend_worker", help="Username")
    p_be.add_argument("--password", help="Specific password (auto-generated if omitted)")

    # sync
    subparsers.add_parser("sync", help="Synchronize ACL rules from existing passwd file")

    # list
    subparsers.add_parser("list", help="List registered Edge nodes and users")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    manager = AclManager(acl_path=Path(args.acl), passwd_path=Path(args.passwd))

    try:
        if args.command == "add-edge":
            pwd = manager.add_edge_node(args.property_id, args.password)
            print(f"Edge node added for property: {args.property_id}")
            print(f"Username: edge_{args.property_id}")
            print(f"Password: {pwd}")
        elif args.command == "remove-edge":
            removed = manager.remove_edge_node(args.property_id)
            if removed:
                print(f"Edge node for property {args.property_id} removed.")
            else:
                print(f"Property {args.property_id} not found.")
        elif args.command == "add-backend":
            pwd = manager.add_backend_worker(args.username, args.password)
            print(f"Backend worker configured: {args.username}")
            print(f"Password: {pwd}")
        elif args.command == "sync":
            manager.sync_acl()
            print(f"ACL synced successfully to {args.acl}")
        elif args.command == "list":
            users = manager.read_passwords()
            props = manager.list_properties()
            print(f"Total Users: {len(users)}")
            print(f"Edge Nodes ({len(props)}): {', '.join(sorted(props)) if props else 'None'}")
            print(f"Other Users: {', '.join([u for u in users if not u.startswith('edge_')]) or 'None'}")
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
