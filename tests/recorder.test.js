import test from "node:test";
import assert from "node:assert/strict";
import { JourneyRecorder } from "../recorder.js";

function setup() {
  const win = new EventTarget(), doc = new EventTarget(), root = new EventTarget();
  doc.defaultView = win; doc.hidden = false;
  root.ownerDocument = doc; root.contains = (node) => Boolean(node?.inside);
  const timers = new Map(); let id = 0;
  const recorder = new JourneyRecorder(root, { clock: () => 25,
    delay: (fn, ms) => { timers.set(++id, { fn, ms }); return id; },
    cancel: (key) => timers.delete(key) });
  const node = (tag = "BUTTON", type = "") => ({ inside: true, tagName: tag, type,
    tabIndex: 0, getAttribute: () => null,
    get value() { throw new Error("Must not read values"); },
    get textContent() { throw new Error("Must not read contents"); } });
  const tick = () => { for (const [key, timer] of [...timers]) if (timer.ms === 80) { timers.delete(key); timer.fn(); } };
  const key = (value = "Tab", props = {}) => recorder.key({ key: value, ...props });
  return { recorder, doc, root, win, node, key, tick, timers };
}
const consent = { testPage: true, normalBrowsing: true };

test("requires deliberate consent and stays idle until start", () => {
  const { recorder, key } = setup();
  key(); assert.equal(recorder.events.length, 0);
  assert.throws(() => recorder.start(), /Confirm/);
  assert.throws(() => recorder.start({ testPage: true }), /Confirm/);
});
test("records focus order and direction, never typed values or text", () => {
  const { recorder, doc, node, key, tick } = setup();
  const a = node(), b = node("INPUT");
  doc.activeElement = a; recorder.start(consent);
  key("p"); key("a"); key("s"); assert.equal(recorder.events.length, 1);
  key("Tab", { shiftKey: true }); doc.activeElement = b; tick();
  const report = recorder.report();
  assert.equal(report.events[1].direction, "backward");
  assert.equal(report.events[1].from.slot, 1); assert.equal(report.events[1].to.slot, 2);
  assert.equal(report.events[1].to.tag, "INPUT");
  assert.ok(!JSON.stringify(report).includes('"value"'));
});
test("three stationary tabs produce traceable possible-trap evidence", () => {
  const { recorder, doc, node, key, tick } = setup();
  doc.activeElement = node(); recorder.start(consent);
  for (let i = 0; i < 3; i++) { key("Tab", { defaultPrevented: true }); tick(); }
  const report = recorder.report();
  assert.equal(report.possible_traps[0].kind, "stationary-focus");
  assert.deepEqual(report.possible_traps[0].sequences, [2, 3, 4]);
  assert.equal(report.events[1].prevented, true);
});
test("password focus stops without retaining a password target", () => {
  const { recorder, doc, node, key, tick } = setup();
  doc.activeElement = node(); recorder.start(consent);
  key(); doc.activeElement = node("INPUT", "password"); tick();
  assert.equal(recorder.reason, "password-focus"); assert.equal(recorder.events.length, 1);
});
test("stop removes listeners and cancels pending sampling", () => {
  const { recorder, doc, node, key, tick, timers, root } = setup();
  doc.activeElement = node(); recorder.start(consent); key();
  recorder.stop(); tick(); assert.equal(timers.size, 0);
  root.dispatchEvent(new Event("focusin")); assert.equal(recorder.events.length, 1);
  key(); assert.equal(recorder.events.length, 1);
});
test("escape, visibility, blur and time boundaries stop", () => {
  for (const boundary of ["escape", "hidden", "blur", "expiry"]) {
    const { recorder, doc, win, node, key, timers } = setup();
    doc.activeElement = node(); recorder.start(consent);
    if (boundary === "escape") key("Escape");
    if (boundary === "hidden") { doc.hidden = true; doc.dispatchEvent(new Event("visibilitychange")); }
    if (boundary === "blur") win.dispatchEvent(new Event("blur"));
    if (boundary === "expiry") [...timers.values()].find((t) => t.ms === 300000).fn();
    assert.equal(recorder.active, false);
  }
});
test("event cap, report isolation, unknown roles and clearing", () => {
  const { recorder, doc, node } = setup();
  doc.activeElement = node("CUSTOM-SECRET"); doc.activeElement.getAttribute = () => "secret typed content";
  recorder.start(consent);
  assert.equal(recorder.events[0].target.tag, "OTHER");
  assert.equal(recorder.events[0].target.role, null);
  const report = recorder.report(); report.events.length = 0;
  assert.equal(recorder.events.length, 1);
  for (let i = 0; i < 500; i++) recorder.focus(doc.activeElement);
  assert.equal(recorder.events.length, 500); assert.equal(recorder.reason, "event-limit");
  recorder.clear(); assert.equal(recorder.events.length, 0);
});
test("leaving selected root stops without page-wide collection", () => {
  const { recorder, doc, node, key, tick } = setup();
  doc.activeElement = node(); recorder.start(consent); key(); doc.activeElement = { inside: false }; tick();
  assert.equal(recorder.reason, "test-root-left");
  assert.deepEqual(recorder.events[1].to, { boundary: true });
});

test("two-element cycles are evidence, modifier combinations are ignored", () => {
  const { recorder, doc, node, key, tick } = setup();
  const a = node(), b = node();
  doc.activeElement = a; recorder.start(consent);
  key("Tab", { ctrlKey: true }); tick();
  key("Tab", { altKey: true }); tick();
  key("Tab", { metaKey: true }); tick();
  key("Tab", { repeat: true }); tick();
  assert.equal(recorder.events.length, 1);
  for (const destination of [b, a, b, a]) { key(); doc.activeElement = destination; tick(); }
  assert.equal(recorder.report().possible_traps[0].kind, "short-focus-cycle");
  assert.throws(() => recorder.start(consent), /already active/);
  recorder.stop(); doc.hidden = true;
  assert.throws(() => recorder.start(consent), /visible/);
});

function dispatch(target, type, properties = {}) {
  const event = new Event(type);
  for (const [name, value] of Object.entries(properties)) {
    Object.defineProperty(event, name, { value });
  }
  target.dispatchEvent(event);
}
test("pointer exit stops even when clicking a non-focusable outside target", () => {
  const { recorder, doc, node, key, tick, root, timers } = setup();
  const inside = node(), outside = { inside: false,
    get value() { throw new Error("Outside values must never be read"); },
    get textContent() { throw new Error("Outside text must never be read"); } };
  doc.activeElement = inside; recorder.start(consent); key();
  dispatch(doc, "pointerdown", { target: outside });
  assert.equal(recorder.reason, "test-root-left"); assert.equal(timers.size, 0);
  const count = recorder.events.length;
  doc.activeElement = inside; dispatch(root, "focusin", { target: inside });
  key(); tick(); assert.equal(recorder.events.length, count);
  assert.equal(recorder.active, false);
});
test("programmatic focus outside and blur-to-body stop; re-entry requires fresh Start", () => {
  for (const relatedTarget of [{ inside: false }, null]) {
    const { recorder, doc, node, root, key, tick } = setup();
    const inside = node(); doc.activeElement = inside; recorder.start(consent);
    dispatch(root, "focusout", { target: inside, relatedTarget });
    assert.equal(recorder.reason, "test-root-left");
    const count = recorder.events.length;
    dispatch(root, "focusin", { target: inside }); key(); tick();
    assert.equal(recorder.events.length, count); assert.equal(recorder.active, false);
    recorder.start(consent); assert.equal(recorder.active, true);
    assert.equal(recorder.events.length, 1);
  }
});
test("document focus boundary is a fallback and document Escape cancels globally", () => {
  const { recorder, doc, node } = setup();
  doc.activeElement = node(); recorder.start(consent);
  dispatch(doc, "focusin", { target: { inside: false } });
  assert.equal(recorder.active, false);
  // Start is allowed from its external UI button; Escape there must still work.
  doc.activeElement = { inside: false }; recorder.start(consent);
  dispatch(doc, "keydown", { key: "x", target: doc.activeElement });
  assert.equal(recorder.active, true); assert.equal(recorder.events.length, 0);
  dispatch(doc, "keydown", { key: "Escape", target: doc.activeElement });
  assert.equal(recorder.reason, "escape"); assert.equal(recorder.active, false);
});
test("inside pointer/focus movement stays active and global listeners detach", () => {
  const { recorder, doc, root, node } = setup();
  const a = node(), b = node(); doc.activeElement = a; recorder.start(consent);
  dispatch(doc, "pointerdown", { target: b });
  dispatch(root, "focusout", { target: a, relatedTarget: b });
  dispatch(doc, "focusin", { target: b });
  assert.equal(recorder.active, true);
  recorder.stop("user");
  dispatch(doc, "keydown", { key: "Escape" });
  dispatch(doc, "pointerdown", { target: { inside: false } });
  assert.equal(recorder.reason, "user");
});

// Merely visiting two destinations does not establish an alternating cycle.
test("stationary samples followed by a move are not a two-element cycle", () => {
  const { recorder, doc, node, key, tick } = setup();
  const a = node(), b = node(); doc.activeElement = a; recorder.start(consent);
  for (const destination of [a, a, a, b]) { key(); doc.activeElement = destination; tick(); }
  assert.equal(recorder.report().possible_traps.some((x) => x.kind === "short-focus-cycle"), false);
  assert.equal(recorder.report().possible_traps.some((x) => x.kind === "stationary-focus"), true);
});
test("backward cycles require contiguous alternating transitions", () => {
  const { recorder, doc, node, key, tick } = setup();
  const a = node(), b = node(); doc.activeElement = a; recorder.start(consent);
  for (const destination of [b, a, b, a]) {
    key("Tab", { shiftKey: true }); doc.activeElement = destination; tick();
  }
  assert.equal(recorder.report().possible_traps[0].kind, "short-focus-cycle");
  recorder.events[2].from = { slot: 999 };
  assert.equal(recorder.report().possible_traps.some((x) => x.kind === "short-focus-cycle"), false);
});
test("mixed Tab direction is not a short-focus-cycle", () => {
  const { recorder, doc, node, key, tick } = setup();
  const a = node(), b = node(); doc.activeElement = a; recorder.start(consent);
  for (const [index, destination] of [b, a, b, a].entries()) {
    key("Tab", { shiftKey: index === 2 }); doc.activeElement = destination; tick();
  }
  assert.deepEqual(recorder.report().possible_traps, []);
});
