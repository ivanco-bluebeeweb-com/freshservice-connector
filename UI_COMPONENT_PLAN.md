# Freshservice Connector — UI component plan

Источники: `Docs/session-notes/UI_COMPONENT_VOCABULARY.md`, `UI_INTERFACE_STANDARD.md`,
`concepts/panels.md`. Основано на функционале `freshservice-connector`.

## 0. Разница с IDEAL_ONBOARDING.md
Идеал предполагает единую форму домен+ключ с мгновенной проверкой. Реализация делает
это тем же способом, что и freshdesk-connector в портфеле — `connect_freshservice`
сам выполняет пробный запрос перед сохранением через стандартный `ui.Form`.

## 1. Компоненты

| Экран | Примитивы | Почему именно эти |
|---|---|---|
| Sidebar (left) | `ui.Stack`(v) + `ui.Text`(domain label) + `ui.Divider` + `ui.Button`×7 (Tickets/Problems/Changes/Releases/Assets/Knowledge/People) + `ui.Button`("App settings") | Без карточек, без дублирования инструкций. |
| Connect form (not connected) | `ui.Form` + labelled `ui.Input`×2 (domain, api_key) | Минимум полей — Freshservice требует только домен и ключ. |
| Help panel | `ext.panel`(center_overlay=True) + `ui.Text`(объяснение unified Ticket model + где взять API-ключ) | Единственное место с инструкциями подключения. |
| Tickets panel (center, `center_overlay=True`) | `ui.Header` + `ui.Input`(query filter) + `ui.DataTable`(id/subject/type/status/priority) + create `ui.Form` | Единый список для Incident+Service Request (различаются полем type). |
| Problems / Changes / Releases panels | Аналогичная структура `ui.DataTable` + create `ui.Form` | Единый паттерн по всем ITSM-объектам. |
| Assets panel | `ui.DataTable`(name/asset_tag/type) | Просмотр CMDB-эквивалента Freshservice. |
| Knowledge panel | `ui.DataTable`(title/status) | Просмотр статей базы знаний. |
| People panel | `ui.DataTable`(requesters) + `ui.DataTable`(agents) | Просмотр заявителей и агентов для контекста назначения. |
| Generic passthrough | `ui.Form`(endpoint path + query) → `ui.DataTable` | Доступ к любому v2-эндпоинту, не покрытому типизированными обёртками. |
| App settings | `ext.panel`(slot=center) + список подключений + Disconnect | Единственное место с disconnect. |

## 2. Соответствие UI_INTERFACE_STANDARD.md
- Все инпуты — с лейблами, плейсхолдеры контекстные (`acme.freshservice.com`, не
  generic "domain").
- Форма подключения растянута на всю ширину левого сайдбара, содержимое растянуто
  внутри неё.
- Инструкции подключения — только в help-панели (модалке), не дублируются в сайдбаре.
