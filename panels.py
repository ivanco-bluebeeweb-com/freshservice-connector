"""Freshservice Connector panels."""
from __future__ import annotations

from imperal_sdk import ui

import handlers as h
from app import ext


def _field(label: str, node: ui.UINode) -> ui.UINode:
    return ui.Stack(direction="v", gap=1, align="stretch", children=[
        ui.Text(label, variant="label"),
        node,
    ])


@ext.panel("freshservice_sidebar", slot="left", title="Freshservice")
async def freshservice_sidebar(ctx, **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Stack(direction="v", gap=3, align="stretch", children=[
            ui.Text("Connect your Freshservice account", variant="subtitle"),
            ui.Button("Sign in with Freshservice (SSO / OAuth)", variant="primary", size="sm", icon="login"),
            ui.Divider(),
            ui.Text("Or connect via API Key & Domain", variant="caption"),
            ui.Form(action="connect_freshservice", submit_label="Connect", children=[
                _field("Account label", ui.Input(param_name="label", placeholder="Acme IT")),
                _field("Freshservice domain", ui.Input(param_name="domain", placeholder="acme.freshservice.com")),
                _field("API key", ui.Input(param_name="api_key", placeholder="Profile Settings > API Key")),
            ]),
            ui.Button("Where do I find my API key?", variant="ghost", size="sm", icon="HelpCircle",
                      on_click=ui.Call("__panel__freshservice_connect_help")),
        ])
    conn = connections[0]
    label = conn.get("label") or conn.get("domain", "")
    return ui.Stack(direction="v", gap=1, align="stretch", children=[
        ui.Text(label, variant="subtitle"),
        ui.Divider(),
        ui.Button("Tickets", icon="Ticket", variant="ghost", on_click=ui.Call("__panel__freshservice_center", {"view": "tickets"})),
        ui.Button("Problems", icon="AlertTriangle", variant="ghost", on_click=ui.Call("__panel__freshservice_center", {"view": "problems"})),
        ui.Button("Changes", icon="GitPullRequest", variant="ghost", on_click=ui.Call("__panel__freshservice_center", {"view": "changes"})),
        ui.Button("Releases", icon="Package", variant="ghost", on_click=ui.Call("__panel__freshservice_center", {"view": "releases"})),
        ui.Button("Assets", icon="Server", variant="ghost", on_click=ui.Call("__panel__freshservice_center", {"view": "assets"})),
        ui.Button("Knowledge base", icon="BookOpen", variant="ghost", on_click=ui.Call("__panel__freshservice_center", {"view": "knowledge"})),
        ui.Button("People", icon="Users", variant="ghost", on_click=ui.Call("__panel__freshservice_center", {"view": "people"})),
        ui.Divider(),
        ui.Button("App settings", icon="Settings", variant="ghost", on_click=ui.Call("__panel__freshservice_settings")),
    ])


@ext.panel("freshservice_connect_help", slot="center", title="Connecting Freshservice", icon="HelpCircle", center_overlay=True)
async def freshservice_connect_help(ctx, **kwargs) -> ui.UINode:
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Finding your Freshservice API key", level=2),
        ui.Text("Log into your Freshservice account, click your profile picture (top right), and choose 'Profile Settings'. Your API key is shown on the right side of that page.", variant="body"),
        ui.Text("The domain is the subdomain part of your Freshservice URL, e.g. if you access Freshservice at 'https://acme.freshservice.com', enter 'acme.freshservice.com' or just 'acme'.", variant="body"),
        ui.Callout(text="Freshservice unifies Incidents and Service Requests into a single 'Tickets' object, distinguished by a type field. This connector's list_tickets/create_ticket/update_ticket cover both.", type="info"),
    ])


@ext.panel("freshservice_center", slot="center", title="Freshservice", icon="Ticket", center_overlay=True)
async def freshservice_center(ctx, view: str = "tickets", **kwargs) -> ui.UINode:
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Text("Connect a Freshservice account first.", variant="body")

    if view == "problems":
        return ui.Stack(direction="v", gap=3, align="stretch", children=[
            ui.Header(text="Problems", level=2),
            ui.Form(action="list_problems", submit_label="List problems", children=[]),
            ui.Divider(),
            ui.Text("Create problem", variant="subtitle"),
            ui.Form(action="create_problem", submit_label="Create", children=[
                _field("Field values (JSON)", ui.Input(param_name="values", placeholder='{"subject": "Recurring VPN drops", "description": "...", "email": "user@acme.com"}')),
            ]),
        ])

    if view == "changes":
        return ui.Stack(direction="v", gap=3, align="stretch", children=[
            ui.Header(text="Changes", level=2),
            ui.Form(action="list_changes", submit_label="List changes", children=[]),
            ui.Divider(),
            ui.Text("Create change request", variant="subtitle"),
            ui.Form(action="create_change", submit_label="Create", children=[
                _field("Field values (JSON)", ui.Input(param_name="values", placeholder='{"subject": "Upgrade firewall firmware", "description": "...", "email": "user@acme.com"}')),
            ]),
        ])

    if view == "releases":
        return ui.Stack(direction="v", gap=3, align="stretch", children=[
            ui.Header(text="Releases", level=2),
            ui.Form(action="list_releases", submit_label="List releases", children=[]),
            ui.Divider(),
            ui.Text("Create release", variant="subtitle"),
            ui.Form(action="create_release", submit_label="Create", children=[
                _field("Field values (JSON)", ui.Input(param_name="values", placeholder='{"subject": "Q3 network upgrade", "description": "...", "email": "user@acme.com"}')),
            ]),
        ])

    if view == "assets":
        return ui.Stack(direction="v", gap=3, align="stretch", children=[
            ui.Header(text="Assets (CMDB)", level=2),
            ui.Form(action="list_assets", submit_label="List assets", children=[]),
        ])

    if view == "knowledge":
        return ui.Stack(direction="v", gap=3, align="stretch", children=[
            ui.Header(text="Knowledge base", level=2),
            ui.Form(action="list_knowledge_articles", submit_label="List articles", children=[]),
        ])

    if view == "people":
        return ui.Stack(direction="v", gap=3, align="stretch", children=[
            ui.Header(text="Requesters & agents", level=2),
            ui.Text("Requesters", variant="subtitle"),
            ui.Form(action="list_requesters", submit_label="List requesters", children=[]),
            ui.Divider(),
            ui.Text("Agents", variant="subtitle"),
            ui.Form(action="list_agents", submit_label="List agents", children=[]),
        ])

    if view == "generic":
        return ui.Stack(direction="v", gap=3, align="stretch", children=[
            ui.Header(text="Generic API access", level=2),
            ui.Form(action="list_table", submit_label="Run GET", children=[
                _field("API path", ui.Input(param_name="path", placeholder="/tickets")),
                _field("Query params (JSON, optional)", ui.Input(param_name="query_params", placeholder='{"per_page": 30}')),
            ]),
        ])

    # default: tickets
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Tickets", level=2),
        ui.Form(action="list_tickets", submit_label="List tickets", children=[
            _field("Filter query (optional)", ui.Input(param_name="query", placeholder="status:2")),
        ]),
        ui.Divider(),
        ui.Text("Create ticket", variant="subtitle"),
        ui.Form(action="create_ticket", submit_label="Create", children=[
            _field("Field values (JSON)", ui.Input(param_name="values", placeholder='{"subject": "Laptop not booting", "description": "...", "email": "user@acme.com", "priority": 2, "status": 2, "type": "Incident"}')),
        ]),
    ])


@ext.panel("freshservice_connect_help", slot="center", title="Connecting Freshservice", icon="HelpCircle", center_overlay=True)
async def freshservice_connect_help(ctx, **kwargs) -> ui.UINode:
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Header(text="Connecting your Freshservice account", level=2),
        ui.Text("Your API key lives in Freshservice under Profile Settings (click your avatar, top right) — copy the API Key shown there.", variant="body"),
        ui.Text("The domain is just your Freshservice subdomain, e.g. if you log in at 'acme.freshservice.com' enter 'acme.freshservice.com' or just 'acme'.", variant="body"),
        ui.Text("Freshservice unifies Incidents and Service Requests into one 'Ticket' object, distinguished by a type field — that's why there's one Tickets view instead of two.", variant="body"),
        ui.Callout(text="Your API key is stored encrypted and used only to call your own Freshservice account's REST API on your behalf.", type="info"),
    ])