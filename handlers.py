"""Chat functions for Freshservice Connector."""
from __future__ import annotations

import json
import uuid

from imperal_sdk import ActionResult

import freshservice_client as fc
from app import chat
from schemas import (
    Article, ArticleList, Asset, AssetIdParams, AssetList, AuditHealthParams,
    ChangeIdParams, ChangeRequest, ChangeRequestList, ConnectFreshserviceParams,
    ConnectionList, ConnectionRefParams, CreateChangeParams,
    CreateProblemParams, CreateReleaseParams, CreateTicketParams,
    DeleteResult, DisconnectFreshserviceParams, FreshserviceConnection,
    GenericDeleteParams, GenericGetParams, GenericPayload, GenericWriteParams,
    HealthAudit, ListArticlesParams, ListAssetsParams, ListChangesParams,
    ListPeopleParams, ListProblemsParams, ListReleasesParams,
    ListTicketsParams, NoParams, Person, PersonList, Problem, ProblemIdParams,
    ProblemList, Release, ReleaseIdParams, ReleaseList, Ticket, TicketIdParams,
    TicketList, UpdateChangeParams, UpdateProblemParams, UpdateReleaseParams,
    UpdateTicketParams,
)

_SECRET_NAME = "freshservice_connections"


async def _load_connections(ctx) -> list[dict]:
    raw = await ctx.secrets.get(_SECRET_NAME)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return data if isinstance(data, list) else []


async def _save_connections(ctx, connections: list[dict]) -> None:
    await ctx.secrets.set(_SECRET_NAME, json.dumps(connections))


def _connection_entity(connection: dict) -> FreshserviceConnection:
    label = connection.get("label") or connection.get("domain", "")
    return FreshserviceConnection(
        id=connection.get("id", ""), title=label, label=label,
        domain=connection.get("domain", ""), connected=True,
    )


def _find_connection(connections: list[dict], connection_id: str) -> dict | None:
    if not connections:
        return None
    if not connection_id:
        return connections[0]
    for c in connections:
        if c.get("id") == connection_id:
            return c
    return None


async def _resolve_client(ctx, connection_id: str) -> tuple[dict, fc.FreshserviceClient]:
    connections = await _load_connections(ctx)
    connection = _find_connection(connections, connection_id)
    if not connection:
        raise fc.FreshserviceError("No Freshservice account connected. Use connect_freshservice first.")
    client = fc.FreshserviceClient(connection["domain"], connection["api_key"])
    return connection, client


@chat.function("connect_freshservice", "Connect your own Freshservice account by saving your domain and API key, after checking they actually work.", action_type="write", chain_callable=True, data_model=FreshserviceConnection, event="freshservice-connector.connect_freshservice", effects=["freshservice.provider.connected"])
async def connect_freshservice(ctx, params: ConnectFreshserviceParams) -> ActionResult:
    """Imperal action: connect_freshservice."""
    try:
        client = fc.FreshserviceClient(params.domain, params.api_key)
        await client.ping()
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_CONNECT_FAILED", retryable=exc.retryable)
    connections = await _load_connections(ctx)
    connection = {
        "id": str(uuid.uuid4()), "label": params.label or client.domain,
        "domain": client.domain, "api_key": params.api_key,
    }
    connections.append(connection)
    await _save_connections(ctx, connections)
    return ActionResult.success(data=_connection_entity(connection), summary=f"Connected to {client.domain}.")


@chat.function("disconnect_freshservice", "Disconnect a Freshservice account: deletes the saved domain/API key.", action_type="write", chain_callable=True, data_model=DeleteResult, event="freshservice-connector.disconnect_freshservice", effects=["freshservice.provider.disconnected"])
async def disconnect_freshservice(ctx, params: DisconnectFreshserviceParams) -> ActionResult:
    """Imperal action: disconnect_freshservice."""
    connections = await _load_connections(ctx)
    remaining = [c for c in connections if c.get("id") != params.connection_id]
    if len(remaining) == len(connections):
        return ActionResult.error("Connection not found.", code="FRESHSERVICE_CONNECTION_NOT_FOUND")
    await _save_connections(ctx, remaining)
    return ActionResult.success(data=DeleteResult(id=params.connection_id, deleted=True), summary="Disconnected.")


@chat.function("list_connections", "List the connected Freshservice accounts.", action_type="read", chain_callable=True, data_model=ConnectionList, event="freshservice-connector.list_connections")
async def list_connections(ctx, params: NoParams) -> ActionResult:
    """Imperal action: list_connections."""
    connections = await _load_connections(ctx)
    return ActionResult.success(data=ConnectionList(connections=[_connection_entity(c) for c in connections]))


def _to_ticket(item: dict) -> Ticket:
    return Ticket(
        ticket_id=str(item.get("id", "")), title=item.get("subject", str(item.get("id", ""))),
        subject=item.get("subject", ""), ticket_type=item.get("type", ""),
        status=item.get("status", 0), priority=item.get("priority", 0), raw=item,
    )


@chat.function("list_tickets", "List tickets (Incidents and Service Requests) in the connected Freshservice account, optionally filtered by a Freshservice filter query.", action_type="read", chain_callable=True, data_model=TicketList, event="freshservice-connector.list_tickets")
async def list_tickets(ctx, params: ListTicketsParams) -> ActionResult:
    """Imperal action: list_tickets."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        items = await client.list_tickets(query=params.query, per_page=params.per_page)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_LIST_TICKETS_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=TicketList(tickets=[_to_ticket(i) for i in items]))


@chat.function("get_ticket", "Read one ticket in full by id.", action_type="read", chain_callable=True, data_model=Ticket, event="freshservice-connector.get_ticket")
async def get_ticket(ctx, params: TicketIdParams) -> ActionResult:
    """Imperal action: get_ticket."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        item = await client.get_ticket(params.ticket_id)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_GET_TICKET_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=_to_ticket(item))


@chat.function("create_ticket", "Create a new ticket (Incident or Service Request).", action_type="write", chain_callable=True, data_model=Ticket, event="freshservice-connector.create_ticket", effects=["create:ticket"])
async def create_ticket(ctx, params: CreateTicketParams) -> ActionResult:
    """Imperal action: create_ticket."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        item = await client.create_ticket(params.values)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_CREATE_TICKET_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=_to_ticket(item), summary="Ticket created.")


@chat.function("update_ticket", "Update selected fields of an existing ticket. Only given fields change.", action_type="write", chain_callable=True, data_model=Ticket, event="freshservice-connector.update_ticket", effects=["update:ticket"])
async def update_ticket(ctx, params: UpdateTicketParams) -> ActionResult:
    """Imperal action: update_ticket."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        item = await client.update_ticket(params.ticket_id, params.values)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_UPDATE_TICKET_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=_to_ticket(item), summary="Ticket updated.")


def _to_problem(item: dict) -> Problem:
    return Problem(
        problem_id=str(item.get("id", "")), title=item.get("subject", str(item.get("id", ""))),
        subject=item.get("subject", ""), status=item.get("status", 0), raw=item,
    )


@chat.function("list_problems", "List problems on the connected Freshservice account.", action_type="read", chain_callable=True, data_model=ProblemList, event="freshservice-connector.list_problems")
async def list_problems(ctx, params: ListProblemsParams) -> ActionResult:
    """Imperal action: list_problems."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        items = await client.list_problems(per_page=params.per_page)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_LIST_PROBLEMS_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=ProblemList(problems=[_to_problem(i) for i in items]))


@chat.function("create_problem", "Create a new problem record.", action_type="write", chain_callable=True, data_model=Problem, event="freshservice-connector.create_problem", effects=["create:problem"])
async def create_problem(ctx, params: CreateProblemParams) -> ActionResult:
    """Imperal action: create_problem."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        item = await client.create_problem(params.values)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_CREATE_PROBLEM_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=_to_problem(item), summary="Problem created.")


@chat.function("update_problem", "Update selected fields of an existing problem.", action_type="write", chain_callable=True, data_model=Problem, event="freshservice-connector.update_problem", effects=["update:problem"])
async def update_problem(ctx, params: UpdateProblemParams) -> ActionResult:
    """Imperal action: update_problem."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        item = await client.update_problem(params.problem_id, params.values)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_UPDATE_PROBLEM_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=_to_problem(item), summary="Problem updated.")


def _to_change(item: dict) -> ChangeRequest:
    return ChangeRequest(
        change_id=str(item.get("id", "")), title=item.get("subject", str(item.get("id", ""))),
        subject=item.get("subject", ""), status=item.get("status", 0), raw=item,
    )


@chat.function("list_changes", "List change requests on the connected Freshservice account.", action_type="read", chain_callable=True, data_model=ChangeRequestList, event="freshservice-connector.list_changes")
async def list_changes(ctx, params: ListChangesParams) -> ActionResult:
    """Imperal action: list_changes."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        items = await client.list_changes(per_page=params.per_page)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_LIST_CHANGES_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=ChangeRequestList(changes=[_to_change(i) for i in items]))


@chat.function("create_change", "Create a new change request.", action_type="write", chain_callable=True, data_model=ChangeRequest, event="freshservice-connector.create_change", effects=["create:change"])
async def create_change(ctx, params: CreateChangeParams) -> ActionResult:
    """Imperal action: create_change."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        item = await client.create_change(params.values)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_CREATE_CHANGE_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=_to_change(item), summary="Change request created.")


@chat.function("update_change", "Update selected fields of an existing change request.", action_type="write", chain_callable=True, data_model=ChangeRequest, event="freshservice-connector.update_change", effects=["update:change"])
async def update_change(ctx, params: UpdateChangeParams) -> ActionResult:
    """Imperal action: update_change."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        item = await client.update_change(params.change_id, params.values)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_UPDATE_CHANGE_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=_to_change(item), summary="Change request updated.")


def _to_release(item: dict) -> Release:
    return Release(
        release_id=str(item.get("id", "")), title=item.get("subject", str(item.get("id", ""))),
        subject=item.get("subject", ""), status=item.get("status", 0), raw=item,
    )


@chat.function("list_releases", "List releases on the connected Freshservice account.", action_type="read", chain_callable=True, data_model=ReleaseList, event="freshservice-connector.list_releases")
async def list_releases(ctx, params: ListReleasesParams) -> ActionResult:
    """Imperal action: list_releases."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        items = await client.list_releases(per_page=params.per_page)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_LIST_RELEASES_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=ReleaseList(releases=[_to_release(i) for i in items]))


@chat.function("create_release", "Create a new release record.", action_type="write", chain_callable=True, data_model=Release, event="freshservice-connector.create_release", effects=["create:release"])
async def create_release(ctx, params: CreateReleaseParams) -> ActionResult:
    """Imperal action: create_release."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        item = await client.create_release(params.values)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_CREATE_RELEASE_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=_to_release(item), summary="Release created.")


@chat.function("update_release", "Update selected fields of an existing release.", action_type="write", chain_callable=True, data_model=Release, event="freshservice-connector.update_release", effects=["update:release"])
async def update_release(ctx, params: UpdateReleaseParams) -> ActionResult:
    """Imperal action: update_release."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        item = await client.update_release(params.release_id, params.values)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_UPDATE_RELEASE_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=_to_release(item), summary="Release updated.")


def _to_article(item: dict) -> Article:
    return Article(
        article_id=str(item.get("id", "")), title=item.get("title", str(item.get("id", ""))),
        status=item.get("status", 0), raw=item,
    )


@chat.function("list_knowledge_articles", "List Knowledge Base articles on the connected Freshservice account.", action_type="read", chain_callable=True, data_model=ArticleList, event="freshservice-connector.list_knowledge_articles")
async def list_knowledge_articles(ctx, params: ListArticlesParams) -> ActionResult:
    """Imperal action: list_knowledge_articles."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        items = await client.list_solution_articles(per_page=params.per_page)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_LIST_ARTICLES_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=ArticleList(articles=[_to_article(i) for i in items]))


def _to_person(item: dict, kind: str) -> Person:
    name = f"{item.get('first_name', '')} {item.get('last_name', '')}".strip() or item.get("email", "")
    return Person(
        person_id=str(item.get("id", "")), title=name, name=name,
        email=item.get("email", item.get("primary_email", "")), kind=kind, raw=item,
    )


@chat.function("list_requesters", "List requesters (end users who raise tickets) on the connected Freshservice account.", action_type="read", chain_callable=True, data_model=PersonList, event="freshservice-connector.list_requesters")
async def list_requesters(ctx, params: ListPeopleParams) -> ActionResult:
    """Imperal action: list_requesters."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        items = await client.list_requesters(per_page=params.per_page)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_LIST_REQUESTERS_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=PersonList(people=[_to_person(i, "requester") for i in items]))


@chat.function("list_agents", "List agents (support staff) on the connected Freshservice account.", action_type="read", chain_callable=True, data_model=PersonList, event="freshservice-connector.list_agents")
async def list_agents(ctx, params: ListPeopleParams) -> ActionResult:
    """Imperal action: list_agents."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        items = await client.list_agents(per_page=params.per_page)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_LIST_AGENTS_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=PersonList(people=[_to_person(i, "agent") for i in items]))


@chat.function("list_table", "List records from any Freshservice v2 API path -- a generic passthrough for endpoints not covered by typed wrappers.", action_type="read", chain_callable=True, data_model=GenericPayload, event="freshservice-connector.list_table")
async def list_table(ctx, params: GenericGetParams) -> ActionResult:
    """Imperal action: list_table."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        data = await client.generic_get(params.path, params.query_params)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_GENERIC_GET_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=GenericPayload(payload=data))


@chat.function("create_record", "Create a new record on any Freshservice v2 API path -- a generic passthrough for endpoints not covered by typed wrappers.", action_type="write", chain_callable=True, data_model=GenericPayload, event="freshservice-connector.create_record", effects=["create:record"])
async def create_record(ctx, params: GenericWriteParams) -> ActionResult:
    """Imperal action: create_record."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        data = await client.generic_post(params.path, params.values)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_GENERIC_CREATE_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=GenericPayload(payload=data), summary="Record created.")


@chat.function("update_record", "Update a record on any Freshservice v2 API path -- a generic passthrough for endpoints not covered by typed wrappers.", action_type="write", chain_callable=True, data_model=GenericPayload, event="freshservice-connector.update_record", effects=["update:record"])
async def update_record(ctx, params: GenericWriteParams) -> ActionResult:
    """Imperal action: update_record."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        data = await client.generic_put(params.path, params.values)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_GENERIC_UPDATE_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=GenericPayload(payload=data), summary="Record updated.")


@chat.function("delete_record", "Permanently delete a record from any Freshservice v2 API path. Cannot be undone.", action_type="write", chain_callable=True, data_model=DeleteResult, event="freshservice-connector.delete_record", effects=["delete:record"])
async def delete_record(ctx, params: GenericDeleteParams) -> ActionResult:
    """Imperal action: delete_record."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        await client.generic_delete(params.path)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_GENERIC_DELETE_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=DeleteResult(deleted=True, path=params.path), summary="Record deleted.")


@chat.function("audit_instance_health", "Build one aggregated health report across the connected Freshservice account: open tickets/problems/changes/releases.", action_type="read", chain_callable=True, data_model=HealthAudit, event="freshservice-connector.audit_instance_health")
async def audit_instance_health(ctx, params: AuditHealthParams) -> ActionResult:
    """Imperal action: audit_instance_health."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        tickets = await client.list_tickets(per_page=100)
        problems = await client.list_problems(per_page=100)
        changes = await client.list_changes(per_page=100)
        releases = await client.list_releases(per_page=100)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_AUDIT_FAILED", retryable=exc.retryable)
    open_tickets = [t for t in tickets if t.get("status", 0) not in (4, 5)]
    open_problems = [p for p in problems if p.get("status", 0) not in (4,)]
    open_changes = [c for c in changes if c.get("status", 0) not in (3,)]
    open_releases = [r for r in releases if r.get("status", 0) not in (3,)]
    return ActionResult.success(data=HealthAudit(
        total_tickets=len(tickets), open_tickets=len(open_tickets),
        total_problems=len(problems), open_problems=len(open_problems),
        total_changes=len(changes), open_changes=len(open_changes),
        total_releases=len(releases), open_releases=len(open_releases),
        summary=(
            f"{len(open_tickets)} open tickets, {len(open_problems)} open problems, "
            f"{len(open_changes)} pending changes, {len(open_releases)} open releases."
        ),
    ))


def _to_asset(item: dict) -> Asset:
    return Asset(
        display_id=str(item.get("display_id", "")), title=item.get("name", str(item.get("display_id", ""))),
        name=item.get("name", ""), asset_tag=item.get("asset_tag", ""), raw=item,
    )


@chat.function("list_assets", "List Configuration Items (CMDB assets) on the connected Freshservice account.", action_type="read", chain_callable=True, data_model=AssetList, event="freshservice-connector.list_assets")
async def list_assets(ctx, params: ListAssetsParams) -> ActionResult:
    """Imperal action: list_assets."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        items = await client.list_assets(per_page=params.per_page)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_LIST_ASSETS_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=AssetList(assets=[_to_asset(i) for i in items]))


@chat.function("get_asset", "Read one asset (Configuration Item) in full by display id.", action_type="read", chain_callable=True, data_model=Asset, event="freshservice-connector.get_asset")
async def get_asset(ctx, params: AssetIdParams) -> ActionResult:
    """Imperal action: get_asset."""
    try:
        _, client = await _resolve_client(ctx, params.connection_id)
        item = await client.get_asset(params.display_id)
    except fc.FreshserviceError as exc:
        return ActionResult.error(str(exc), code="FRESHSERVICE_GET_ASSET_FAILED", retryable=exc.retryable)
    return ActionResult.success(data=_to_asset(item))
