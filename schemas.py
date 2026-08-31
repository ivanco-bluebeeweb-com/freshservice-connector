"""Pydantic input contracts and SDL result entities for Freshservice Connector."""
from __future__ import annotations

from imperal_sdk import sdl
from pydantic import BaseModel, Field


class NoParams(BaseModel):
    pass


class ConnectionRefParams(BaseModel):
    connection_id: str = Field("", description="Optional saved Freshservice connection ID. Omit to use the first connected account.")


class ConnectFreshserviceParams(BaseModel):
    label: str = Field("", description="Friendly account label, e.g. 'Acme IT'.")
    domain: str = Field(..., description="Freshservice domain, e.g. 'acme.freshservice.com' or just 'acme'.")
    api_key: str = Field(..., description="Freshservice account API key (Profile Settings > API Key).")


class DisconnectFreshserviceParams(ConnectionRefParams):
    connection_id: str = Field(..., description="Saved Freshservice connection ID to remove from Imperal.")


class TicketIdParams(ConnectionRefParams):
    ticket_id: str = Field(..., description="Ticket display id.")


class ListTicketsParams(ConnectionRefParams):
    query: str = Field("", description="Optional Freshservice filter query, e.g. \"status:2\" or \"priority:3\".")
    per_page: int = Field(30, description="Max records to return (up to 100).")


class CreateTicketParams(ConnectionRefParams):
    values: dict = Field(..., description="Ticket field values, e.g. {'subject': '...', 'description': '...', 'email': 'user@acme.com', 'priority': 1, 'status': 2, 'type': 'Incident'}.")


class UpdateTicketParams(TicketIdParams):
    values: dict = Field(..., description="Ticket field values to update.")


class ProblemIdParams(ConnectionRefParams):
    problem_id: str = Field(..., description="Problem display id.")


class ListProblemsParams(ConnectionRefParams):
    per_page: int = Field(30, description="Max records to return (up to 100).")


class CreateProblemParams(ConnectionRefParams):
    values: dict = Field(..., description="Problem field values, e.g. {'subject': '...', 'description': '...'}.")


class UpdateProblemParams(ProblemIdParams):
    values: dict = Field(..., description="Problem field values to update.")


class ChangeIdParams(ConnectionRefParams):
    change_id: str = Field(..., description="Change display id.")


class ListChangesParams(ConnectionRefParams):
    per_page: int = Field(30, description="Max records to return (up to 100).")


class CreateChangeParams(ConnectionRefParams):
    values: dict = Field(..., description="Change field values, e.g. {'subject': '...', 'description': '...', 'planned_start_date': '...'}.")


class UpdateChangeParams(ChangeIdParams):
    values: dict = Field(..., description="Change field values to update.")


class ReleaseIdParams(ConnectionRefParams):
    release_id: str = Field(..., description="Release display id.")


class ListReleasesParams(ConnectionRefParams):
    per_page: int = Field(30, description="Max records to return (up to 100).")


class CreateReleaseParams(ConnectionRefParams):
    values: dict = Field(..., description="Release field values, e.g. {'subject': '...', 'description': '...'}.")


class UpdateReleaseParams(ReleaseIdParams):
    values: dict = Field(..., description="Release field values to update.")


class AssetIdParams(ConnectionRefParams):
    display_id: str = Field(..., description="Asset display id.")


class ListAssetsParams(ConnectionRefParams):
    per_page: int = Field(30, description="Max records to return (up to 100).")


class ListArticlesParams(ConnectionRefParams):
    per_page: int = Field(30, description="Max records to return (up to 100).")


class ListPeopleParams(ConnectionRefParams):
    per_page: int = Field(30, description="Max records to return (up to 100).")


class GenericGetParams(ConnectionRefParams):
    path: str = Field(..., description="Exact Freshservice v2 API path, e.g. '/tickets' or '/agents'.")
    query_params: dict = Field(default_factory=dict, description="Optional query string parameters.")


class GenericWriteParams(ConnectionRefParams):
    path: str = Field(..., description="Exact Freshservice v2 API path, e.g. '/tickets'.")
    values: dict = Field(..., description="Field name/value pairs for the request body.")


class GenericDeleteParams(ConnectionRefParams):
    path: str = Field(..., description="Exact Freshservice v2 API path including the record id, e.g. '/tickets/123'.")


class AuditHealthParams(ConnectionRefParams):
    pass


class FreshserviceConnection(sdl.Entity):
    id: str = ""
    title: str = ""
    label: str = ""
    domain: str = ""
    connected: bool = True


class ConnectionList(sdl.Entity):
    id: str = "connections"
    title: str = "Freshservice connections"
    connections: list[FreshserviceConnection] = []


class DeleteResult(sdl.Entity):
    id: str = "delete"
    title: str = "Delete result"
    deleted: bool = True


class Ticket(sdl.Entity):
    id: str = ""
    ticket_id: str = ""
    title: str = ""
    subject: str = ""
    status: int = 0
    priority: int = 0
    type: str = ""
    raw: dict = {}


class TicketList(sdl.Entity):
    id: str = "tickets"
    title: str = "Tickets"
    tickets: list[Ticket] = []


class Problem(sdl.Entity):
    id: str = ""
    problem_id: str = ""
    title: str = ""
    subject: str = ""
    status: int = 0
    raw: dict = {}


class ProblemList(sdl.Entity):
    id: str = "problems"
    title: str = "Problems"
    problems: list[Problem] = []


class ChangeRequest(sdl.Entity):
    id: str = ""
    change_id: str = ""
    title: str = ""
    subject: str = ""
    status: int = 0
    raw: dict = {}


class ChangeRequestList(sdl.Entity):
    id: str = "changes"
    title: str = "Changes"
    changes: list[ChangeRequest] = []


class Release(sdl.Entity):
    id: str = ""
    release_id: str = ""
    title: str = ""
    subject: str = ""
    status: int = 0
    raw: dict = {}


class ReleaseList(sdl.Entity):
    id: str = "releases"
    title: str = "Releases"
    releases: list[Release] = []


class Asset(sdl.Entity):
    id: str = ""
    display_id: str = ""
    title: str = ""
    name: str = ""
    asset_tag: str = ""
    raw: dict = {}


class AssetList(sdl.Entity):
    id: str = "assets"
    title: str = "Assets"
    assets: list[Asset] = []


class Article(sdl.Entity):
    id: str = ""
    article_id: str = ""
    title: str = ""
    status: int = 0
    raw: dict = {}


class ArticleList(sdl.Entity):
    id: str = "articles"
    title: str = "Knowledge base articles"
    articles: list[Article] = []


class Person(sdl.Entity):
    id: str = ""
    person_id: str = ""
    title: str = ""
    name: str = ""
    email: str = ""
    raw: dict = {}


class PersonList(sdl.Entity):
    id: str = "people"
    title: str = "People"
    people: list[Person] = []


class GenericPayload(sdl.Entity):
    id: str = "generic"
    title: str = "Generic response"
    raw: dict = {}


class HealthAudit(sdl.Entity):
    id: str = "audit"
    title: str = "Freshservice health audit"
    open_ticket_count: int = 0
    open_problem_count: int = 0
    open_change_count: int = 0
    open_release_count: int = 0
    raw: dict = {}
