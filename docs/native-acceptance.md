# Native browser acceptance

Use a normal, non-private browser window on an owned synthetic page. Record browser name/version, operating system/version, exact tested commit and (for release acceptance) downloaded ZIP SHA-256. Chromium and WebKit automation are additional evidence, not Edge or Safari results. Preserve the historical Edge 0.1.0 result separately.

Unpack the web ZIP, run `python -m http.server 8765 --bind 127.0.0.1` inside it, and open `http://127.0.0.1:8765/`. The source ZIP can run the same pages from its root. Do not use file:// because the app uses ES modules. No npm install is needed for browser use.

1. Before consent, press Tab and type synthetic text. The report must remain idle. Start without both confirmations must display an actionable error.
2. Confirm both statements and Start. Focus moves inside the fixture. Tab forward, then Shift+Tab backward, waiting at least 100 ms between keys. Escape stops. Review the JSON: generated slots, directions and sequence numbers appear; typed contents, labels, DOM IDs and page URLs do not.
3. Before a fresh Start, enable the deliberately broken trap. Reach Trap fixture and press Tab three times without moving focus. Escape stops; stationary-focus evidence points to the events. Four alternating transitions between two controls may produce a short-focus-cycle; the tool does not claim every modal loop is a defect.
4. Export after stopping. Open the downloaded JSON and compare it to the reviewed report. Clear must erase evidence and disable Export. Re-entry and Tab after a stop must add no events without a new Start.
5. Open `/examples/exit-rehearsal.html`. Confirm both statements, Start, focus an inside control, then separately test: pointer press on the outside non-focusable area; the inside programmatic-exit button; the blur-to-body button; Escape outside the root. Start a new session for each. Every departure must stop; re-entry and Tab must not resume collection.
6. At desktop and narrow window widths, verify visible focus, usable controls and readable review/export; switch windows while recording and verify it stops. Inspect the developer console for uncaught errors. The recorder must issue no evidence uploads, storage writes or network fetches; local static asset loads are expected.

Also test password focus, time/event caps, listener cleanup and pending timers through automated synthetic fixtures. Native keyboard behavior must be observed in genuine Microsoft Edge on Windows, Firefox, and Safari on macOS for final acceptance. Record unsupported or unavailable native environments as pending rather than substituting another engine.
