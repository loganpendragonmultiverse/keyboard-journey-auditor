# Integrating an owned test page

Copy recorder.js into a test-only application and import it from a module. Do not install it globally, ship it into production, run it in private browsing or inject it into arbitrary pages. Each host must provide its own consent controls, accessible Stop control outside the selected root, review/export surface and Clear action.

~~~js
import { JourneyRecorder } from "./recorder.js";
const recorder = new JourneyRecorder(document.querySelector("#synthetic-test-root"));
startButton.addEventListener("click", () => {
  recorder.start({
    testPage: ownedSyntheticTestCheckbox.checked,
    normalBrowsing: normalWindowCheckbox.checked,
  });
});
stopButton.addEventListener("click", () => recorder.stop());
clearButton.addEventListener("click", () => recorder.clear());
// Render report() with textContent after stopping. Export only on deliberate click.
~~~

Only elements within that root are described. The recorder stores generated per-session slots, coarse tag/role categories and numeric tabindex, never selectors, labels or values. Test the actual keyboard routes; this does not infer focus order from DOM order. Three stationary Tab samples and four samples cycling through two destinations generate possible-trap evidence. Review their sequence numbers in the exported events, test Shift+Tab and Escape, and determine whether the loop is intended.

The normal-window assertion is an explicit user boundary. Web pages cannot reliably identify private browsing without intrusive techniques; no detection, browsing-history access or private-window capability is requested. Do not use the library outside an owned synthetic test page in a normal window.
