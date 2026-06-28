// VUNJA LUTI — Wails frontend logic. Every backend call is async (Promise), and
// the Go side runs each on a goroutine, so the UI never blocks.

const $ = (id) => document.getElementById(id);
const App = () => (window.go && window.go.main && window.go.main.App) || null;
const rt = () => window.runtime || null;

let rotations = 0;
let startedAt = null;
const latencies = [];

// ---------- tabs ----------
document.querySelectorAll(".tab").forEach((t) => {
  t.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((x) => x.classList.remove("active"));
    document.querySelectorAll(".page").forEach((x) => x.classList.remove("active"));
    t.classList.add("active");
    $(t.dataset.tab).classList.add("active");
  });
});

// ---------- theme ----------
$("theme").addEventListener("change", (e) => {
  document.documentElement.dataset.theme = e.target.value;
  drawSpark();
  if (App()) App().SetTheme(e.target.value);
});

function setStatusbar(msg) { $("statusbar").textContent = msg; }

// ---------- status polling ----------
async function poll() {
  if (!App()) return;
  try {
    const st = await App().Status();
    renderStatus(st);
  } catch (e) { /* ignore */ }
  try {
    const hops = await App().Circuit();
    renderCircuit(hops);
  } catch (e) { /* ignore */ }
}

function renderStatus(st) {
  const dot = $("dot");
  if (st.running) {
    $("state").textContent = "RUNNING";
    dot.className = "dot on";
    if (!startedAt) startedAt = Date.now();
  } else {
    $("state").textContent = "STOPPED";
    dot.className = "dot off";
    startedAt = null;
  }
  $("ip").textContent = st.exitIP || "—";
  $("country").textContent = (st.flag || "") + " " + (st.country || "—");
  $("latency").textContent = quality(st.latencyMs) + " " + st.latencyMs + " ms";
  $("rotations").textContent = rotations;
  $("uptime").textContent = startedAt ? fmtUptime(Date.now() - startedAt) : "—";
  const b = Math.max(0, Math.min(100, st.bootstrap));
  $("boot").style.width = b + "%";
  $("bootlabel").textContent = "Tor bootstrap " + b + "%";
  if (st.latencyMs > 0) pushLatency(st.latencyMs);
}

function renderCircuit(hops) {
  const el = $("circuit");
  if (!hops || hops.length === 0) {
    el.innerHTML = '<span class="muted">no circuit yet — start Tor</span>';
    return;
  }
  const nodes = [{ g: "🖥", l: "You" }];
  const labels = ["guard", "middle", "exit"];
  hops.slice(0, 3).forEach((h, i) => nodes.push({ g: h.flag, l: labels[i] || "relay" }));
  nodes.push({ g: "🌐", l: "Internet" });
  el.innerHTML = nodes
    .map((n) => `<div class="hop"><div class="node">${n.g}</div><div class="lbl">${n.l}</div></div>`)
    .join('<span class="arrow">→</span>');
}

function quality(ms) {
  if (ms <= 0) return "⚫";
  if (ms < 300) return "🟢";
  if (ms < 800) return "🟡";
  return "🔴";
}
function fmtUptime(ms) {
  const s = Math.floor(ms / 1000);
  return Math.floor(s / 60) + "m " + (s % 60) + "s";
}

// ---------- buttons ----------
$("start").addEventListener("click", async () => {
  if (!App()) return;
  setStatusbar("Starting Tor…");
  const err = await App().StartTor();
  setStatusbar(err ? "Start failed: " + err : "Tor started");
  poll();
});
$("stop").addEventListener("click", async () => {
  if (!App()) return;
  $("auto").checked = false;
  const err = await App().StopTor();
  setStatusbar(err ? "Stop failed: " + err : "Tor stopped");
  poll();
});
$("rotate").addEventListener("click", async () => {
  if (!App()) return;
  setStatusbar("Rotating…");
  const r = await App().Rotate();
  if (r.err) setStatusbar("Rotate failed: " + r.err);
});
$("auto").addEventListener("change", (e) => {
  if (!App()) return;
  if (e.target.checked) { App().StartAuto(); setStatusbar("Auto-rotate on"); }
  else { App().StopAuto(); setStatusbar("Auto-rotate off"); }
});

// ---------- events from backend ----------
function wireEvents() {
  if (!rt()) return;
  rt().EventsOn("rotated", (r) => {
    rotations++;
    const ts = new Date().toLocaleTimeString();
    appendLine("feed", `${ts}  #${rotations}  ${r.ip}  ${r.flag} ${r.country}  ${r.latencyMs}ms`);
    $("ip").textContent = r.ip || "—";
    $("country").textContent = (r.flag || "") + " " + (r.country || "—");
    $("rotations").textContent = rotations;
    if (r.latencyMs > 0) pushLatency(r.latencyMs);
  });
  rt().EventsOn("tool:line", (l) => appendLine("output", l));
  rt().EventsOn("tool:done", (code) => {
    appendLine("output", `[exit code ${code}]`);
    $("run").disabled = false; $("kill").disabled = true;
  });
}

function appendLine(id, line) {
  const el = $(id);
  el.textContent += (el.textContent ? "\n" : "") + line;
  el.scrollTop = el.scrollHeight;
}

// ---------- sparkline ----------
function pushLatency(v) { latencies.push(v); if (latencies.length > 60) latencies.shift(); drawSpark(); }
function cssVar(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
function drawSpark() {
  const c = $("spark"); if (!c) return;
  const dpr = window.devicePixelRatio || 1;
  const w = c.clientWidth, h = c.clientHeight || 70;
  c.width = w * dpr; c.height = h * dpr;
  const ctx = c.getContext("2d"); ctx.scale(dpr, dpr); ctx.clearRect(0, 0, w, h);
  if (latencies.length < 2) {
    ctx.fillStyle = cssVar("--sub"); ctx.font = "12px monospace";
    ctx.fillText("collecting latency…", 8, h / 2); return;
  }
  const lo = Math.min(...latencies), hi = Math.max(...latencies), rng = Math.max(1, hi - lo);
  const pad = 6, step = (w - 2 * pad) / (latencies.length - 1);
  const pts = latencies.map((v, i) => [pad + i * step, h - pad - ((v - lo) / rng) * (h - 2 * pad)]);
  const accent = cssVar("--accent");
  ctx.beginPath(); ctx.moveTo(pts[0][0], h - pad);
  pts.forEach((p) => ctx.lineTo(p[0], p[1]));
  ctx.lineTo(pts[pts.length - 1][0], h - pad); ctx.closePath();
  ctx.fillStyle = accent + "33"; ctx.fill();
  ctx.beginPath(); pts.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
  ctx.strokeStyle = accent; ctx.lineWidth = 2; ctx.stroke();
  ctx.fillStyle = cssVar("--good");
  ctx.beginPath(); ctx.arc(pts[pts.length - 1][0], pts[pts.length - 1][1], 3, 0, 7); ctx.fill();
  ctx.fillStyle = cssVar("--sub"); ctx.font = "11px monospace";
  ctx.fillText(`${latencies[latencies.length - 1]} ms (min ${lo}/max ${hi})`, 6, 12);
}
window.addEventListener("resize", drawSpark);

// ---------- toolbox ----------
async function initToolbox() {
  if (!App()) return;
  const tpl = await App().ToolTemplates();
  const sel = $("tool"); sel.innerHTML = "";
  Object.keys(tpl).forEach((k) => { const o = document.createElement("option"); o.value = k; o.textContent = k; sel.appendChild(o); });
  const custom = document.createElement("option"); custom.value = "__custom__"; custom.textContent = "custom"; sel.appendChild(custom);
  window._templates = tpl;
  sel.addEventListener("change", () => buildToolForm(sel.value));
  buildToolForm(sel.value);
}
function buildToolForm(tool) {
  const host = $("toolform"); host.innerHTML = "";
  if (tool === "__custom__") { host.appendChild(field("command", "full command, e.g. curl https://example.com")); return; }
  const tpl = window._templates[tool] || "";
  const seen = {};
  (tpl.match(/\{(\w+)\}/g) || []).forEach((m) => {
    const name = m.slice(1, -1);
    if (seen[name]) return; seen[name] = 1;
    const def = { wordlist: "/usr/share/wordlists/dirb/common.txt", ports: "80,443,8080", service: "ssh" }[name] || "";
    host.appendChild(field(name, name, def));
  });
}
function field(name, placeholder, val) {
  const row = document.createElement("div"); row.className = "row";
  const lbl = document.createElement("label"); lbl.textContent = name;
  const inp = document.createElement("input"); inp.placeholder = placeholder; inp.value = val || ""; inp.dataset.f = name;
  row.appendChild(lbl); row.appendChild(inp); return row;
}
$("run").addEventListener("click", () => {
  if (!App()) return;
  const tool = $("tool").value;
  const inputs = {}; document.querySelectorAll("#toolform input").forEach((i) => (inputs[i.dataset.f] = i.value.trim()));
  let cmd;
  if (tool === "__custom__") cmd = inputs["command"] || "";
  else { cmd = window._templates[tool]; for (const k in inputs) cmd = cmd.replaceAll("{" + k + "}", inputs[k]); cmd = cmd.replace(/\{auth\}/g, ""); }
  const args = shellSplit(cmd);
  if (!args.length) return;
  $("output").textContent = "$ " + args.join(" ");
  $("run").disabled = true; $("kill").disabled = false;
  App().RunTool(args);
});
$("kill").addEventListener("click", () => { setStatusbar("Stop the tool from a terminal (kill not wired in PoC)"); });

function shellSplit(s) {
  const out = []; const re = /"([^"]*)"|'([^']*)'|(\S+)/g; let m;
  while ((m = re.exec(s)) !== null) out.push(m[1] ?? m[2] ?? m[3]);
  return out;
}

// ---------- settings ----------
$("interval").addEventListener("change", (e) => { if (App()) App().SetInterval(parseInt(e.target.value || "60", 10)); });
$("applyexit").addEventListener("click", async () => {
  if (!App()) return;
  const err = await App().ApplyExitFilter($("exitfilter").value.trim());
  setStatusbar(err ? "Exit filter failed: " + err : "Exit filter applied");
});
$("doctor").addEventListener("click", async () => {
  if (!App()) return;
  const checks = await App().Doctor();
  $("doctorout").textContent = checks.map((c) => `${c.ok ? "✔" : "✖"}  ${c.name.padEnd(14)} ${c.note}`).join("\n");
});
$("doctorfix").addEventListener("click", async () => {
  if (!App()) return;
  setStatusbar("Enabling control port…");
  const err = await App().DoctorFix();
  setStatusbar(err ? "Doctor fix failed: " + err : "Control port enabled — rotation ready");
});
$("reset").addEventListener("click", async () => {
  if (!App()) return;
  const err = await App().Reset();
  $("auto").checked = false;
  setStatusbar(err ? "Reset failed: " + err : "All VL changes reverted");
});

// ---------- boot ----------
async function boot() {
  wireEvents();
  if (App()) {
    try {
      const cfg = await App().GetConfig();
      if (cfg.theme) { $("theme").value = cfg.theme; document.documentElement.dataset.theme = cfg.theme; }
      if (cfg.rotate_interval) $("interval").value = cfg.rotate_interval;
      if (cfg.exit_filter) $("exitfilter").value = cfg.exit_filter;
    } catch (e) {}
    await initToolbox();
  }
  poll();
  setInterval(poll, 4000);
}
// Wails injects window.go after load; wait for it.
if (App()) boot();
else window.addEventListener("DOMContentLoaded", () => setTimeout(boot, 300));
