# Testing

Use Node 22 or newer. Run `npm test`, `npm run check`, `npm run build` and `npm audit --omit=dev`. There are no third-party runtime or build dependencies.

The 13 automated tests cover explicit start and consent, safe evidence fields, Tab direction, possible traps, password focus, event and time limits, listener cleanup, and stopping when the session leaves its selected root. GitHub CI passed on Windows, macOS and Linux on 2026-10-15. CodeQL analysis and result upload passed.

## Browser acceptance

Serve the checkout locally and open `examples/exit-rehearsal.html` in a normal browser window. Use its synthetic controls to check Escape while focus is outside the root, a pointer press on an outside non-focusable area, programmatic focus departure, blur to the document body, and re-entry followed by Tab without another Start. Each case must leave collection stopped, with no new events after re-entry.

These checks passed in Microsoft Edge on Windows on 2026-10-15. Firefox and Safari browser acceptance have not been performed. The macOS CI run verifies Node tests, not Safari behavior. No private browsing or real user content was used.
