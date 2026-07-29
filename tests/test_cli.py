"""Unit tests for cli.py — the pip-installed pe-mcp-thin entry point."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import cli


def test_defaults_to_serve(monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["pe-mcp-thin"])
    fake_proxy_module = MagicMock()
    with patch.dict("sys.modules", {"proxy": fake_proxy_module}):
        cli.main()
    fake_proxy_module.proxy.run.assert_called_once_with(transport="stdio")


def test_serve_command(monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["pe-mcp-thin", "serve"])
    fake_proxy_module = MagicMock()
    with patch.dict("sys.modules", {"proxy": fake_proxy_module}):
        cli.main()
    fake_proxy_module.proxy.run.assert_called_once_with(transport="stdio")


def test_validate_command(monkeypatch) -> None:
    monkeypatch.setattr("sys.argv", ["pe-mcp-thin", "validate"])
    fake_selftest_module = MagicMock()
    with patch.dict("sys.modules", {"selftest": fake_selftest_module}):
        cli.main()
    fake_selftest_module.main.assert_called_once()


def test_unknown_command(monkeypatch, capsys) -> None:
    monkeypatch.setattr("sys.argv", ["pe-mcp-thin", "bogus"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "Unknown command: bogus" in err
    assert "Usage: pe-mcp-thin {serve|validate}" in err
