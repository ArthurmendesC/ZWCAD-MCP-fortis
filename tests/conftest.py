"""Shared fixtures for zwcad-mcp tests."""

import pytest


@pytest.fixture(autouse=True)
def _isolate_backend(monkeypatch):
    """Reset the backend singleton between tests."""
    import zwcad_mcp.client as client_mod
    monkeypatch.setattr(client_mod, "_backend", None)
    # Force ezdxf backend for tests (not on Windows or no ZWCAD)
    monkeypatch.setenv("ZWCAD_MCP_BACKEND", "ezdxf")
