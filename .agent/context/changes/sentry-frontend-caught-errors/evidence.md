# Evidence

Comparison base: `2bea126e43680f4cb59cf8c5d700cbd45a4b3696`. Only frontend delivery code, its tests and change documentation are modified.

## Diagnosis

- Production public asset `/assets/index-D_od0K4V.js` contains the correct `linksifty-web` DSN and `enabled: true`; its entrypoint calls the initializer. The page response has no CSP header blocking ingestion. Public backend health200 is availability only, not SDK proof.
- Invalid input reproduction against the local API returned422/url_parsing. The production screenshot alone does not prove a technical crash or broken monitoring.
- Shared api/watchActivity throw failures that their UI callers catch. Global handlers cannot capture those caught failures. This is the supported reporting defect; the fix preserves the expected422 behavior.

## Automated regression evidence

With original API code:6 failures,13 passes in the new suite. With corrected code:19/19 pass. Only network delivery is faked; real SDK initialization, filtering and memory envelopes are exercised. A separate SDK-instance fault is injected to verify outage safety.

| Regression | Observable assertion | Broken behavior it detects |
| --- | --- | --- |
| API/SSE503 (2 cases) | Original status remains503; one sanitized event | Caught5xx disappears from monitoring |
| API/SSE401,403,409,422 (8 cases) | Original denial retained; zero events | Normal access/validation outcomes flood Sentry |
| API/SSEnetwork failure (2 cases) | Same Error identity rethrown; one sanitized event | Fetch outage swallowed by UI |
| API/SSEAbortError (2 cases) | Same cancellation; zero events | User navigation/cancellation reported as failure |
| Malformed progress | Parsing failure reports once; reader cancellation happens | Broken stream data invisible or cleanup lost |
| Stream denial |403 and zero events | Revoked access treated as technical failure |
| API success | Same data and zero events | Monitoring changes successful behavior |
| SDK instance failure | Original request error preserved | Monitoring outage replaces product error |
| Malformed API JSON | SyntaxError plus one event | Missing await escapes reporting boundary |

All frontend suites:112 tests pass. Existing SDK privacy suite:5/5 pass. Oxlint and TypeScript/Vite production build pass. No backend files/dependencies/configuration changed. Existing pinned agent-toolkit check is recorded separately; Graft remained unavailable, so focused source/caller inspection was used.

## Sentry ingestion probe

One synthetic error passed through `monitoringOptions` and the real frontend SDK in an isolated Node process with the existing public web DSN. Filtered output contains technical data only. MCP search by exact event ID confirms `linksifty-web`, `test`, event `6b10529bc6bf40a7b0d3ec59072c4760`. No user sessions or content were used. This is not claimed as a browser-to-Sentry test or backend verification.

## Review and publication

Fresh independent reviewer `/root/linksifty_frontend_reporting_review`: approve for frontend source integration, independently19/19 tests. [Review report](reviews/implementation-review.md). Publication result is recorded in the final handoff after push. Native Safari diagnostics were interrupted by the user's browser activity; an isolated read-only IAB tab does not prove page SDK globals or delivery. No blockers or settings were disabled to force a result.

## Completed publication

Source: `d6590a5648885585269010ffe9b97e946d3eb64c` on main. [CI](https://github.com/fifmazurkiewicz/linksifty/actions/runs/41752580193) and [Secrets](https://github.com/fifmazurkiewicz/linksifty/actions/runs/41752580397) completed successfully. Public deployment now serves `/assets/index-Cda6QEGH.js` with the unexpected-failure reporting guard and expected web DSN.

The synthetic adapter probe is visible as [LINKSIFTY-WEB-1](https://fmazurkiewicz.sentry.io/issues/LINKSIFTY-WEB-1), environment test, one event, zero users. Only frontend reporting was changed. The user's Safari transport and backend activation are not claimed as verified. This final record update does not change runtime code.
