"""Exercise an actual release web ZIP with a preinstalled native WebDriver.

Never changes browser/security settings or enables Safari remote automation.
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import http.server
import json
import os
import pathlib
import platform
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
import zipfile

ELEMENT = "element-6066-11e4-a52e-4f735466cecf"


def wait_for(fn, seconds=15):
    deadline = time.monotonic() + seconds
    last = None
    while time.monotonic() < deadline:
        try:
            result = fn()
            if result:
                return result
        except (OSError, RuntimeError, json.JSONDecodeError) as exc:
            last = exc
        time.sleep(0.1)
    raise AssertionError(f"Timed out waiting for browser condition: {last}")


class Browser:
    def __init__(self, kind):
        self.kind = kind
        self.click_results = []
        self.window_selection_results = []
        binary = {"safari": "safaridriver", "edge": "msedgedriver", "firefox": "geckodriver"}[kind]
        executable = shutil.which(binary)
        if executable is None:
            location = os.environ.get({"edge": "EDGEWEBDRIVER", "firefox": "GECKOWEBDRIVER", "safari": "SAFARIWEBDRIVER"}[kind], "")
            for name in [binary, binary + ".exe"]:
                candidate = pathlib.Path(location) / name
                if location and candidate.is_file():
                    executable = str(candidate)
                    break
        if executable is None:
            raise RuntimeError(f"Preinstalled {binary} unavailable; no installation/settings fallback")
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        self.base = f"http://127.0.0.1:{port}"
        self.session = None
        arguments = [executable, "--port=" + str(port)] if kind == "edge" else [executable, "-p" if kind == "safari" else "--port", str(port)]
        if kind == "safari":
            # Ordinary application launch only; never enable automation or edit preferences.
            subprocess.run(["open", "-a", "Safari", "about:blank"], check=True)
            time.sleep(2)
        self.process = subprocess.Popen(arguments)
        try:
            wait_for(lambda: self.call("GET", "/status").get("ready"))
            caps = {"browserName": {"safari": "safari", "edge": "MicrosoftEdge", "firefox": "firefox"}[kind]}
            if kind == "edge":
                caps["ms:edgeOptions"] = {"args": ["--headless=new"]}
            if kind == "firefox":
                caps["moz:firefoxOptions"] = {"args": ["-headless"]}
            started = self.call("POST", "/session", {"capabilities": {"alwaysMatch": caps}})
            self.session = started["sessionId"]
            self.capabilities = started["capabilities"]
            assert self.capabilities["browserName"].lower() == caps["browserName"].lower()
            assert self.capabilities.get("browserVersion")
        except BaseException:
            self.close()
            raise

    def call(self, method, path, data=None):
        body = None if data is None else json.dumps(data).encode()
        req = urllib.request.Request(self.base + path, data=body, method=method, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=40) as response:
                value = json.load(response)["value"]
        except urllib.error.HTTPError as exc:
            raise RuntimeError(exc.read().decode()) from exc
        if isinstance(value, dict) and value.get("error"):
            raise RuntimeError(json.dumps(value))
        return value

    def command(self, method, path, data=None):
        return self.call(method, "/session/" + self.session + path, data)

    def js(self, script, *args):
        return self.command("POST", "/execute/sync", {"script": script, "args": list(args)})

    def element(self, selector):
        return self.command("POST", "/element", {"using": "css selector", "value": selector})[ELEMENT]

    def click(self, selector):
        element = self.element(selector)
        before = self.js("""
          const element = arguments[0];
          element.scrollIntoView({block:'center',inline:'nearest',behavior:'instant'});
          window.__nativeClick = {events:[],listeners:[]};
          for (const type of ['pointerdown','pointerup','mousedown','mouseup','click']) {
            const handler = event => window.__nativeClick.events.push({type,
              expected_target:event.target === element || element.contains(event.target),
              trusted:event.isTrusted,tag:event.target.tagName,id:event.target.id,
              x:event.clientX,y:event.clientY,scrollX,scrollY});
            document.addEventListener(type,handler,true);
            window.__nativeClick.listeners.push([type,handler]);
          }
          return {rect:element.getBoundingClientRect().toJSON(),scrollX,scrollY,width:innerWidth,height:innerHeight,hasFocus:document.hasFocus()};
        """, {ELEMENT:element})
        mechanism = "W3C pointer Actions" if self.kind == "safari" else "WebDriver ElementClick"
        result = {"selector":selector,"mechanism":mechanism,"before":before}
        if self.kind == "safari":
            result["window_before"] = {"current":self.command("GET", "/window"),
                                       "handles":self.command("GET", "/window/handles")}
        try:
            if self.kind == "safari":
                # Standard remote-end pointer input; no DOM click/event dispatch,
                # alternate activation fallback or changed browser preferences.
                self.command("POST", "/actions", {"actions":[{
                    "type":"pointer","id":"native-mouse","parameters":{"pointerType":"mouse"},
                    "actions":[{"type":"pointerMove","duration":250,"origin":{ELEMENT:element},"x":0,"y":0},
                               {"type":"pointerDown","button":0},{"type":"pointerUp","button":0}]
                }]})
            else:
                self.command("POST", "/element/" + element + "/click", {})
        finally:
            result["after"] = self.js("""
              for (const [type,handler] of window.__nativeClick.listeners)
                document.removeEventListener(type,handler,true);
              return {events:window.__nativeClick.events,scrollX,scrollY,hasFocus:document.hasFocus(),
                rect:arguments[0].getBoundingClientRect().toJSON(),active:{tag:document.activeElement.tagName,id:document.activeElement.id}};
            """, {ELEMENT:element})
            self.click_results.append(result)
        required = ['pointerdown','pointerup','click']
        observed = result['after']['events']
        if self.kind == 'safari' and not all(any(event['type'] == expected and
                event['trusted'] and event['expected_target'] for event in observed)
                for expected in required):
            # Observation only after failed immediate activation: never sends
            # another input and never promotes a late event into a passing case.
            result['failure_only_late_trace'] = []
            started = time.monotonic()
            for seconds in [0.1,0.5,1.5,3.0]:
                time.sleep(max(0, started + seconds - time.monotonic()))
                snapshot = self.js("""
                  const element = document.querySelector(arguments[0]);
                  return {page_performance_ms:performance.now(),readyState:document.readyState,hidden:document.hidden,hasFocus:document.hasFocus(),
                    status:document.getElementById('status')?.textContent,
                    active:{tag:document.activeElement.tagName,id:document.activeElement.id},
                    intendedRect:element?.getBoundingClientRect().toJSON(),scrollX,scrollY,
                    persistentTrace:window.__nativeStartup || {events:window.__nativeBoundaryEvents || []}};
                """, selector)
                result['failure_only_late_trace'].append({'after_initial_snapshot_seconds':time.monotonic()-started,'snapshot':snapshot})
        for expected in ['pointerdown','pointerup','click']:
            assert any(event['type'] == expected and event['trusted'] and event['expected_target']
                       for event in result['after']['events']), json.dumps({"native_activation_failure":result,"capabilities":self.capabilities})

    def keys(self, value):
        active = self.command("GET", "/element/active")[ELEMENT]
        self.command("POST", "/element/" + active + "/value", {"text": value})
        time.sleep(0.15)  # Preserve the recorder's documented 80-ms sample boundary.

    def open(self, url):
        self.command("POST", "/url", {"url": url})
        wait_for(lambda: self.js("return document.readyState === 'complete'"))

    def report(self):
        return json.loads(self.js("return document.getElementById('report').textContent"))

    def close(self):
        if self.session:
            try:
                self.command("DELETE", "")
            finally:
                self.session = None
        if self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=10)


def acceptance(browser, base, version):
    completed = []
    browser.open(base + "/")
    if browser.kind == "safari":
        # Select the already owned browsing context once during initial setup.
        # This is a standard context command, not a failed-click fallback;
        # native trusted activation assertions below remain mandatory.
        current = browser.command("GET", "/window")
        selection = {"requested_handle":current, "application_activation":{
            "before":browser.js("return {hasFocus:document.hasFocus(),hidden:document.hidden}"),
            "current_before":current, "handles_before":browser.command("GET", "/window/handles")}}
        browser.window_selection_results.append(selection)
        # Ordinary application activation only, without a URL or a new window.
        # Activate before the sole context selection so the owned automation
        # context is selected after any existing Safari window comes forward.
        activated = subprocess.run(["open", "-a", "Safari"], capture_output=True, text=True)
        selection["application_activation"]["returncode"] = activated.returncode
        time.sleep(1)  # One bounded setup settling interval; no repeated launch/input.
        selection["application_activation"]["after"] = browser.js("return {hasFocus:document.hasFocus(),hidden:document.hidden}")
        selection["application_activation"]["current_after"] = browser.command("GET", "/window")
        selection["application_activation"]["handles_after"] = browser.command("GET", "/window/handles")
        activated.check_returncode()
        selection["before"] = browser.js("return {hasFocus:document.hasFocus(),hidden:document.hidden}")
        selection["handles_before"] = browser.command("GET", "/window/handles")
        try:
            browser.command("POST", "/window", {"handle":current})
        finally:
            selection["current_after"] = browser.command("GET", "/window")
            selection["handles_after"] = browser.command("GET", "/window/handles")
            selection["after"] = browser.js("return {hasFocus:document.hasFocus(),hidden:document.hidden}")
    browser.js("""
      window.__nativeStartup = {events:[], errors:[], unhandledRejections:[]};
      const describe = element => element ? {tag:element.tagName,id:element.id,
        rect:element.getBoundingClientRect().toJSON()} : null;
      for (const type of ['pointerdown','pointerup','mousedown','mouseup','click','focusin','focusout'])
        document.addEventListener(type, event => window.__nativeStartup.events.push({
          type, target:describe(event.target), active:describe(document.activeElement),
          trusted:event.isTrusted, x:event.clientX ?? null,y:event.clientY ?? null,scrollX,scrollY
        }), true);
      addEventListener('error', e => window.__nativeStartup.errors.push({message:e.message,filename:e.filename,line:e.lineno}));
      addEventListener('unhandledrejection', e => window.__nativeStartup.unhandledRejections.push(String(e.reason)));
    """)
    initial = browser.js("return {readyState:document.readyState,hidden:document.hidden,status:document.getElementById('status').textContent,consents:[document.getElementById('test').checked,document.getElementById('normal').checked],width:innerWidth,height:innerHeight}")
    assert "Idle" in browser.js("return document.getElementById('status').textContent")
    browser.keys("\ue004")
    assert browser.js("return document.getElementById('report').textContent") == "No evidence yet."
    browser.click("#start")
    status = browser.js("return document.getElementById('status').textContent")
    if "Confirm" not in status:
        diagnostics = browser.js("return {initial:arguments[0],status:document.getElementById('status').textContent,consents:[document.getElementById('test').checked,document.getElementById('normal').checked],trace:window.__nativeStartup,resources:performance.getEntriesByType('resource').map(e=>({name:e.name,duration:e.duration,responseEnd:e.responseEnd})),readyState:document.readyState,hidden:document.hidden}", initial)
        # Failure-only probe: inspect the module cache/rejection after capturing
        # the failed native click. Never retries that click or converts failure to pass.
        try:
            diagnostics["module_probe_after_failure"] = browser.command("POST", "/execute/async", {"script":"const done=arguments[arguments.length-1]; import(document.querySelector('script[type=module]').src).then(()=>done({resolved:true})).catch(e=>done({resolved:false,name:e.name,message:e.message}));", "args":[]})
        except RuntimeError as exc:
            diagnostics["module_probe_after_failure"] = {"driver_error":str(exc)}
        assert "Confirm" in status, json.dumps({"initial_consent_failure":diagnostics,"capabilities":browser.capabilities})
    completed.append("idle and consent refusal")
    browser.click("#test")
    browser.click("#normal")
    browser.click("#start")
    browser.js("document.querySelector('#fixture input').focus()")
    browser.keys("SYNTHETIC_TYPED_CANARY")
    # Real DOM controls and real native key dispatch; synthetic host deliberately
    # cycles focus. No recorder events, stop methods or reports are mocked.
    browser.js("""
      const root = document.getElementById('fixture');
      const a = document.createElement('button'), b = document.createElement('button');
      a.id = 'native-a'; b.id = 'native-b'; a.textContent = 'Synthetic A'; b.textContent = 'Synthetic B';
      root.append(a,b);
      for (const [from,to] of [[a,b],[b,a]]) from.addEventListener('keydown', e => {
        if (e.key === 'Tab') { e.preventDefault(); to.focus(); }
      });
      a.focus();
    """)
    for _ in range(4):
        browser.keys("\ue004")
    for _ in range(4):
        browser.keys("\ue008\ue004\ue000")
    browser.keys("\ue00c")
    report = browser.report()
    assert report["active"] is False and report["stop_reason"] == "escape"
    assert report["version"] == version
    tabs = [x for x in report["events"] if x["kind"] == "tab"]
    assert {x["direction"] for x in tabs} == {"forward", "backward"}
    assert any(x["kind"] == "short-focus-cycle" for x in report["possible_traps"])
    text = json.dumps(report)
    assert all(canary not in text for canary in ["SYNTHETIC_TYPED_CANARY", "native-a", "Synthetic A", base])
    completed.append("real Tab/Shift+Tab, contiguous cycle, Escape and value-free report")
    browser.js("window.__export = null; const original = URL.createObjectURL; URL.createObjectURL = blob => { blob.text().then(text => window.__export = text); return original(blob); };")
    browser.click("#export")
    exported = wait_for(lambda: browser.js("return window.__export"))
    assert json.loads(exported) == report
    completed.append("deliberate native export click and exact Blob payload")
    browser.click("#clear")
    assert browser.report()["events"] == []
    assert browser.js("return document.getElementById('export').disabled")
    browser.click("#trap")
    browser.click("#start")
    browser.js("document.getElementById('trap-button').focus()")
    for _ in range(3):
        browser.keys("\ue004")
    browser.js("document.getElementById('native-a').focus()")
    browser.keys("\ue004")
    browser.keys("\ue00c")
    traps = browser.report()["possible_traps"]
    assert any(x["kind"] == "stationary-focus" for x in traps)
    assert not any(x["kind"] == "short-focus-cycle" for x in traps)
    completed.append("clear, fresh session, stationary trap and non-cycle counterexample")
    viewports = []
    for width in [1280, 390]:
        browser.command("POST", "/window/rect", {"width": width, "height": 900})
        dims = browser.js("return {width:innerWidth, scroll:document.documentElement.scrollWidth, client:document.documentElement.clientWidth}")
        assert dims["scroll"] <= dims["client"] + 1
        viewports.append({"requested_window_width": width, "actual": dims})
    completed.append("desktop/narrow native window layout (actual dimensions recorded)")
    for departure in ["pointer", "programmatic", "blur", "escape-outside"]:
        browser.open(base + "/examples/exit-rehearsal.html")
        browser.js("""
          window.__nativeBoundaryEvents = [];
          const describe = element => element ? {tag:element.tagName, id:element.id,
            inside:document.getElementById('root').contains(element)} : null;
          for (const type of ['pointerdown','pointerup','mousedown','mouseup','click','focusin','focusout'])
            document.addEventListener(type, event => window.__nativeBoundaryEvents.push({
              type, target:describe(event.target), active:describe(document.activeElement),
              trusted:event.isTrusted, pointerType:event.pointerType || null,
              x:event.clientX ?? null, y:event.clientY ?? null, scrollX, scrollY,
              targetRect:event.target.getBoundingClientRect().toJSON(),
              reportRect:document.getElementById('report').getBoundingClientRect().toJSON()
            }), true);
        """)
        layout = browser.js("return {width:innerWidth,scroll:document.documentElement.scrollWidth,client:document.documentElement.clientWidth,reportHeight:document.getElementById('report').getBoundingClientRect().height}")
        assert layout["scroll"] <= layout["client"] + 1
        browser.click("#owned")
        browser.click("#normal")
        browser.click("#start")
        if departure == "escape-outside":
            browser.keys("\ue00c")  # Start is outside the selected root.
        else:
            browser.click("#inside")
            browser.click({"pointer": "#outside-pointer", "programmatic": "#programmatic", "blur": "#blur"}[departure])
        report = browser.report()
        assert browser.js("return document.getElementById('report').getBoundingClientRect().height") == layout["reportHeight"]
        diagnostics = browser.js("return {events:window.__nativeBoundaryEvents,active:{tag:document.activeElement.tagName,id:document.activeElement.id},status:document.getElementById('status').textContent,scrollX,scrollY,width:innerWidth,height:innerHeight,reportRect:document.getElementById('report').getBoundingClientRect().toJSON()}")
        assert not report["active"], json.dumps({"departure":departure, "report":report,
            "diagnostics":diagnostics, "capabilities":browser.capabilities})
        assert report["stop_reason"] == ("escape" if departure == "escape-outside" else "test-root-left"), json.dumps(diagnostics)
        before = len(report["events"])
        browser.js("document.getElementById('inside').focus()")
        browser.keys("\ue004")
        assert len(browser.report()["events"]) == before
        assert not browser.report()["active"]
        completed.append(departure + " stops; re-entry cannot resume")
    return {"cases": completed, "case_count": len(completed), "native_window_dimensions": viewports,
            "export_payload_verified": True, "OS_download_file_verified": False,
            "export_boundary": "Real export control clicked and native Blob payload compared. OS save-dialog/download-directory behavior is separate from this assertion."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--browser", choices=["safari", "edge", "firefox"], required=True)
    parser.add_argument("--web-zip", type=pathlib.Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    assert args.commit == subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    checksums = dict(line.split("  ", 1)[::-1] for line in (args.web_zip.parent / "SHA256SUMS").read_text().splitlines())
    assert checksums[args.web_zip.name] == hashlib.sha256(args.web_zip.read_bytes()).hexdigest()
    raw = args.web_zip.read_bytes()
    evidence = {"browser": args.browser, "commit": args.commit, "artifact": args.web_zip.name,
                "artifact_sha256": hashlib.sha256(raw).hexdigest(), "script_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
                "OS": platform.platform(), "settings_modified": False, "passed": False}
    browser = None
    with tempfile.TemporaryDirectory(prefix="keyboard-native-") as directory:
        with zipfile.ZipFile(args.web_zip) as archive:
            names = archive.namelist()
            assert len(names) == len(set(names)) and sum(x.file_size for x in archive.infolist()) < 10_000_000
            assert all(not pathlib.PurePosixPath(n).is_absolute() and ".." not in pathlib.PurePosixPath(n).parts and "\\" not in n for n in names)
            assert {"index.html", "recorder.js", "app.js", "README.md", "DEVELOPMENT.md", "TESTING.md", "CHANGELOG.md", "LICENSE", "examples/exit-rehearsal.html"} <= set(names)
            archive.extractall(directory)
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=directory)
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            browser = Browser(args.browser)
            evidence["capabilities"] = browser.capabilities
            version = args.web_zip.name.split("-v", 1)[1].removesuffix("-web.zip")
            evidence["version"] = version
            evidence.update(acceptance(browser, f"http://127.0.0.1:{server.server_port}", version))
            evidence["passed"] = True
        finally:
            if browser:
                evidence["native_clicks"] = browser.click_results
                evidence["window_selection"] = browser.window_selection_results
                browser.close()
            server.shutdown()
            server.server_close()
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(evidence))


if __name__ == "__main__":
    main()
