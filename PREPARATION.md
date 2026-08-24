# Freshservice Connector — Preparation

**Version:** 0.1.0 (planning)
**Date:** 2026-08-24
**Related task:** BBW Imperal Apps #2446
**Scope decision:** maximum feasible capability against the publicly documented
Freshservice v2 REST API (per standing "максимальный функционал" instruction).

## 1. App passport

**Name:** Freshservice Connector
**One-line purpose:** Connect your own Freshservice ITSM account to manage Tickets
(Incidents & Service Requests), Problems, Changes, Releases, Assets (CMDB), and
Knowledge Base articles through the Freshservice v2 REST API.

**What it is not:**
- Not the Freshdesk connector — Freshservice ITSM scope (Problems/Changes/Releases/
  Assets) is not present in Freshdesk at all; this is a distinct product/API.
- Not a Freshservice Orchestration/workflow-automation replacement.
- Not an Asset-discovery/agent-install tool — reads/writes asset *records*, does not
  run discovery probes.

## 2. Human problem

> An IT service desk agent using Freshservice needs to triage tickets, look up asset
> ownership, track a change through approval, or get a daily open-ticket snapshot —
> without switching to the Freshservice web console.

### Personas
| Persona | Trigger | Value |
|---|---|---|
| Service desk agent | "What's the status of ticket #4521?" | Instant lookup + reply without leaving chat |
| ITSM admin | Needs to close a batch of resolved incidents | Ticket update wrapper, one call per ticket or bulk via filter+loop |
| Change manager | Wants changes awaiting approval | list_changes filtered by status |
| Asset manager | Needs to check which asset a ticket references | get_asset / list_assets |
| Ops lead | Wants a daily open-ticket/problem/change snapshot | audit_instance_health value-add report |

## 3. Auth & connection model

HTTP Basic Auth: API key as username, any string as password (Freshservice/Freshdesk
convention). Validated with a real `GET /api/v2/agents/me`-style call before saving.

## 4. Scope of "maximum functionality" for v1

- Connection lifecycle: connect/disconnect/list_connections (multi-account support).
- Tickets (incidents & service requests unified): list (with query filter), get,
  create, update — covers both ticket types via the `type` field.
- Problems: list, get, create, update.
- Changes: list, get, create, update.
- Releases: list, get, create, update.
- Assets (CMDB): list, get.
- Knowledge base articles: list.
- Requesters & Agents: list, get (for assignment/lookup context).
- Generic passthrough: list/get/create/update/delete against any Freshservice v2
  endpoint not covered by typed wrappers.
- audit_instance_health: open ticket/problem/change counts in one call.

## 5. Non-goals for v1

- No Orchestration workflow triggers.
- No SLA policy CRUD (read via ticket fields is sufficient for v1).
- No asset discovery/agent management.
