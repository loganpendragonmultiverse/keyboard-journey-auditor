# Changelog

## 0.1.1 — 2026-10-20

- Require four contiguous alternating transitions for two-element cycle evidence; stationary samples followed by a move no longer produce that cycle warning.
- Cover backward cycles, disrupted transitions and direction changes with regressions.
- Include the synthetic root-departure rehearsal and native-browser acceptance instructions in the web distribution.
- Keep the rehearsal controls usable on narrow screens with wrapped JSON and a stable scrollable report area.
- Make the Blur rehearsal release the actual focused element within its owned root, including Safari button clicks that do not focus the button.

## 0.1.0 — 2026-10-15

- Added a local static demonstration plus an embeddable JavaScript recorder that a developer explicitly installs in a selected test root. Each session requires an owned-test-page and normal-window attestation. Anonymous element slots, safe tag/role categories, Tab direction, default-prevention evidence, elapsed time and sequence numbers support focus-order review and possible-trap evidence.
- Stop sessions on pointer or programmatic root departure, blur-to-body and document-wide Escape; prevent re-entry from resuming collection without a fresh Start.
- Added synthetic examples, regression tests, usage documentation and MIT licensing.
- Added version-checked release packaging with SHA-256 checksums.
