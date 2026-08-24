# Freshservice Connector — Connector Discovery

**Discovery date:** 2026-08-24
**Release scope:** maximum functionality against the publicly documented Freshservice
v2 REST API (per standing "максимальный функционал" instruction).
**Related task:** BBW Imperal Apps #2446.

## 1. What Freshservice actually is

Freshservice (by Freshworks) is a cloud-native ITSM platform covering the classic
ITIL processes: Incident, Problem, Change, Release, Service Catalog (Service Requests),
Assets/CMDB, and Knowledge Base — plus a lighter, more modern onboarding/config
surface than legacy tools like BMC Remedy or Ivanti ISM. It exposes a clean, well
documented **REST API v2** at `https://<domain>.freshservice.com/api/v2/`.

## 2. Chosen integration surface

**Freshservice REST API v2**:
- **Auth**: HTTP Basic Auth with the account API key as username and any string
  (commonly `X`) as password — the same pattern as Freshdesk (same parent company,
  same API design lineage already in this portfolio via freshdesk-connector). No
  OAuth2 required for v2.
- **Core resources**:
  - `/api/v2/tickets` — Incidents AND Service Requests are unified under "Tickets"
    in Freshservice (distinguished by `type` field: "Incident" or "Service Request").
  - `/api/v2/problems` — Problem records.
  - `/api/v2/changes` — Change records.
  - `/api/v2/releases` — Release records.
  - `/api/v2/assets` — CMDB assets (Freshservice's CI equivalent).
  - `/api/v2/solutions/articles` — Knowledge base articles (under solutions/categories/folders/articles hierarchy).
  - `/api/v2/requesters` — End users who raise tickets.
  - `/api/v2/agents` — Support staff.
- **Pagination**: page-based (`page`, `per_page` up to 100), Link headers for next page.
- **Filtering**: query params per-field for tickets (`filter=`, `query=` with encoded
  Freshservice query syntax), and a dedicated `/api/v2/tickets/filter?query=` endpoint
  for advanced search.

## 3. What "maximum functionality" means here

Full CRUD on Tickets (incidents + service requests unified), Problems, Changes,
Releases, Assets, Knowledge articles, plus requester/agent lookup and a generic
passthrough for any endpoint not covered by typed wrappers, matching the depth already
delivered for ServiceNow/JSM/BMC Helix/Ivanti in this same category.

## 4. Precedents already in this portfolio

`freshdesk-connector` already exists and shares the same underlying API design
(Basic Auth with API key, page-based pagination, same JSON conventions) since
Freshservice and Freshdesk are sibling Freshworks products — this reduces discovery
risk substantially; the ticket/problem/change/release/asset resource model is
Freshservice-specific ITSM scope that Freshdesk (a helpdesk-only product) does not
cover.
