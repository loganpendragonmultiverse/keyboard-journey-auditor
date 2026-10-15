/**
 * Opt-in recorder for a developer-selected test root. Never reads element text,
 * values, names, IDs, labels, URLs, clipboard data, or non-navigation key values.
 */
const roles = new Set(["button", "link", "checkbox", "radio", "textbox", "combobox",
  "listbox", "option", "tab", "tabpanel", "menu", "menuitem", "dialog", "switch"]);
const tags = new Set(["A", "BUTTON", "INPUT", "TEXTAREA", "SELECT", "SUMMARY"]);
export class JourneyRecorder {
  constructor(root, { onStop = () => {}, clock = () => performance.now(),
    delay = (fn, ms) => setTimeout(fn, ms), cancel = (id) => clearTimeout(id) } = {}) {
    this.root = root;
    this.doc = root.ownerDocument;
    this.win = this.doc.defaultView;
    this.onStop = onStop;
    this.clock = clock;
    this.delay = delay;
    this.cancel = cancel;
    this.active = false;
    this.events = [];
    this.ids = new WeakMap();
    this.nextId = 1;
    this.pending = new Set();
    this.keyHandler = (e) => this.key(e);
    this.focusHandler = (e) => this.focus(e.target);
    this.hideHandler = () => { if (this.doc.hidden) this.stop("hidden"); };
    this.exitHandler = () => this.stop("page-left");
    this.blurHandler = () => this.stop("window-blur");
  }
  describe(element) {
    if (!element || !this.root.contains(element)) return { boundary: true };
    if (element.tagName === "INPUT" && element.type === "password") return { sensitive: true };
    if (!this.ids.has(element)) this.ids.set(element, this.nextId++);
    const role = element.getAttribute("role");
    return { slot: this.ids.get(element), tag: tags.has(element.tagName) ? element.tagName : "OTHER",
      role: roles.has(role) ? role : null,
      tabindex: Number.isInteger(element.tabIndex) ? element.tabIndex : null };
  }
  start({ testPage = false, normalBrowsing = false } = {}) {
    if (!testPage || !normalBrowsing) throw new Error("Confirm an owned test page in a normal browsing window");
    if (this.active) throw new Error("Session already active");
    if (this.doc.hidden) throw new Error("Test page must be visible");
    this.events = [];
    this.ids = new WeakMap();
    this.nextId = 1;
    this.started = this.clock();
    this.reason = null;
    this.active = true;
    this.root.addEventListener("keydown", this.keyHandler, true);
    this.root.addEventListener("focusin", this.focusHandler, true);
    this.doc.addEventListener("visibilitychange", this.hideHandler);
    this.win.addEventListener("pagehide", this.exitHandler);
    this.win.addEventListener("blur", this.blurHandler);
    this.expiry = this.delay(() => this.stop("time-limit"), 300000);
    this.focus(this.doc.activeElement);
  }
  record(event) {
    if (!this.active) return;
    this.events.push({ sequence: this.events.length + 1,
      elapsed_ms: Math.round(this.clock() - this.started), ...event });
    if (this.events.length >= 500) this.stop("event-limit");
  }
  focus(element) {
    if (!this.active) return;
    const descriptor = this.describe(element);
    if (descriptor.sensitive) { this.stop("password-focus"); return; }
    if (!descriptor.boundary) this.record({ kind: "focus", target: descriptor });
  }
  key(event) {
    if (!this.active) return;
    if (event.key === "Escape") { this.stop("escape"); return; }
    if (event.key !== "Tab") return;
    if (event.ctrlKey || event.altKey || event.metaKey || event.repeat) return;
    const from = this.describe(this.doc.activeElement);
    if (from.sensitive) { this.stop("password-focus"); return; }
    let timer;
    timer = this.delay(() => {
      this.pending.delete(timer);
      if (!this.active) return;
      const to = this.describe(this.doc.activeElement);
      if (to.sensitive) { this.stop("password-focus"); return; }
      this.record({ kind: "tab", direction: event.shiftKey ? "backward" : "forward",
        from, to, prevented: Boolean(event.defaultPrevented) });
      if (to.boundary) this.stop("test-root-left");
    }, 80);
    this.pending.add(timer);
  }
  stop(reason = "user") {
    if (!this.active) return;
    this.active = false;
    this.reason = reason;
    this.cancel(this.expiry);
    for (const timer of this.pending) this.cancel(timer);
    this.pending.clear();
    this.root.removeEventListener("keydown", this.keyHandler, true);
    this.root.removeEventListener("focusin", this.focusHandler, true);
    this.doc.removeEventListener("visibilitychange", this.hideHandler);
    this.win.removeEventListener("pagehide", this.exitHandler);
    this.win.removeEventListener("blur", this.blurHandler);
    this.onStop(reason);
  }
  report() {
    const evidence = structuredClone(this.events);
    const tabs = evidence.filter((e) => e.kind === "tab");
    const possibleTraps = [];
    for (let i = 2; i < tabs.length; i++) {
      const window = tabs.slice(i - 2, i + 1);
      if (window.every((e) => e.from.slot && e.from.slot === e.to.slot)) {
        possibleTraps.push({ kind: "stationary-focus", sequences: window.map((e) => e.sequence) });
      }
    }
    for (let i = 3; i < tabs.length; i++) {
      const window = tabs.slice(i - 3, i + 1);
      const destinations = window.map((e) => e.to.slot);
      if (destinations.every(Boolean) && new Set(destinations).size === 2 &&
        window.every((e) => e.direction === window[0].direction)) {
        possibleTraps.push({ kind: "short-focus-cycle", sequences: window.map((e) => e.sequence) });
      }
    }
    return { schema: 1, version: "0.1.0", active: this.active,
      stop_reason: this.reason, events: evidence, possible_traps: possibleTraps,
      interpretation: "Heuristic evidence only. A dialog loop can be intentional. Test escape routes manually.",
      privacy: "No text, input values, labels, IDs, page URL or typed contents are recorded." };
  }
  clear() {
    this.stop("cleared");
    this.events = [];
    this.ids = new WeakMap();
    this.reason = "cleared";
  }
}
