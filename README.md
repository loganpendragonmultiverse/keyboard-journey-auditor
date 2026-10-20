# Keyboard Journey Auditor

Record deliberate, value-free focus and Tab evidence on owned test pages.

MIT licensed. Runs locally without an account or external service. See [GitHub Releases](https://github.com/loganpendragonmultiverse/keyboard-journey-auditor/releases) for downloads.

## Three-minute start

```sh
npm test
npm run check
npm run build
python -m http.server 8765 --bind 127.0.0.1
# Open http://127.0.0.1:8765/ in a normal window.
# Confirm both statements, Start, Tab through the fixture, Escape, review, Export.
```

For a downloaded web ZIP, serve the unpacked folder with the Python command above and open its index page. The npm checks require the complete source checkout.

## Features

A local static demonstration plus an embeddable JavaScript recorder that a developer explicitly installs in a selected test root. Each session requires an owned-test-page and normal-window attestation. Anonymous element slots, safe tag/role categories, Tab direction, default-prevention evidence, elapsed time and sequence numbers support focus-order review and possible-trap evidence.

## Privacy and safe operation

Idle by default; explicit start only. Never reads or exports text, input values, labels, names, IDs, page URLs, clipboard data, passwords or typed contents. Only Tab and Escape are interpreted; other keys are discarded. Password focus within the selected root, any focus departure or pointer press outside that root, Escape anywhere in the document, window blur, page hiding, page departure, event limit and timeout stop collection and remove listeners. Re-entry cannot resume a stopped session without a fresh Start. Outside targets are checked only for root membership; no outside text, values or typed contents are collected. Evidence stays in memory until a user reviews and exports it; clearing discards it. No telemetry, data uploads, persistent storage, permission prompts or continuous background collection. Serving the application loads its static assets; the recorder does not send captured evidence to a server.

## Boundaries

No browser extension, cross-origin inspection, automatic site crawling, private browsing inspection, screen-reader audit, WCAG certification, shadow-root traversal or iframe traversal. Private mode cannot reliably be detected from a webpage: users must attest a normal window, and private browsing use is unsupported. Only instrument developer-owned synthetic test pages. The host page can already observe its own events; this library is not a security sandbox against a hostile host. Potential stationary focus and two-element cycles are heuristics; modal focus loops may be intentional and missed/false-positive traps are possible. Session limits: 500 events and five minutes. A pending Tab is sampled after 80 ms; slower dynamic focus updates may be missed.

## Development and support

Requires a modern browser with ES modules; development commands require Node 22+. No third-party runtime or build dependencies. See [DEVELOPMENT.md](DEVELOPMENT.md), [TESTING.md](TESTING.md), [SECURITY.md](SECURITY.md), and [CHANGELOG.md](CHANGELOG.md). Pull requests receive maintainer review; no contribution or release merges automatically. Maintenance is on demand, with no service-level commitment.

## 0.1.1: more precise cycle evidence

Two-element cycle warnings require four contiguous same-direction Tab transitions alternating between two distinct slots. This avoids labeling stationary focus followed by one move as a two-element cycle; stationary-focus evidence remains separate. The web ZIP now includes `examples/exit-rehearsal.html` and [native-browser acceptance instructions](docs/native-acceptance.md). Serve these over local HTTP just like the main app.
