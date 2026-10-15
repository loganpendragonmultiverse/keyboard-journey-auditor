import { JourneyRecorder } from "./recorder.js";
const get = (id) => document.getElementById(id);
const recorder = new JourneyRecorder(get("fixture"), { onStop: (reason) => {
  get("status").textContent = "Stopped · " + reason;
  get("start").disabled = false;
  get("stop").disabled = true;
  get("export").disabled = recorder.events.length === 0;
  render();
} });
function render() { get("report").textContent = JSON.stringify(recorder.report(), null, 2); }
get("start").addEventListener("click", () => {
  try {
    recorder.start({ testPage: get("test").checked, normalBrowsing: get("normal").checked });
    get("start").disabled = true; get("stop").disabled = false; get("export").disabled = true;
    get("status").textContent = "Recording · Tab through the fixture; Escape stops";
    get("fixture").querySelector("a").focus();
  } catch (error) { get("status").textContent = error.message; }
});
get("stop").addEventListener("click", () => recorder.stop());
get("clear").addEventListener("click", () => {
  recorder.clear(); render(); get("export").disabled = true;
  get("status").textContent = "Cleared · no evidence retained";
});
get("export").addEventListener("click", () => {
  if (recorder.active) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(recorder.report(), null, 2)], { type: "application/json" }));
  const link = document.createElement("a"); link.href = url; link.download = "keyboard-journey.json"; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
get("trap-button").addEventListener("keydown", (event) => {
  if (get("trap").checked && event.key === "Tab") event.preventDefault();
});
get("fixture").addEventListener("focusin", () => { if (recorder.active) render(); });
