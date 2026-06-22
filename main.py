#!/usr/bin/env python3
from __future__ import annotations

import json, math, random, socketserver, subprocess, threading, time, webbrowser
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, parse_qs


USA_TIMEZONES = {
    "Eastern": {"iana": "America/New_York", "offset_std": -5, "offset_dst": -4, "uses_dst": True, "example": "New York, NY"},
    "Central": {"iana": "America/Chicago", "offset_std": -6, "offset_dst": -5, "uses_dst": True, "example": "Chicago, IL / Jackson County, MO"},
    "Mountain": {"iana": "America/Denver", "offset_std": -7, "offset_dst": -6, "uses_dst": True, "example": "Denver, CO"},
    "Arizona Mountain": {"iana": "America/Phoenix", "offset_std": -7, "offset_dst": -7, "uses_dst": False, "example": "Phoenix, AZ"},
    "Pacific": {"iana": "America/Los_Angeles", "offset_std": -8, "offset_dst": -7, "uses_dst": True, "example": "Los Angeles, CA"},
    "Alaska": {"iana": "America/Anchorage", "offset_std": -9, "offset_dst": -8, "uses_dst": True, "example": "Anchorage, AK"},
    "Hawaii": {"iana": "Pacific/Honolulu", "offset_std": -10, "offset_dst": -10, "uses_dst": False, "example": "Honolulu, HI"},
    "Aleutian": {"iana": "America/Adak", "offset_std": -10, "offset_dst": -9, "uses_dst": True, "example": "Adak, AK"},
    "Atlantic": {"iana": "America/Puerto_Rico", "offset_std": -4, "offset_dst": -4, "uses_dst": False, "example": "Puerto Rico / U.S. Virgin Islands"},
    "Samoa": {"iana": "Pacific/Pago_Pago", "offset_std": -11, "offset_dst": -11, "uses_dst": False, "example": "American Samoa"},
    "Chamorro": {"iana": "Pacific/Guam", "offset_std": 10, "offset_dst": 10, "uses_dst": False, "example": "Guam / Northern Mariana Islands"},
}


@dataclass
class Config:
    server_host: str = "127.0.0.1"
    server_port: int = 8080
    port_attempts: int = 100
    tick_seconds: float = 1.5
    output_dir: str = "outputs"
    default_timezone: str = "America/Chicago"


@dataclass
class TelemetryState:
    timestamp: str
    utc_time: str
    local_time: str
    timezone_name: str
    timezone_label: str
    utc_offset: str
    cycle: int
    status: str
    coherence: float
    drift: float
    stability: float
    concepts: int
    operators: int
    observations: int
    recommendation: str
    layer_1_coupling: str = "tight"
    layer_1_z_in: float = 500.0
    layer_2_branch: str = "cushion"
    layer_2_resistance: float = 50.0
    layer_3_entangled: bool = True
    layer_3_drag: float = 1.4
    layer_4_path: str = "internalizing"
    capacitor_voltage: float = 0.0
    capacitor_energy: float = 0.0
    collapse_mode: str = "none"


def second_sunday(year: int, month: int) -> datetime:
    d = datetime(year, month, 1)
    return d + timedelta(days=((6 - d.weekday()) % 7) + 7)


def first_sunday(year: int, month: int) -> datetime:
    d = datetime(year, month, 1)
    return d + timedelta(days=(6 - d.weekday()) % 7)


def us_dst_active(utc_now: datetime) -> bool:
    year = utc_now.year
    dst_start = second_sunday(year, 3).replace(hour=7, tzinfo=timezone.utc)
    dst_end = first_sunday(year, 11).replace(hour=6, tzinfo=timezone.utc)
    return dst_start <= utc_now < dst_end


def find_timezone_info(tz_name: str):
    for label, info in USA_TIMEZONES.items():
        if info["iana"] == tz_name:
            return label, info
    return "Central", USA_TIMEZONES["Central"]


def now_for_timezone(tz_name: str):
    utc_now = datetime.now(timezone.utc)
    label, info = find_timezone_info(tz_name)
    is_dst = bool(info["uses_dst"] and us_dst_active(utc_now))
    offset_hours = int(info["offset_dst"] if is_dst else info["offset_std"])
    local_now = utc_now.astimezone(timezone(timedelta(hours=offset_hours)))
    sign = "+" if offset_hours >= 0 else "-"
    return {
        "timestamp": utc_now.isoformat(),
        "utc_time": utc_now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "local_time": local_now.strftime("%Y-%m-%d %I:%M:%S %p") + f" {label} {'DST' if is_dst else 'STD'}",
        "timezone_name": info["iana"],
        "timezone_label": label,
        "utc_offset": f"{sign}{abs(offset_hours):02d}:00",
    }


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


class TelemetryBus:
    def __init__(self, cfg: Config):
        self.lock = threading.Lock()
        self.selected_timezone = cfg.default_timezone
        self.state = TelemetryState(
            **now_for_timezone(self.selected_timezone),
            cycle=0, status="INITIALIZING",
            coherence=0, drift=0, stability=0,
            concepts=0, operators=0, observations=0,
            recommendation="System warming up.",
        )
        self.history = []

    def set_timezone(self, tz):
        find_timezone_info(tz)
        with self.lock:
            self.selected_timezone = tz

    def get_timezone(self):
        with self.lock:
            return self.selected_timezone

    def update(self, state):
        with self.lock:
            self.state = state
            self.history.append(state)
            self.history = self.history[-300:]

    def snapshot(self):
        with self.lock:
            return {
                "state": asdict(self.state),
                "history": [asdict(x) for x in self.history[-100:]],
                "timezones": USA_TIMEZONES,
            }


class Engine:
    def __init__(self, cfg: Config, bus: TelemetryBus):
        self.cfg, self.bus = cfg, bus
        self.running = threading.Event()
        self.running.set()
        self.cycle = 0
        self.semantic_terms = ["ontology", "operator", "relation", "coherence", "drift", "stability", "capacitor_lattice", "timezone_support"]
        self.operator_terms = ["observe", "integrate", "score", "report", "repair", "synchronize"]

    def stop(self):
        self.running.clear()

    def compute(self):
        self.cycle += 1
        ts = now_for_timezone(self.bus.get_timezone())

        concepts = len(self.semantic_terms)
        operators = len(self.operator_terms)
        observations = concepts + operators + random.randint(3, 12)

        coupling = "tight" if self.cycle % 7 != 0 else "loose"
        z_in = 500.0 if coupling == "tight" else 5.0
        noise = 0.0 if coupling == "tight" else random.uniform(5, 40)

        branch = "cushion" if self.cycle % 5 != 0 else "quarantine"
        resistance = 50.0 * (10 if branch == "quarantine" else 1)

        entangled = self.cycle % 4 != 0
        drag = 1.4 if entangled else 1.0

        wave = (math.sin(self.cycle / 5) + 1) / 2
        coherence = clamp(.35 + .25 + clamp(observations / 40) * .25 + wave * .15)
        drift = clamp((1 - coherence) * .45 + abs(math.sin(self.cycle / 7)) * .12 + random.random() * .04 + (.08 if coupling == "loose" else 0))
        stability = clamp(coherence * (1 - drift))

        ceiling = 2000.0
        voltage = ceiling * clamp(self.cycle / 30) + noise
        energy = (voltage ** 2) / max(resistance, 1) * drag

        collapse = "none"
        path = "internalizing"

        if drift > .42 and coupling == "loose":
            path = "externalizing"
            if voltage * (1 + drift * drag) > ceiling * 1.8:
                collapse, status, stability = "breakdown", "BREAKDOWN", 0
                rec = "Externalizing collapse: dielectric breakdown / arc-over. Reset lattice."
            else:
                status, rec = "WATCH", "Externalizing pressure rising. Reduce loose coupling."
        elif drift > .36 and branch == "quarantine":
            path = "internalizing"
            if stability < .25:
                collapse, status, stability, voltage = "deadlock", "DEADLOCK", 0, 0
                rec = "Internalizing collapse: leakage deadlock. Restore useful return path."
            else:
                status, rec = "WATCH", "Internal leakage rising. Reduce quarantine isolation."
        elif stability >= .70:
            status, rec = "STABLE", f"Stable for {ts['timezone_label']} time."
        elif stability >= .45:
            status, rec = "WATCH", f"Monitoring required in {ts['timezone_label']} time."
        else:
            status, rec = "REPAIR", "Reduce drift and stabilize capacitor lattice."

        return TelemetryState(
            **ts, cycle=self.cycle, status=status,
            coherence=round(coherence, 6), drift=round(drift, 6), stability=round(stability, 6),
            concepts=concepts, operators=operators, observations=observations,
            recommendation=rec,
            layer_1_coupling=coupling, layer_1_z_in=z_in,
            layer_2_branch=branch, layer_2_resistance=resistance,
            layer_3_entangled=entangled, layer_3_drag=drag,
            layer_4_path=path, capacitor_voltage=round(voltage, 3),
            capacitor_energy=round(energy, 3), collapse_mode=collapse,
        )

    def write_report(self):
        Path(self.cfg.output_dir).mkdir(exist_ok=True)
        snap = self.bus.snapshot()
        Path(self.cfg.output_dir, "atmos_omega_report.json").write_text(json.dumps(snap, indent=2), encoding="utf-8")

    def run(self):
        while self.running.is_set():
            state = self.compute()
            self.bus.update(state)
            print(f"[ATMOS-Ω] {state.local_time} cycle={state.cycle} status={state.status} V={state.capacitor_voltage:.1f}")
            self.write_report()
            time.sleep(self.cfg.tick_seconds)


DASHBOARD_HTML = r"""
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ATMOS-Ω Dashboard</title><script src="https://cdn.tailwindcss.com"></script>
<style>body{background:#060913;color:#f8fafc;font-family:system-ui}.mono{font-family:monospace}</style></head>
<body>
<header class="p-4 bg-slate-950 border-b border-red-900"><h1 class="text-xl font-black text-red-400">GCITS / ATMOS-Ω Dashboard</h1><p class="text-xs text-slate-400 mono">Runtime telemetry · USA timezone capacitor lattice</p></header>
<main class="p-4 max-w-6xl mx-auto grid gap-4">
<section class="bg-slate-950 border border-slate-800 rounded-xl p-4">
<div class="grid md:grid-cols-3 gap-3">
<div><label class="text-xs text-slate-400 mono">USA Timezone</label><select id="tz" onchange="setTZ()" class="w-full bg-slate-900 p-2 rounded"></select></div>
<div><div class="text-xs text-slate-400 mono">Local Time</div><div id="local" class="text-emerald-400 font-bold mono">--</div></div>
<div><div class="text-xs text-slate-400 mono">UTC</div><div id="utc" class="text-cyan-400 font-bold mono">--</div></div>
</div>
</section>
<section class="grid grid-cols-2 md:grid-cols-4 gap-3">
<div class="bg-slate-950 p-4 rounded border border-slate-800"><b>Coherence</b><div id="coh" class="text-2xl text-red-400 mono">0</div></div>
<div class="bg-slate-950 p-4 rounded border border-slate-800"><b>Drift</b><div id="drift" class="text-2xl text-purple-400 mono">0</div></div>
<div class="bg-slate-950 p-4 rounded border border-slate-800"><b>Stability</b><div id="stab" class="text-2xl text-indigo-400 mono">0</div></div>
<div class="bg-slate-950 p-4 rounded border border-slate-800"><b>Status</b><div id="status" class="text-2xl text-emerald-400 mono">--</div></div>
<div class="bg-slate-950 p-4 rounded border border-slate-800"><b>Voltage</b><div id="volt" class="text-2xl text-amber-400 mono">0V</div></div>
<div class="bg-slate-950 p-4 rounded border border-slate-800"><b>Energy</b><div id="energy" class="text-2xl text-cyan-400 mono">0J</div></div>
<div class="bg-slate-950 p-4 rounded border border-slate-800 col-span-2"><b>Collapse</b><div id="collapse" class="text-2xl text-red-400 mono">none</div></div>
</section>
<section class="bg-slate-950 border border-slate-800 rounded-xl p-4">
<h2 class="text-red-400 font-bold">Recommendation</h2><p id="rec" class="mono text-sm"></p>
</section>
<section class="bg-slate-950 border border-slate-800 rounded-xl p-4">
<h2 class="text-red-400 font-bold">Open Hubs</h2>
<a class="underline text-cyan-300" href="/thought" target="_blank">Open Ω Thought Hub</a>
</section>
</main>
<script>
async function loadTZ(){let r=await fetch('/api/timezones');let z=await r.json();let s=document.getElementById('tz');s.innerHTML='';Object.entries(z).forEach(([k,v])=>{let o=document.createElement('option');o.value=v.iana;o.textContent=k+' — '+v.example;if(v.iana==='America/Chicago')o.selected=true;s.appendChild(o)})}
async function setTZ(){await fetch('/api/set_timezone?tz='+encodeURIComponent(document.getElementById('tz').value));refresh()}
async function refresh(){let r=await fetch('/api/state');let d=await r.json();let s=d.state;local.textContent=s.local_time;utc.textContent=s.utc_time;coh.textContent=Number(s.coherence).toFixed(2);drift.textContent=Number(s.drift).toFixed(2);stab.textContent=Number(s.stability).toFixed(2);status.textContent=s.status;volt.textContent=Number(s.capacitor_voltage).toFixed(1)+'V';energy.textContent=Number(s.capacitor_energy).toFixed(1)+'J';collapse.textContent=s.collapse_mode;rec.textContent=s.recommendation}
window.onload=async()=>{await loadTZ();refresh();setInterval(refresh,1500)}
</script></body></html>
"""

THOUGHT_HTML = r"""
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ω Thought Hub</title><style>
body{margin:0;background:#060913;color:#eaf0ff;font-family:system-ui}header{padding:24px;background:#0b1020;border-bottom:1px solid #26314d}h1{margin:0;color:#7df9ff}.card{background:#111827;border:1px solid #26314d;border-radius:16px;padding:18px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}main{padding:24px;display:grid;gap:18px;max-width:1100px;margin:auto}label{font-size:12px;color:#9aa8c7;text-transform:uppercase}textarea{width:100%;box-sizing:border-box;margin-top:6px;background:#05070d;color:#eaf0ff;border:1px solid #334155;border-radius:10px;padding:10px}button{background:#7df9ff;color:#061018;border:0;border-radius:10px;padding:12px 16px;font-weight:800;cursor:pointer}button.secondary{background:#1f2937;color:#eaf0ff;border:1px solid #334155}pre{white-space:pre-wrap;background:#05070d;border:1px solid #334155;border-radius:12px;padding:14px;overflow:auto}.row{display:flex;gap:10px;flex-wrap:wrap}
</style></head><body>
<header><h1>Ω UDF Thought Hub</h1><p>A → B → C → X → P → Q → R thought integration controller</p></header>
<main>
<section class="card"><div class="grid">
<div><label>A — Assertion</label><textarea id="A"></textarea></div><div><label>B — Basis</label><textarea id="B"></textarea></div><div><label>C — Constraint</label><textarea id="C"></textarea></div><div><label>X — Transformation</label><textarea id="X"></textarea></div><div><label>P — Process</label><textarea id="P"></textarea></div><div><label>Q — Question</label><textarea id="Q"></textarea></div><div><label>R — Resolution</label><textarea id="R"></textarea></div>
</div><br><div class="row"><button onclick="generate()">Generate Ω Output</button><button class="secondary" onclick="downloadJSON()">Export JSON</button><button class="secondary" onclick="downloadTXT()">Export TXT</button><button class="secondary" onclick="downloadMD()">Export Markdown</button><button class="secondary" onclick="clearAll()">Clear</button><a href="/" target="_blank"><button class="secondary">Open Dashboard</button></a></div></section>
<section class="card"><h2>Ω Equation</h2><pre id="equation">Awaiting input...</pre></section>
<section class="card"><h2>Ω Synthesis</h2><pre id="synthesis">Awaiting input...</pre></section>
<section class="card"><h2>Ω Logic Tree</h2><pre id="tree">Awaiting input...</pre></section>
</main>
<script>
function val(id){return document.getElementById(id).value.trim()||`[empty ${id}]`}
function state(){return{timestamp:new Date().toISOString(),A:val('A'),B:val('B'),C:val('C'),X:val('X'),P:val('P'),Q:val('Q'),R:val('R')}}
function outputs(s){let equation=`Ω = ((A[${s.A}] + B[${s.B}]) - C[${s.C}]) × X[${s.X}] → P[${s.P}] ? Q[${s.Q}] ⇒ R[${s.R}]`;let synthesis=`My current thought begins as "${s.A}".\nIt is supported by "${s.B}".\nIt is limited by "${s.C}".\nIt transforms through "${s.X}".\nIt processes by "${s.P}".\nIt is tested by "${s.Q}".\nIt resolves into "${s.R}".`;let tree=`OMEGA UDF THOUGHT TREE\n\nROOT\n├── A: ${s.A}\n├── B: ${s.B}\n├── C: ${s.C}\n├── X: ${s.X}\n├── P: ${s.P}\n├── Q: ${s.Q}\n└── R: ${s.R}`;return{equation,synthesis,tree}}
function generate(){let s=state(),o=outputs(s);equation.textContent=o.equation;synthesis.textContent=o.synthesis;tree.textContent=o.tree;return{...s,...o}}
function dl(name,text,type){let b=new Blob([text],{type});let a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=name;a.click();URL.revokeObjectURL(a.href)}
function stamp(){return new Date().toISOString().replace(/[:.]/g,'-')}
function downloadJSON(){let o=generate();dl(`omega_thought_${stamp()}.json`,JSON.stringify(o,null,2),'application/json')}
function downloadTXT(){let o=generate();dl(`omega_thought_${stamp()}.txt`,`${o.equation}\n\n${o.synthesis}\n\n${o.tree}`,'text/plain')}
function downloadMD(){let o=generate();dl(`omega_thought_${stamp()}.md`,`# Omega UDF Thought\n\n## Equation\n\`\`\`text\n${o.equation}\n\`\`\`\n\n## Synthesis\n${o.synthesis}\n\n## Tree\n\`\`\`text\n${o.tree}\n\`\`\`\n`,'text/markdown')}
function clearAll(){['A','B','C','X','P','Q','R'].forEach(id=>document.getElementById(id).value='');equation.textContent='Awaiting input...';synthesis.textContent='Awaiting input...';tree.textContent='Awaiting input...'}
</script></body></html>
"""


class Handler(BaseHTTPRequestHandler):
    bus: TelemetryBus | None = None

    def log_message(self, *_): return

    def text(self, body, ctype="text/html"):
        b = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def js(self, data):
        self.text(json.dumps(data, indent=2), "application/json")

    def do_GET(self):
        p = urlparse(self.path)
        if p.path in ("/", "/dashboard"):
            return self.text(DASHBOARD_HTML)
        if p.path in ("/thought", "/omega", "/omega_thought_hub.html"):
            return self.text(THOUGHT_HTML)
        if p.path == "/api/timezones":
            return self.js(USA_TIMEZONES)
        if p.path == "/api/set_timezone":
            tz = parse_qs(p.query).get("tz", ["America/Chicago"])[0]
            if Handler.bus: Handler.bus.set_timezone(tz)
            return self.js({"ok": True, "timezone": tz})
        if p.path == "/api/state":
            return self.js(Handler.bus.snapshot() if Handler.bus else {"error": "no bus"})
        self.send_response(404); self.end_headers()


class Server(socketserver.ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def open_url(url):
    for cmd in (
        ["am", "start", "-a", "android.intent.action.VIEW", "-d", url],
        ["termux-open", url],
    ):
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except Exception:
            pass
    try:
        webbrowser.open_new_tab(url)
    except Exception:
        print(f"Open manually: {url}")


def run_server(cfg, bus):
    Handler.bus = bus
    for port in range(cfg.server_port, cfg.server_port + cfg.port_attempts):
        try:
            server = Server((cfg.server_host, port), Handler)
            cfg.server_port = port
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            return server
        except OSError:
            print(f"[PORT BUSY] {port} — trying next...")
    raise RuntimeError("No free port found.")


def main():
    print("[SINGULARITY] Precomputed MASTER MATRIX")
    print("[GCITS / ATMOS-Ω] Starting dashboard + thought hub...")

    cfg = Config()
    bus = TelemetryBus(cfg)
    engine = Engine(cfg, bus)
    server = run_server(cfg, bus)

    base = f"http://{cfg.server_host}:{cfg.server_port}"
    print(f"[DASHBOARD] {base}/dashboard")
    print(f"[THOUGHT HUB] {base}/thought")

    threading.Thread(target=engine.run, daemon=True).start()

    open_url(base + "/dashboard")
    time.sleep(0.8)
    open_url(base + "/thought")

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        engine.stop()
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()