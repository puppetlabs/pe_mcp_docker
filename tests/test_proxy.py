"""Unit tests for proxy.py — module-level env-driven config and proxy wiring.

proxy.py builds its Client/proxy at import time from env vars, so these
tests reload the module under controlled env vars rather than calling
functions on an already-imported instance.
"""

from __future__ import annotations

import importlib
import sys

import proxy as _proxy_first_import  # noqa: F401  (ensures baseline import works)


def _reload_proxy_with_env(monkeypatch, **env: str):
    for key in ("SMART_MCP_URL", "PE_CA_CERT"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    sys.modules.pop("proxy", None)
    return importlib.import_module("proxy")


def test_defaults_when_env_unset(monkeypatch) -> None:
    mod = _reload_proxy_with_env(monkeypatch)
    assert mod.REMOTE_MCP_URL == "https://REPLACE_WITH_MCP_NODE_FQDN/mcp/"
    assert mod.CA_CERT_PATH == str(mod.DEFAULT_CA_CERT)
    assert mod.CA_CERT_PATH == "/config/pe-ca.pem"


def test_env_vars_override_defaults(monkeypatch) -> None:
    mod = _reload_proxy_with_env(
        monkeypatch,
        SMART_MCP_URL="https://pe.example.com/mcp/",
        PE_CA_CERT="/custom/ca.pem",
    )
    assert mod.REMOTE_MCP_URL == "https://pe.example.com/mcp/"
    assert mod.CA_CERT_PATH == "/custom/ca.pem"


def test_proxy_and_client_are_constructed(monkeypatch) -> None:
    mod = _reload_proxy_with_env(monkeypatch)
    assert mod.client is not None
    assert mod.proxy is not None
