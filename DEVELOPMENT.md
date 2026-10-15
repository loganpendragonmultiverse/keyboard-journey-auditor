# Development

Scope: A local static demonstration plus an embeddable JavaScript recorder that a developer explicitly installs in a selected test root. Each session requires an owned-test-page and normal-window attestation. Anonymous element slots, safe tag/role categories, Tab direction, default-prevention evidence, elapsed time and sequence numbers support focus-order review and possible-trap evidence.

Idle by default; explicit start only. Never reads or exports text, input values, labels, names, IDs, page URLs, clipboard data, passwords or typed contents. Only Tab and Escape are interpreted; other keys are discarded. Password focus within the selected root, any focus departure or pointer press outside that root, Escape anywhere in the document, window blur, page hiding, page departure, event limit and timeout stop collection and remove listeners. Re-entry cannot resume a stopped session without a fresh Start. Outside targets are checked only for root membership; no outside text, values or typed contents are collected. Evidence stays in memory until a user reviews and exports it; clearing discards it. No telemetry, data uploads, persistent storage, permission prompts or continuous background collection. Serving the application loads its static assets; the recorder does not send captured evidence to a server.

No browser extension, cross-origin inspection, automatic site crawling, private browsing inspection, screen-reader audit, WCAG certification, shadow-root traversal or iframe traversal. Private mode cannot reliably be detected from a webpage: users must attest a normal window, and private browsing use is unsupported. Only instrument developer-owned synthetic test pages. The host page can already observe its own events; this library is not a security sandbox against a hostile host. Potential stationary focus and two-element cycles are heuristics; modal focus loops may be intentional and missed/false-positive traps are possible. Session limits: 500 events and five minutes. A pending Tab is sampled after 80 ms; slower dynamic focus updates may be missed.

Run `npm test`, `npm run check`, `npm run build` and `npm audit --omit=dev`. Tests use Node built-ins; the distributable is static HTML/CSS/ES modules.

## Release process

Use a branch and pull request for changes. Run the test matrix and CodeQL, resolve review conversations, and let the maintainer make the final merge decision. CI workflows use read-only permissions and pinned actions.

For a release, keep the package version and changelog in agreement, create an annotated semantic-version tag, and use that tag's successful release build. Verify the downloadable files against SHA256SUMS before publishing a GitHub release. Never bypass repository protections or publish artifacts from a different commit.
