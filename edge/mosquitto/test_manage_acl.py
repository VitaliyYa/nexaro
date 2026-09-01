"""Unit tests for Mosquitto ACL and Passwd Manager."""

import tempfile
from pathlib import Path
import pytest

from edge.mosquitto.manage_acl import (
    AclManager,
    generate_backend_acl_block,
    generate_edge_acl_block,
    hash_mosquitto_password,
)


def test_hash_mosquitto_password():
    pwd = "super-secret-password"
    hashed = hash_mosquitto_password(pwd)
    assert hashed.startswith("$7$")
    parts = hashed.split("$")
    assert len(parts) == 5  # empty, 7, iter, salt, digest


def test_generate_edge_acl_block():
    block = generate_edge_acl_block("prop_123")
    assert "user edge_prop_123" in block
    assert "topic write properties/prop_123/+/+/state" in block
    assert "topic write properties/prop_123/+/+/event" in block
    assert "topic write properties/prop_123/node/+/availability" in block
    assert "topic read properties/prop_123/+/+/set" in block
    # Ensure no wildcards across other properties
    assert "properties/+/" not in block


def test_invalid_property_id():
    with pytest.raises(ValueError):
        generate_edge_acl_block("../invalid/path")

    with pytest.raises(ValueError):
        generate_edge_acl_block("prop space")


def test_generate_backend_acl_block():
    block = generate_backend_acl_block("backend_worker")
    assert "user backend_worker" in block
    assert "topic read properties/+/+/+/state" in block
    assert "topic read properties/+/+/+/event" in block
    assert "topic read properties/+/node/+/availability" in block
    assert "topic write properties/+/+/+/set" in block


def test_acl_manager_workflow():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        acl_file = tmp_path / "acl"
        passwd_file = tmp_path / "passwd"

        manager = AclManager(acl_path=acl_file, passwd_path=passwd_file)

        # 1. Add backend worker
        be_pwd = manager.add_backend_worker("backend_worker", "worker-pass-123")
        assert be_pwd == "worker-pass-123"

        # 2. Add edge nodes
        edge1_pwd = manager.add_edge_node("prop_001", "edge-pass-001")
        assert edge1_pwd == "edge-pass-001"
        edge2_pwd = manager.add_edge_node("prop_002")
        assert len(edge2_pwd) > 10

        # Check users in passwd
        users = manager.read_passwords()
        assert "backend_worker" in users
        assert "edge_prop_001" in users
        assert "edge_prop_002" in users

        # Check ACL content
        acl_content = acl_file.read_text()
        assert "user backend_worker" in acl_content
        assert "user edge_prop_001" in acl_content
        assert "user edge_prop_002" in acl_content
        assert "topic write properties/prop_001/+/+/state" in acl_content
        assert "topic write properties/prop_002/+/+/state" in acl_content

        # 3. Remove edge node
        removed = manager.remove_edge_node("prop_001")
        assert removed is True
        users_after = manager.read_passwords()
        assert "edge_prop_001" not in users_after
        assert "edge_prop_002" in users_after

        acl_content_after = acl_file.read_text()
        assert "user edge_prop_001" not in acl_content_after
        assert "user edge_prop_002" in acl_content_after
