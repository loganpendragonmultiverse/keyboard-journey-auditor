# Testing

Use Node 22 or newer. Run `npm test`, `npm run check`, `npm run build` and `npm audit --omit=dev`. There are no third-party runtime or build dependencies.

The original 13 automated tests cover explicit start and consent, safe evidence fields, Tab direction, possible traps, password focus, event and time limits, listener cleanup, and stopping when the session leaves its selected root. GitHub CI passed on Windows, macOS and Linux on 2026-10-15. CodeQL analysis and result upload passed.

## Browser acceptance

Serve the checkout locally and open `examples/exit-rehearsal.html` in a normal browser window. Use its synthetic controls to check Escape while focus is outside the root, a pointer press on an outside non-focusable area, programmatic focus departure, blur to the document body, and re-entry followed by Tab without another Start. Each case must leave collection stopped, with no new events after re-entry.

These checks passed in Microsoft Edge on Windows on 2026-10-15. Firefox and Safari browser acceptance had not been performed for 0.1.0. The macOS CI run verifies Node tests, not Safari behavior. No private browsing or real user content was used.

## 0.1.1 acceptance

Run all 16 unit tests, including forward/backward cycles and stationary/disrupted/mixed-direction counterexamples. Run the full existing native Node matrix and CodeQL, then test the actual unpacked tagged web ZIP and source ZIP. Follow [the native checklist](docs/native-acceptance.md); record genuine Edge, Firefox and Safari results separately from headless Chromium, Firefox and WebKit automation. An older-version result does not verify a new candidate. No private browsing or real user forms are involved.

The additional native CI jobs run the actual packaged web ZIP through preinstalled SafariDriver on macOS, Microsoft Edge WebDriver on Windows and geckodriver/Firefox on Linux. The original Node matrix remains intact. PR jobs use the exact PR head; tag jobs download the exact distribution built by that same tag workflow. Evidence records actual ZIP/script SHA-256, tested commit, native capabilities/OS, assertions and actual window dimensions. No browser/security setting is enabled or changed; unavailable preconfiguration fails the job. Native export tests click the real Export control and compare its Blob payload; OS save-dialog/download-directory behavior is not asserted by that check and needs separate observed evidence. Headless Playwright downloads remain supplementary.
