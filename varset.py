#!/usr/bin/env python3
from __future__ import annotations

import json, socketserver, subprocess, threading, time, webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


THOUGHT_HTML = r"""
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ω Thought Hub</title><style>
body{margin:0;background:#060913;color:#eaf0ff;font-family:system-ui}header{padding:24px;background:#0b1020;border-bottom:1px solid #26314d}h1{margin:0;color:#7df9ff}.card{background:#111827;border:1px solid #26314d;border-radius:16px;padding:18px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}main{padding:24px;display:grid;gap:18px;max-width:1100px;margin:auto}label{font-size:12px;color:#9aa8c7;text-transform:uppercase}textarea{width:100%;box-sizing:border-box;margin-top:6px;background:#05070d;color:#eaf0ff;border:1px solid #334155;border-radius:10px;padding:10px}button{background:#7df9ff;color:#061018;border:0;border-radius:10px;padding:12px 16px;font-weight:800;cursor:pointer}button.secondary{background:#1f2937;color:#eaf0ff;border:1px solid #334155}pre{white-space:pre-wrap;background:#05070d;border:1px solid #334155;border-radius:12px;padding:14px;overflow:auto}.row{display:flex;gap:10px;flex-wrap:wrap}
</style></head><body>
<header><h1>Ω UDF Thought Hub</h1><p>A → B → C → X → P → Q → R thought integration controller</p></header>
<main>
<section class="card"><div class="grid">
<div><label>A — Assertion</label><textarea id="A"></textarea></div>
<div><label>B — Basis</label><textarea id="B"></textarea></div>
<div><label>C — Constraint</label><textarea id="C"></textarea></div>
<div><label>X — Transformation</label><textarea id="X"></textarea></div>
<div><label>P — Process</label><textarea id="P"></textarea></div>
<div><label>Q — Question</label><textarea id="Q"></textarea></div>
<div><label>R — Resolution</label><textarea id="R"></textarea></div>
</div><br><div class="row">
<button onclick="generate()">Generate Ω Output</button>
<button class="secondary" onclick="downloadJSON()">Export JSON</button>
<button class="secondary" onclick="downloadTXT()">Export TXT</button>
<button class="secondary" onclick="downloadMD()">Export Markdown</button>
<button class="secondary" onclick="clearAll()">Clear</button>
</div></section>
<section class="card"><h2>Ω Equation</h2><pre id="equation">Awaiting input...</pre></section>
<section class="card"><h2>Ω Synthesis</h2><pre id="synthesis">Awaiting input...</pre></section>
<section class="card"><h2>Ω Logic Tree</h2><pre id="tree">Awaiting input...</pre></section>
</main>
<script>
function val(id){return document.getElementById(id).value.trim()||`[empty ${id}]`}
function state(){return{timestamp:new Date().toISOString(),A:val('A'),B:val('B'),C:val('C'),X:val('X'),P:val('P'),Q:val('Q'),R:val('R')}}
function outputs(s){let equation=`Ω = ((A[${s.A}] + B[${s.B}]) - C[${s.C}]) × X[${s.X}] → P[${s.P}] ? Q[${s.Q}] ⇒ R[${s.R}]`;let synthesis=`My current thought begins as "${s.A}".\nIt is supported by "${s.B}".\nIt is limited by "${s.C}".\nIt transforms through "${s.X}".\nIt processes by "${s.P}".\nIt is tested by "${s.Q}".\nIt resolves into "${s.R}".`;let tree=`OMEGA UDF THOUGHT TREE\n\nROOT\n├── A: ${s.A}\n├── B: ${s.B}\n├── C: ${s.C}\n├── X: ${s.X}\n├── P: ${s.P}\n├── Q: ${s.Q}\n└── R: ${s.R}`;return{equation,synthesis,tree}}
function generate(){let s=state(),o=outputs(s);equation.textContent=o.equation;synthesis.textContent=o.synthesis;tree.textContent=o.tree;fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...s,...o})}).catch(()=>{});return{...s,...o}}
function dl(name,text,type){let b=new Blob([text],{type});let a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=name;a.click();URL.revokeObjectURL(a.href)}
function stamp(){return new Date().toISOString().replace(/[:.]/g,'-')}
function downloadJSON(){let o=generate();dl(`omega_thought_${stamp()}.json`,JSON.stringify(o,null,2),'application/json')}
function downloadTXT(){let o=generate();dl(`omega_thought_${stamp()}.txt`,`${o.equation}\n\n${o.synthesis}\n\n${o.tree}`,'text/plain')}
function downloadMD(){let o=generate();dl(`omega_thought_${stamp()}.md`,`# Omega UDF Thought\n\n## Equation\n\`\`\`text\n${o.equation}\n\`\`\`\n\n## Synthesis\n${o.synthesis}\n\n## Tree\n\`\`\`text\n${o.tree}\n\`\`\`\n`,'text/markdown')}
function clearAll(){['A','B','C','X','P','Q','R'].forEach(id=>document.getElementById(id).value='');equation.textContent='Awaiting input...';synthesis.textContent='Awaiting input...';tree.textContent='Awaiting input...'}
</script></body></html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): return

    def do_GET(self):
        b = THOUGHT_HTML.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        if self.path != "/api/save":
            self.send_response(404); self.end_headers(); return
        length = int(self.headers.get("Content-Length", "0"))
        data = json.loads(self.rfile.read(length).decode() or "{}")
        out = Path("omega_thought_outputs")
        out.mkdir(exist_ok=True)
        stamp = data.get("timestamp", str(time.time())).replace(":", "-").replace(".", "-")
        (out / f"omega_thought_{stamp}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'{"ok":true}')


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
    webbrowser.open_new_tab(url)


def main():
    host = "127.0.0.1"
    start_port = 8090

    for port in range(start_port, start_port + 50):
        try:
            server = Server((host, port), Handler)
            break
        except OSError:
            continue
    else:
        raise RuntimeError("No free port found.")

    threading.Thread(target=server.serve_forever, daemon=True).start()

    url = f"http://{host}:{port}"
    print(f"[Ω THOUGHT HUB] {url}")
    open_url(url)

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping Ω Thought Hub...")
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()