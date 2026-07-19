# MCP contracts

MCP (Model Context Protocol) is the external integration layer of
RewardsPilotOS (MASTER_SPEC ch. 22). Contracts here define the shapes every
MCP client speaks: `MCPRequest`, `MCPResponse`, `MCPError` in `base.py`.

## Routing rule (binding)

Internal tools execute business logic and computation (Rule Engine, Graph
Engine, Reward Calculator, Knowledge Search, Memory, Portfolio). **MCP is
selected only when external capabilities or live information are required**
(live issuer pages, browser automation, email, calendar, flight/hotel
search). The Planner owns this routing and keeps it deterministic wherever
possible. MCP servers never calculate rewards, make recommendations, execute
business rules, store user memory, or perform graph optimization.

## Clients and sprint status

| Client | Purpose | Sprint status |
|---|---|---|
| BrowserMCPClient | Live issuer page retrieval | Stub — typed `pending_integration` errors |
| PlaywrightMCPClient | Browser automation (navigate, extract, screenshot) | Stub — typed `pending_integration` errors |
| EmailMCPClient | Reward statements, promo mail (with consent) | Interface only |
| CalendarMCPClient | Expiry/fee/promotion reminders | Interface only |
| FlightSearchMCPClient | Award availability, pricing | Interface only |
| HotelSearchMCPClient | Hotel availability, cash vs points | Interface only |

Real servers are wired only if the final day finishes early; live
integrations are the only deferred piece (roadmap-flagged, BUILD_SPEC §8).

## Error handling

Failures are structured (`MCPError`: code, message, retryable). The Planner
decides whether to retry, use cached/indexed knowledge with reduced
confidence, or tell the user. Secrets are handled per server and are never
exposed to the LLM.
