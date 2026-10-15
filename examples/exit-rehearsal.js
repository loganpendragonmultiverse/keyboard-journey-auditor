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
get("blur").addEventListener("click", (event) => event.currentTarget.blur());
get("root").addEventListener("focusin", render);
