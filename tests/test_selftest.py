"""Unit tests for selftest.py — the validate/smoke-test entry point."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import selftest


def run_sync(coro: Any) -> Any:
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def test_check_returns_tool_names() -> None:
    fake_tool_a = MagicMock(name="a")
    fake_tool_a.name = "puppet_node_lookup"
    fake_tool_b = MagicMock(name="b")
    fake_tool_b.name = "puppet_pql_query"

    fake_client = MagicMock()
    fake_client.__aenter__ = AsyncMock(return_value=fake_client)
    fake_client.__aexit__ = AsyncMock(return_value=False)
    fake_client.list_tools = AsyncMock(return_value=[fake_tool_a, fake_tool_b])

    with patch("selftest.Client", return_value=fake_client):
        names = run_sync(selftest.check("https://pe.example.com/mcp/", "/tmp/ca.pem"))

    assert names == ["puppet_node_lookup", "puppet_pql_query"]


def test_main_fails_when_url_unset(monkeypatch, capsys) -> None:
    monkeypatch.delenv("PE_MCP_URL", raising=False)
    monkeypatch.delenv("PE_CA_CERT", raising=False)
    with pytest.raises(SystemExit) as exc:
        selftest.main()
    assert exc.value.code == 1
    assert "PE_MCP_URL is not configured" in capsys.readouterr().err


def test_main_fails_when_url_is_placeholder(monkeypatch, capsys) -> None:
    monkeypatch.setenv("PE_MCP_URL", "https://REPLACE_WITH_MCP_NODE_FQDN/mcp/")
    monkeypatch.delenv("PE_CA_CERT", raising=False)
    with pytest.raises(SystemExit) as exc:
        selftest.main()
    assert exc.value.code == 1
    assert "is not configured" in capsys.readouterr().err


def test_main_fails_when_ca_cert_missing(monkeypatch, capsys, tmp_path) -> None:
    monkeypatch.setenv("PE_MCP_URL", "https://pe.example.com/mcp/")
    monkeypatch.setenv("PE_CA_CERT", str(tmp_path / "does-not-exist.pem"))
    with pytest.raises(SystemExit) as exc:
        selftest.main()
    assert exc.value.code == 1
    assert "PE CA cert not found" in capsys.readouterr().err


def test_main_fails_when_ca_cert_env_unset(monkeypatch, capsys) -> None:
    monkeypatch.setenv("PE_MCP_URL", "https://pe.example.com/mcp/")
    monkeypatch.delenv("PE_CA_CERT", raising=False)
    with pytest.raises(SystemExit) as exc:
        selftest.main()
    assert exc.value.code == 1
    assert "PE CA cert not found" in capsys.readouterr().err


def test_main_fails_when_check_raises(monkeypatch, capsys, tmp_path) -> None:
    ca = tmp_path / "ca.pem"
    ca.write_text("dummy")
    monkeypatch.setenv("PE_MCP_URL", "https://pe.example.com/mcp/")
    monkeypatch.setenv("PE_CA_CERT", str(ca))

    async def raising_check(url: str, ca_cert: str) -> list[str]:
        raise RuntimeError("connection refused")

    with patch("selftest.check", raising_check):
        with pytest.raises(SystemExit) as exc:
            selftest.main()
    assert exc.value.code == 1
    assert "could not reach or authenticate" in capsys.readouterr().err


def test_main_success(monkeypatch, capsys, tmp_path) -> None:
    ca = tmp_path / "ca.pem"
    ca.write_text("dummy")
    monkeypatch.setenv("PE_MCP_URL", "https://pe.example.com/mcp/")
    monkeypatch.setenv("PE_CA_CERT", str(ca))

    async def fake_check(url: str, ca_cert: str) -> list[str]:
        return ["puppet_node_lookup", "puppet_pql_query"]

    with patch("selftest.check", fake_check):
        with pytest.raises(SystemExit) as exc:
            selftest.main()
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "PASS: connected to PE MCP, 2 tool(s) available" in out
    assert "puppet_node_lookup" in out
