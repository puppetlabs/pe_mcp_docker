"""Unit tests for proxy.py — module-level env-driven config and proxy wiring.

proxy.py builds its Client/proxy at import time from env vars, so these
tests reload the module under controlled env vars rather than calling
functions on an already-imported instance.
"""

from __future__ import annotations

import http.server
import importlib
import sys
import threading

import proxy as _proxy_first_import  # noqa: F401  (ensures baseline import works)


def _reload_proxy_with_env(monkeypatch, **env: str):
    for key in ("PE_MCP_URL", "PE_CA_CERT", "PE_RBAC_TOKEN"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    sys.modules.pop("proxy", None)
    return importlib.import_module("proxy")


def test_defaults_when_env_unset(monkeypatch) -> None:
    mod = _reload_proxy_with_env(monkeypatch)
    assert mod.REMOTE_MCP_URL == "https://REPLACE_WITH_MCP_NODE_FQDN/mcp"
    assert mod.CA_CERT_PATH == str(mod.DEFAULT_CA_CERT)
    assert mod.CA_CERT_PATH == "/config/pe-ca.pem"


def test_env_vars_override_defaults(monkeypatch) -> None:
    mod = _reload_proxy_with_env(
        monkeypatch,
        PE_MCP_URL="https://pe.example.com/mcp",
        PE_CA_CERT="/custom/ca.pem",
    )
    assert mod.REMOTE_MCP_URL == "https://pe.example.com/mcp"
    assert mod.CA_CERT_PATH == "/custom/ca.pem"


def test_trailing_slash_is_normalized(monkeypatch) -> None:
    """A trailing slash 404s after auth and surfaces as an opaque
    "Session terminated", so accept either form."""
    mod = _reload_proxy_with_env(
        monkeypatch, PE_MCP_URL="https://pe.example.com/mcp/"
    )
    assert mod.REMOTE_MCP_URL == "https://pe.example.com/mcp"
    assert mod.transport.url == "https://pe.example.com/mcp"


def test_multiple_trailing_slashes_are_normalized(monkeypatch) -> None:
    mod = _reload_proxy_with_env(
        monkeypatch, PE_MCP_URL="https://pe.example.com/mcp///"
    )
    assert mod.REMOTE_MCP_URL == "https://pe.example.com/mcp"


def test_surrounding_whitespace_is_stripped(monkeypatch) -> None:
    mod = _reload_proxy_with_env(
        monkeypatch,
        PE_MCP_URL="  https://pe.example.com/mcp/ \n",
        PE_CA_CERT="  /custom/ca.pem \n",
    )
    assert mod.REMOTE_MCP_URL == "https://pe.example.com/mcp"
    assert mod.CA_CERT_PATH == "/custom/ca.pem"


def test_no_auth_header_when_token_unset(monkeypatch) -> None:
    """Deployments that don't gate on RBAC need no token — send no header."""
    mod = _reload_proxy_with_env(monkeypatch)
    assert mod.RBAC_TOKEN == ""
    assert mod.AUTH_HEADERS == {}
    assert "X-Authentication" not in mod.transport.headers


def test_no_auth_header_when_token_empty(monkeypatch) -> None:
    mod = _reload_proxy_with_env(
        monkeypatch,
        PE_MCP_URL="https://pe.example.com/mcp",
        PE_RBAC_TOKEN="",
    )
    assert mod.AUTH_HEADERS == {}
    assert "X-Authentication" not in mod.transport.headers


def test_whitespace_only_token_sends_no_header(monkeypatch) -> None:
    """An empty header value can be rejected outright, so treat blank as absent."""
    mod = _reload_proxy_with_env(
        monkeypatch,
        PE_MCP_URL="https://pe.example.com/mcp",
        PE_RBAC_TOKEN="   \n ",
    )
    assert mod.RBAC_TOKEN == ""
    assert mod.AUTH_HEADERS == {}
    assert "X-Authentication" not in mod.transport.headers


def test_token_is_stripped(monkeypatch) -> None:
    mod = _reload_proxy_with_env(
        monkeypatch,
        PE_MCP_URL="https://pe.example.com/mcp",
        PE_RBAC_TOKEN="  s3cret\n",
    )
    assert mod.AUTH_HEADERS == {"X-Authentication": "s3cret"}


def test_rbac_token_becomes_x_authentication_header(monkeypatch) -> None:
    mod = _reload_proxy_with_env(
        monkeypatch,
        PE_MCP_URL="https://pe.example.com/mcp/",
        PE_CA_CERT="/custom/ca.pem",
        PE_RBAC_TOKEN="s3cret",
    )
    assert mod.AUTH_HEADERS == {"X-Authentication": "s3cret"}
    assert mod.transport.headers["X-Authentication"] == "s3cret"


def test_ca_cert_applied_via_httpx_factory(monkeypatch) -> None:
    """Supplying a factory makes fastmcp ignore transport.verify, so the CA
    cert must come from the factory or TLS falls back to system CAs."""
    mod = _reload_proxy_with_env(
        monkeypatch,
        PE_MCP_URL="https://pe.example.com/mcp",
        PE_CA_CERT="/custom/ca.pem",
        PE_RBAC_TOKEN="s3cret",
    )
    assert mod.transport.httpx_client_factory is mod._httpx_client_factory

    captured = {}

    def fake_async_client(**kwargs):
        captured.update(kwargs)
        return "client"

    monkeypatch.setattr(mod.httpx, "AsyncClient", fake_async_client)
    mod._httpx_client_factory()

    assert captured["verify"] == "/custom/ca.pem"
    assert captured["follow_redirects"] is True
    assert mod._diagnose_response in captured["event_hooks"]["response"]


def test_httpx_factory_forwards_headers_and_auth(monkeypatch) -> None:
    mod = _reload_proxy_with_env(monkeypatch, PE_MCP_URL="https://pe.example.com/mcp")

    captured = {}

    def fake_async_client(**kwargs):
        captured.update(kwargs)
        return "client"

    monkeypatch.setattr(mod.httpx, "AsyncClient", fake_async_client)
    mod._httpx_client_factory(headers={"A": "b"}, auth="auth-obj")

    assert captured["headers"] == {"A": "b"}
    assert captured["auth"] == "auth-obj"


def test_httpx_factory_accepts_the_kwargs_fastmcp_actually_sends(monkeypatch) -> None:
    """Regression: fastmcp passes follow_redirects, which a factory declaring
    only (headers, timeout, auth) rejects at connect time with a TypeError."""
    mod = _reload_proxy_with_env(monkeypatch, PE_MCP_URL="https://pe.example.com/mcp")

    captured = {}

    def fake_async_client(**kwargs):
        captured.update(kwargs)
        return "client"

    monkeypatch.setattr(mod.httpx, "AsyncClient", fake_async_client)
    mod._httpx_client_factory(
        headers={"A": "b"}, auth=None, follow_redirects=True, timeout=None
    )

    assert captured["follow_redirects"] is True
    assert captured["timeout"] is not None
    assert mod._diagnose_response in captured["event_hooks"]["response"]


def test_httpx_factory_preserves_caller_event_hooks(monkeypatch) -> None:
    mod = _reload_proxy_with_env(monkeypatch, PE_MCP_URL="https://pe.example.com/mcp")

    captured = {}

    def fake_async_client(**kwargs):
        captured.update(kwargs)
        return "client"

    async def other_hook(response):  # pragma: no cover - never invoked
        return None

    monkeypatch.setattr(mod.httpx, "AsyncClient", fake_async_client)
    mod._httpx_client_factory(event_hooks={"response": [other_hook]})

    assert captured["event_hooks"]["response"] == [other_hook, mod._diagnose_response]


def _run(coro):
    import asyncio

    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class _FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


def test_401_without_token_explains_token_is_required(monkeypatch, capsys) -> None:
    mod = _reload_proxy_with_env(monkeypatch, PE_MCP_URL="https://pe.example.com/mcp")
    _run(mod._diagnose_response(_FakeResponse(401)))
    err = capsys.readouterr().err
    assert "no" in err and "PE_RBAC_TOKEN" in err
    assert "puppet-access login" in err


def test_401_with_token_explains_rejection(monkeypatch, capsys) -> None:
    mod = _reload_proxy_with_env(
        monkeypatch,
        PE_MCP_URL="https://pe.example.com/mcp",
        PE_RBAC_TOKEN="s3cret",
    )
    _run(mod._diagnose_response(_FakeResponse(401)))
    err = capsys.readouterr().err
    assert "rejected" in err
    assert "expired" in err


def test_401_warning_is_emitted_only_once(monkeypatch, capsys) -> None:
    mod = _reload_proxy_with_env(monkeypatch, PE_MCP_URL="https://pe.example.com/mcp")
    _run(mod._diagnose_response(_FakeResponse(401)))
    _run(mod._diagnose_response(_FakeResponse(401)))
    assert capsys.readouterr().err.count("ERROR:") == 1


def test_non_401_response_is_silent(monkeypatch, capsys) -> None:
    mod = _reload_proxy_with_env(monkeypatch, PE_MCP_URL="https://pe.example.com/mcp")
    for status in (200, 404, 500):
        _run(mod._diagnose_response(_FakeResponse(status)))
    assert capsys.readouterr().err == ""


def test_401_diagnostic_never_prints_the_token_value(monkeypatch, capsys) -> None:
    """The token is a credential; _diagnose_response must never echo it, even
    though it's a module-level global readily available where the hint is
    printed."""
    mod = _reload_proxy_with_env(
        monkeypatch,
        PE_MCP_URL="https://pe.example.com/mcp",
        PE_RBAC_TOKEN="s3cret-token-value",
    )
    _run(mod._diagnose_response(_FakeResponse(401)))
    captured = capsys.readouterr()
    assert "s3cret-token-value" not in captured.out
    assert "s3cret-token-value" not in captured.err


class _CapturingHandler(http.server.BaseHTTPRequestHandler):
    """Records the headers of the one request it expects to receive."""

    received_headers: dict[str, str] = {}

    def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler naming)
        _CapturingHandler.received_headers = dict(self.headers)
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args: object) -> None:  # keep test output quiet
        pass


def test_auth_header_reaches_a_real_http_server(monkeypatch) -> None:
    """The unit tests elsewhere assert on StreamableHttpTransport/factory
    kwargs, which would miss a fastmcp/httpx API shift that stopped the
    header from actually being sent. Prove it end-to-end: a real
    httpx.AsyncClient built by the real factory, over a real loopback
    socket, must deliver X-Authentication to the far end."""
    mod = _reload_proxy_with_env(
        monkeypatch,
        PE_MCP_URL="https://pe.example.com/mcp",
        PE_RBAC_TOKEN="s3cret",
    )
    # This request is plain HTTP, not HTTPS, so there's nothing to verify --
    # bypass the factory's CA-cert loading rather than feeding it a fake cert.
    monkeypatch.setattr(mod, "CA_CERT_PATH", False)

    server = http.server.HTTPServer(("127.0.0.1", 0), _CapturingHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.handle_request, daemon=True)
    thread.start()

    async def _make_request() -> None:
        client = mod._httpx_client_factory(headers=mod.AUTH_HEADERS)
        async with client:
            await client.get(f"http://127.0.0.1:{port}/")

    try:
        _run(_make_request())
        thread.join(timeout=5)
    finally:
        server.server_close()

    assert _CapturingHandler.received_headers.get("X-Authentication") == "s3cret"


def test_proxy_and_client_are_constructed(monkeypatch) -> None:
    mod = _reload_proxy_with_env(monkeypatch)
    assert mod.client is not None
    assert mod.proxy is not None
