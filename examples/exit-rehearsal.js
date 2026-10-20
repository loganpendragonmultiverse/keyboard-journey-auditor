import { JourneyRecorder } from "../recorder.js";
const get = (id) => document.getElementById(id);
const recorder = new JourneyRecorder(get("root"), { onStop: (reason) => {
  get("status").textContent = "Stopped: " + reason;
  render();
} });
function render() { get("report").textContent = JSON.stringify(recorder.report(), null, 2); }
get("start").addEventListener("click", () => {
  try {
    recorder.start({ testPage: get("owned").checked, normalBrowsing: get("normal").checked });
    get("status").textContent = "Recording"; render();
  } catch (error) { get("status").textContent = error.message; }
});
get("stop").addEventListener("click", () => recorder.stop());
get("programmatic").addEventListener("click", () => get("outside").focus());
// Safari pointer clicks need not focus a button. Blur the actual owned focus,
// so this fixture exercises a real focusout-to-body in every native browser.
get("blur").addEventListener("click", () => {
  const active = document.activeElement;
  if (get("root").contains(active)) active.blur();
});
get("root").addEventListener("focusin", render);
