# UI dependency migration

Checked September 7, 2026.

| Component | Version / configuration |
|---|---|
| HTMX | 4.0.0, enabled through `FastHTML(htmx4=True)` |
| python-fasthtml | 0.14.13 |
| fastcore | 2.2.22 |
| fastlite | 0.2.4 |
| MonsterUI | 1.0.47, with its supported FrankenUI/DaisyUI assets |
| Pico CSS | Disabled; the app uses MonsterUI. The current Pico release checked was 2.1.1. |

HTMX's former experimental/next line reached 4.0.0 on August 28, 2026. Its website points to that release while npm's `latest` tag remains on 2.x. The app therefore opts into 4 explicitly. [HTMX announcement](https://four.htmx.org/announcements/2026-08-28-htmx-4.0.0-is-released), [FastHTML](https://pypi.org/project/python-fasthtml/0.14.13/), [MonsterUI](https://pypi.org/project/monsterui/1.0.47/), [Pico documentation](https://picocss.com/docs)

## Compatibility changes

- FastHTML's HTMX 4 configuration uses `-` as the event/modifier separator. `static/app.js` derives event names from that setting and reads the new request/swap context.
- Hyperscript initialization is connected to HTMX's current `onLoad` API. The app does not load HTMX 2 or the htmx-2-compat extension.
- Explicit `hx-include` fields carry the workspace ID. The old mutable request-parameters hook is removed.
- File upload uses the current MonsterUI UploadZone API with one file input. Fetch-based uploads show an indeterminate busy indicator rather than an XHR percentage.
- Swap handling refreshes generation-button state and workspace counts. Delete actions explicitly render the updated list, rather than depending on the old empty-response/OOB behavior.
- Recording cleanup is registered once and uses resolved swap targets. The recording status element no longer uses the browser's built-in `window.status` property.
- Composite cards avoid a second layer of body padding. FastCore/FastLite compatibility fixes keep required model fields before defaults and store the inserted user's integer ID in the session.

## Theme and validation

The light theme in `css.py` supplies warm background, text, card, border, focus, and accent variables for MonsterUI. Status/error colors retain their meanings. Pico is kept off to avoid competing global component styles.

Application smoke tests use an isolated database and make no model calls. Browser checks exercise the real HTMX 4 runtime, desktop/mobile navigation, uploads, editing, and deletion. Existing report-component tests remain independent of the UI stack. Tests against a copy of the existing database confirm that the updated model definitions preserve its logical table contents.

The report-component schema is still a separate feature; this UI dependency migration does not wire that new report shape into the existing database or enable an AI provider.
