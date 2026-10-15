# Testing

Node tests exercise explicit consent, idle behavior, Tab direction and focus order, forbidden value/text getters, stationary-trap sequences, password stop, listener/timer teardown, Escape, visibility/blur/time boundaries, event caps, redacted tags/roles, report isolation, clearing and test-root exit. Browser acceptance must also exercise the bundled fixture and verify the network/privacy boundary before public release.

`npm test`; `npm run check`; `npm run build`; `npm audit --omit=dev`.

Exact execution results and environment evidence are supplied with the RC bundle. CI definitions are not proof of completed remote CI. Public release remains gated on successful remote checks and maintainer security review.

## Candidate evidence — 2026-10-15

Windows Node: initial eight tests passed, recorder line coverage 91.54%, branch coverage 85.51% (a ninth cycle/modifier regression was then added); syntax checks and static build passed. Edge loopback browser rehearsal: consent refusal passed, value-free focus transitions observed, synthetic typed contents absent from evidence, intentional stationary trap identified with sequences 3/4/5, Escape stopped recording, deliberate JSON export succeeded. Export SHA-256: cf4492330a0e05d50814ba419472488db0971e88e7cb6b135910cdccaffdac3b.

Linux container and remote CI results are recorded in the release-candidate evidence packet. macOS and Firefox remain unverified unless the remote checks explicitly establish them. No real backup or private browsing was used.


## Independent-review regression acceptance

The root-exit regressions cover outside pointer presses, programmatic focus departure, blur to the document body, global Escape, listener teardown and re-entry without a fresh Start. No outside values or text are read. Serve the source checkout and open examples/exit-rehearsal.html to exercise those routes in a real browser. Start from the external button and press Escape to verify document-wide cancellation; start again, enter the root, click the outside non-focusable paragraph, and confirm re-entry stays stopped; repeat with the programmatic-focus and blur buttons.


## Review-fix verification — 2026-10-15

Independent-review corrections: 13 Node tests passed. Added pointer/programmatic exit, blur-to-body, global Escape, listener teardown and fresh-start regressions. The source-only examples/exit-rehearsal.html fixture supports real-browser acceptance.
