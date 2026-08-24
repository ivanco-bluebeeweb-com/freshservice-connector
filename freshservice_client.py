"""Thin REST client for Freshservice v2 API.

Auth: HTTP Basic (api_key, "X"). Same design lineage as Freshdesk.
"""
from __future__ import annotations

import base64
from typing import Any

import httpx


class FreshserviceError(RuntimeError):
    """A safe provider-facing error; never includes credentials."""

    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class FreshserviceClient:
    """REST client for Freshservice's v2 API."""

    def __init__(self, domain: str, api_key: str, *, timeout: float = 30.0):
        d = (domain or "").strip()
        if not d:
            raise FreshserviceError("Domain is required, e.g. 'acme.freshservice.com'.")
        d = d.replace("https://", "").replace("http://", "").rstrip("/")
        if not d.endswith(".freshservice.com") and "." not in d:
            d = f"{d}.freshservice.com"
        self.domain = d
        self.base_url = f"https://{d}/api/v2"
        if not api_key:
            raise FreshserviceError("API key is required.")
        token = base64.b64encode(f"{api_key}:X".encode()).decode()
        self._auth_header = f"Basic {token}"
        self.timeout = timeout

    async def request(self, method: str, path: str, *, params: dict | None = None,
                       json_body: dict | None = None) -> Any:
        url = f"{self.base_url}{path}"
        headers = {"Authorization": self._auth_header, "Content-Type": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.request(method, url, params=params, json=json_body, headers=headers)
        except httpx.RequestError as exc:
            raise FreshserviceError(f"Network error reaching Freshservice: {exc}", retryable=True) from exc
        if resp.status_code == 401:
            raise FreshserviceError("Authentication failed. Check your Freshservice API key.")
        if resp.status_code == 429:
            raise FreshserviceError("Rate limited by Freshservice. Try again shortly.", retryable=True)
        if resp.status_code >= 500:
            raise FreshserviceError(f"Freshservice server error ({resp.status_code}).", retryable=True)
        if resp.status_code >= 400:
            raise FreshserviceError(f"Freshservice request failed ({resp.status_code}): {resp.text[:300]}")
        if resp.status_code == 204 or not resp.content:
            return {}
        return resp.json()

    async def ping(self) -> dict:
        return await self.request("GET", "/agents", params={"per_page": 1})

    # -- Tickets (Incidents & Service Requests unified) ------------------------
    async def list_tickets(self, *, query: str = "", per_page: int = 30) -> list[dict]:
        params: dict[str, Any] = {"per_page": min(per_page, 100)}
        if query:
            data = await self.request("GET", "/tickets/filter", params={"query": f'"{query}"', **params})
        else:
            data = await self.request("GET", "/tickets", params=params)
        return data.get("tickets", [])

    async def get_ticket(self, ticket_id: str) -> dict:
        data = await self.request("GET", f"/tickets/{ticket_id}")
        return data.get("ticket", {})

    async def create_ticket(self, values: dict) -> dict:
        data = await self.request("POST", "/tickets", json_body=values)
        return data.get("ticket", {})

    async def update_ticket(self, ticket_id: str, values: dict) -> dict:
        data = await self.request("PUT", f"/tickets/{ticket_id}", json_body=values)
        return data.get("ticket", {})

    # -- Problems ---------------------------------------------------------------
    async def list_problems(self, *, per_page: int = 30) -> list[dict]:
        data = await self.request("GET", "/problems", params={"per_page": min(per_page, 100)})
        return data.get("problems", [])

    async def get_problem(self, problem_id: str) -> dict:
        data = await self.request("GET", f"/problems/{problem_id}")
        return data.get("problem", {})

    async def create_problem(self, values: dict) -> dict:
        data = await self.request("POST", "/problems", json_body=values)
        return data.get("problem", {})

    async def update_problem(self, problem_id: str, values: dict) -> dict:
        data = await self.request("PUT", f"/problems/{problem_id}", json_body=values)
        return data.get("problem", {})

    # -- Changes ------------------------------------------------------------
    async def list_changes(self, *, per_page: int = 30) -> list[dict]:
        data = await self.request("GET", "/changes", params={"per_page": min(per_page, 100)})
        return data.get("changes", [])

    async def get_change(self, change_id: str) -> dict:
        data = await self.request("GET", f"/changes/{change_id}")
        return data.get("change", {})

    async def create_change(self, values: dict) -> dict:
        data = await self.request("POST", "/changes", json_body=values)
        return data.get("change", {})

    async def update_change(self, change_id: str, values: dict) -> dict:
        data = await self.request("PUT", f"/changes/{change_id}", json_body=values)
        return data.get("change", {})

    # -- Releases -----------------------------------------------------------
    async def list_releases(self, *, per_page: int = 30) -> list[dict]:
        data = await self.request("GET", "/releases", params={"per_page": min(per_page, 100)})
        return data.get("releases", [])

    async def get_release(self, release_id: str) -> dict:
        data = await self.request("GET", f"/releases/{release_id}")
        return data.get("release", {})

    async def create_release(self, values: dict) -> dict:
        data = await self.request("POST", "/releases", json_body=values)
        return data.get("release", {})

    async def update_release(self, release_id: str, values: dict) -> dict:
        data = await self.request("PUT", f"/releases/{release_id}", json_body=values)
        return data.get("release", {})

    # -- Assets (CMDB) --------------------------------------------------------
    async def list_assets(self, *, per_page: int = 30) -> list[dict]:
        data = await self.request("GET", "/assets", params={"per_page": min(per_page, 100)})
        return data.get("assets", [])

    async def get_asset(self, display_id: str) -> dict:
        data = await self.request("GET", f"/assets/{display_id}")
        return data.get("asset", {})

    # -- Knowledge base -------------------------------------------------------
    async def list_solution_articles(self, *, per_page: int = 30) -> list[dict]:
        data = await self.request("GET", "/solutions/articles", params={"per_page": min(per_page, 100)})
        return data if isinstance(data, list) else data.get("articles", [])

    # -- People -----------------------------------------------------------------
    async def list_requesters(self, *, per_page: int = 30) -> list[dict]:
        data = await self.request("GET", "/requesters", params={"per_page": min(per_page, 100)})
        return data.get("requesters", [])

    async def list_agents(self, *, per_page: int = 30) -> list[dict]:
        data = await self.request("GET", "/agents", params={"per_page": min(per_page, 100)})
        return data.get("agents", [])

    # -- Generic passthrough ------------------------------------------------
    async def generic_get(self, path: str, params: dict | None = None) -> Any:
        return await self.request("GET", path, params=params)

    async def generic_post(self, path: str, values: dict) -> Any:
        return await self.request("POST", path, json_body=values)

    async def generic_put(self, path: str, values: dict) -> Any:
        return await self.request("PUT", path, json_body=values)

    async def generic_delete(self, path: str) -> None:
        await self.request("DELETE", path)
