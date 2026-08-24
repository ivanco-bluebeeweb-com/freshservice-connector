"""Freshservice Connector extension declaration.

Freshservice exposes ITSM data (Tickets/Problems/Changes/Releases/Assets/Knowledge)
through the Freshservice REST API v2, authenticated with HTTP Basic Auth using the
account API key as username.
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "freshservice-connector",
    version="0.1.0",
    display_name="Freshservice",
    description=(
        "Connect your own Freshservice ITSM account to manage Tickets (Incidents & "
        "Service Requests), Problems, Changes, Releases, Assets (CMDB), and Knowledge "
        "Base articles through the Freshservice v2 REST API."
    ),
    icon="icon.svg",
    capabilities=["freshservice:read", "freshservice:write"],
    actions_explicit=True,
    system=False,
)

chat = ChatExtension(
    ext,
    tool_name="freshservice",
    description=(
        "Freshservice Connector — manage Tickets, Problems, Changes, Releases, "
        "Assets, and Knowledge Base articles through the Freshservice v2 REST API."
    ),
)

ext.secret(
    "freshservice_connections",
    "JSON list of connected Freshservice accounts and encrypted API keys. Managed only through connect_freshservice and disconnect_freshservice.",
    required=True,
    write_mode="both",
    max_bytes=65536,
    rotation_hint_days=90,
)(lambda: None)


@ext.health_check
async def health_check(ctx) -> dict:
    """Report whether at least one Freshservice account is configured."""
    raw = await ctx.secrets.get("freshservice_connections")
    import json
    try:
        connections = json.loads(raw) if raw else []
    except (TypeError, ValueError):
        connections = []
    if not connections:
        return {"healthy": True, "detail": "No Freshservice account connected yet."}
    return {"healthy": True, "detail": f"{len(connections)} Freshservice account(s) connected."}
