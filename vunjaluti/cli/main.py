"""``vl`` / ``vunja-luti`` command-line entry point."""

from __future__ import annotations

import argparse
import sys
import time

from .. import __version__, themes
from ..core import firewall, sessions, torrc, wrap
from ..core.config import Config, ensure_dirs
from ..core.engine import TorEngine, TorError
from . import ui


def _engine(cfg: Config) -> TorEngine:
    return TorEngine(cfg.socks_port, cfg.control_port)


# ── commands ─────────────────────────────────────────────────────
def cmd_status(args, cfg, eng):
    st = eng.status()
    ui.banner(cfg.theme)
    state = ui.c("good", "🌐 RUNNING") if st.running else ui.c("bad", "⛔ DEAD")
    print(f"  {ui.c('accent', '╭─ STATUS ' + '─' * 44 + '╮')}")
    print(f"   Tor service   {state}")
    print(f"   Exit IP       {ui.bold(st.exit_ip or '—')}  {st.flag} {st.country}")
    from ..core import geo
    print(f"   Latency       {geo.quality(st.latency_ms)} {st.latency_ms} ms")
    print(f"   SOCKS5        {ui.c('teal', f'127.0.0.1:{st.socks_port}')}")
    print(f"   Control port  {(ui.c('good','open') if st.control else ui.c('warn','closed (vl doctor)'))}")
    print(f"   Killswitch    {(ui.c('good','⚡ engaged') if firewall.is_active() else ui.dim('disarmed'))}")
    print(f"   Exit filter   {ui.c('peach', cfg.exit_filter or 'any')}")
    print(f"  {ui.c('accent', '╰' + '─' * 53 + '╯')}")
    print()
    # circuit map
    circs = eng.circuits()
    if circs:
        hops = circs[0]
        chain = ui.dim(" → ").join(f"{h.flag} {ui.c('accent', h.nickname)}" for h in hops)
        print(f"  Circuit: {chain} {ui.dim('→')} {ui.c('good','🌐')}")
        print()
    return 0


def cmd_start(args, cfg, eng):
    ui.banner(cfg.theme)
    if not eng.is_running():
        ui.say("Starting Tor service…")
        if not eng.start_service():
            ui.err("Tor failed to start — try: sudo systemctl start tor")
            return 1
    # real bootstrap progress
    last = -1
    for _ in range(60):
        p = eng.bootstrap_phase()
        if p < 0:
            break
        if p != last:
            _bar(p, "Bootstrapping Tor")
            last = p
        if p >= 100:
            break
        time.sleep(0.5)
    print()
    if not eng.control_available():
        ui.warn("Control port closed — rotation disabled. Run: vl doctor --fix")
    ui.ok("Tor is up. Rotating every %ss (Ctrl+C to stop)." % cfg.rotate_interval)
    print()

    log = cfg.log_file or str(sessions.auto_log_path(args.session))
    count = 0
    try:
        while True:
            time.sleep(cfg.rotate_interval)
            count += 1
            ip, cc, flag, ms = eng.rotate()
            from ..core import geo
            ts = time.strftime("%H:%M:%S")
            print(f"  {ui.dim(ts)} {ui.c('accent', '#'+str(count))}  "
                  f"{ui.bold(ip or '—')}  {flag} {cc}  {geo.quality(ms)} "
                  f"{ui.c('good', str(ms)+'ms')}")
            sessions.log_rotation(log, ip or "", cc, flag, ms)
    except KeyboardInterrupt:
        print()
        ui.say("Stopped rotation (Tor still running). `vl stop` to stop Tor.")
    return 0


def cmd_stop(args, cfg, eng):
    ui.say("Stopping Tor…")
    if firewall.is_active():
        firewall.disable()
        ui.say("Killswitch disengaged.")
    ui.ok("Tor stopped." if eng.stop_service() else "Tried to stop Tor.")
    return 0


def cmd_rotate(args, cfg, eng):
    ui.say("Requesting new identity…")
    try:
        old = None
        from ..core import geo
        old = geo.exit_ip(cfg.socks_port)
        ip, cc, flag, ms = eng.rotate()
    except TorError as e:
        ui.err(str(e))
        return 1
    print(f"  {ui.dim(old or '—')} {ui.dim('→')} {ui.bold(ip or '—')}  "
          f"{flag} {cc}  {ms}ms")
    return 0


def cmd_anoncheck(args, cfg, eng):
    from ..core import geo
    tor_ip = geo.exit_ip(cfg.socks_port)
    real = geo.real_ip()
    ui.banner(cfg.theme)
    print(f"  Tor exit IP : {ui.c('accent', tor_ip or '—')}")
    print(f"  Real IP     : {ui.dim(real or '—')}")
    if tor_ip and real and tor_ip != real:
        ui.ok("ANONYMOUS — exit IP differs from real IP")
    elif not tor_ip:
        ui.err("Tor not connected")
        return 1
    else:
        ui.err("EXPOSED — IPs match!")
        return 2
    return 0


def cmd_sessions(args, cfg, eng):
    rows = sessions.list_sessions()
    if not rows:
        ui.warn("No saved sessions.")
        return 0
    ui.say("Saved sessions:")
    for s in rows:
        name = s.get("name", "?")
        meta = f"({s.get('rotations', 0)} rotations, started {s.get('started', '?')})"
        print(f"    {ui.bold(name)}  {ui.dim(meta)}")
    return 0


def cmd_wrap(args, cfg, eng):
    if not args.command:
        ui.err('Usage: vl wrap -- hydra -l admin -P pass.txt ssh://target')
        return 1
    ui.banner(cfg.theme)
    ui.say("Routing through Tor SOCKS5…")
    print(f"  {ui.dim('CMD: ' + ' '.join(args.command))}")
    rotate_fn = None
    if cfg.rotate_interval > 0 and eng.control_available():
        rotate_fn = eng.new_identity
        ui.say(f"IP rotation active (every {cfg.rotate_interval}s)")
    elif cfg.rotate_interval > 0:
        ui.warn("Control port closed — rotation disabled (vl doctor --fix)")
    try:
        rc = wrap.wrap(args.command, rotate_fn=rotate_fn,
                       rotate_interval=cfg.rotate_interval)
    except RuntimeError as e:
        ui.err(str(e))
        return 1
    print(f"  {ui.dim('Exit code: ' + str(rc))}")
    return rc


def cmd_autochain(args, cfg, eng):
    path = wrap.build_proxychains_conf(dest="/tmp/vl_proxychains.conf")
    ui.ok(f"proxychains config written: {path}")
    print(f"  {ui.dim('Use: proxychains4 -f ' + path + ' <command>')}")
    return 0


def cmd_doctor(args, cfg, eng):
    from ..core import doctor
    ui.banner(cfg.theme)
    ui.say("Running diagnostics…")
    print()
    fixable_found = False
    for ch in doctor.run_checks(cfg):
        mark = ui.c("good", "✔") if ch.ok else ui.c("bad", "✖")
        print(f"   {mark}  {ch.name:<18} {ui.dim(ch.detail)}")
        fixable_found |= (ch.fixable and not ch.ok)
    print()
    if args.fix and fixable_found:
        ui.say("Applying fixes…")
        ok, msg = doctor.fix_control_port(cfg)
        (ui.ok if ok else ui.err)(msg)
        if ok:
            time.sleep(2)
    elif fixable_found:
        ui.warn("Re-run with `vl doctor --fix` to auto-enable the control port.")
    return 0


def cmd_reset(args, cfg, eng):
    ui.say("Reverting VL changes…")
    torrc.clear_block()
    torrc.reload_tor()
    if firewall.is_active():
        firewall.disable()
    firewall.set_ipv6(False)
    ui.ok("torrc managed block removed, firewall restored, IPv6 re-enabled.")
    return 0


def cmd_export(args, cfg, eng):
    try:
        j, c = sessions.export(args.log, args.out)
    except FileNotFoundError:
        ui.err(f"Log not found: {args.log}")
        return 1
    ui.ok(f"JSON: {j}")
    ui.ok(f"CSV : {c}")
    return 0


def cmd_toolbox(args, cfg, eng):
    ui.banner(cfg.theme)
    items = list(wrap.TOOLBOX.keys())
    print(f"  {ui.c('accent','╭─ TOOLBOX ' + '─'*30 + '╮')}")
    for i, name in enumerate(items, 1):
        print(f"   {ui.bold(str(i))}  {name}")
    print(f"   {ui.bold(str(len(items)+1))}  custom command")
    print(f"  {ui.c('accent','╰' + '─'*40 + '╯')}")
    try:
        choice = int(input("  Select: ").strip())
    except (ValueError, EOFError):
        ui.err("Invalid choice")
        return 1
    if choice == len(items) + 1:
        cmd = input("  Command: ").strip()
        args.command = wrap.to_argv(cmd)
        return cmd_wrap(args, cfg, eng)
    if not 1 <= choice <= len(items):
        ui.err("Invalid choice")
        return 1
    tool = items[choice - 1]
    template = wrap.TOOLBOX[tool]
    fields = {}
    import string
    for _, field, _, _ in string.Formatter().parse(template):
        if field and field not in fields:
            default = {"wordlist": "/usr/share/wordlists/dirb/common.txt",
                       "ports": "80,443,8080"}.get(field, "")
            prompt = f"  {field}" + (f" [{default}]" if default else "") + ": "
            val = input(prompt).strip() or default
            fields[field] = val
    args.command = wrap.to_argv(template.format(**fields))
    return cmd_wrap(args, cfg, eng)


def cmd_monitor(args, cfg, eng):
    ui.banner(cfg.theme)
    ui.say("Circuit health monitor (Ctrl+C to stop)")
    from ..core import geo
    failures = 0
    try:
        while True:
            ip = geo.exit_ip(cfg.socks_port)
            ts = time.strftime("%H:%M:%S")
            if not ip:
                failures += 1
                print(f"  {ui.dim(ts)} {ui.c('bad','⛔ circuit dead')} ({failures})")
                if failures >= 3:
                    ui.warn("Auto-recovering…")
                    try:
                        eng.new_identity()
                    except TorError:
                        eng.restart_service()
                    failures = 0
            else:
                failures = 0
                cc, flag = geo.country_of(ip, cfg.socks_port)
                ms = geo.latency_ms(cfg.socks_port)
                print(f"  {ui.dim(ts)} {ui.c('good','●')} {ui.bold(ip)} {flag} {cc} "
                      f"{geo.quality(ms)} {ms}ms")
            time.sleep(5)
    except KeyboardInterrupt:
        print()
    return 0


def cmd_gui(args, cfg, eng):
    try:
        from ..gui.app import main as gui_main
    except ImportError as e:
        ui.err(f"GUI unavailable: {e} (install python3-pyqt6)")
        return 1
    return gui_main()


# ── argument parser ──────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="vl", description="VUNJA LUTI — Tor proxy + IP rotator + tool wrapper")
    p.add_argument("--version", action="version", version=f"VUNJA LUTI v{__version__}")
    p.add_argument("--theme", help="colour theme: " + ", ".join(themes.PALETTES))
    p.add_argument("--rotate", type=int, metavar="N", help="rotation interval (seconds)")
    p.add_argument("--exit-filter", metavar="CC", help="exit countries, e.g. us,nl,de")
    p.add_argument("--killswitch", action="store_true", help="block non-Tor egress")
    p.add_argument("--leak-guard", action="store_true", help="disable IPv6 + route DNS via Tor")
    p.add_argument("--session", metavar="NAME", help="named session")
    p.add_argument("--log", metavar="FILE", help="rotation JSON log path")
    p.add_argument("--debug", action="store_true", help="show full tracebacks")

    sub = p.add_subparsers(dest="cmd")
    for name, fn, help_ in [
        ("start", cmd_start, "start Tor + rotate IPs"),
        ("stop", cmd_stop, "stop Tor"),
        ("status", cmd_status, "show exit IP, country, latency"),
        ("rotate", cmd_rotate, "force one rotation now"),
        ("anoncheck", cmd_anoncheck, "verify anonymity"),
        ("sessions", cmd_sessions, "list saved sessions"),
        ("autochain", cmd_autochain, "write proxychains config"),
        ("toolbox", cmd_toolbox, "interactive tool selector"),
        ("monitor", cmd_monitor, "live circuit health monitor"),
        ("doctor", cmd_doctor, "diagnose & repair the setup"),
        ("reset", cmd_reset, "revert all VL torrc/firewall changes"),
        ("gui", cmd_gui, "launch the desktop GUI"),
    ]:
        sp = sub.add_parser(name, help=help_)
        sp.set_defaults(func=fn)
        if name == "doctor":
            sp.add_argument("--fix", action="store_true", help="auto-fix issues")

    wp = sub.add_parser("wrap", help="route a command through Tor")
    wp.add_argument("command", nargs=argparse.REMAINDER,
                    help="command after -- (e.g. vl wrap -- nmap -sT target)")
    wp.set_defaults(func=cmd_wrap)

    ep = sub.add_parser("export", help="export a rotation log to JSON+CSV")
    ep.add_argument("log")
    ep.add_argument("out", nargs="?")
    ep.set_defaults(func=cmd_export)

    return p


def _bar(pct: int, label: str) -> None:
    width = 32
    filled = max(0, min(width, pct * width // 100))
    chars = "▁▂▃▄▅▆▇█"
    bar = "".join(ui.c("accent", chars[min(7, i * 8 // max(1, width))]) for i in range(filled))
    rest = ui.dim("·" * (width - filled))
    print(f"\r  {bar}{rest} {pct:3d}%  {ui.c('subtext', label)}", end="", flush=True)


def _apply_globals(args) -> Config:
    cfg = Config.load()
    if args.theme:
        cfg.theme = themes.resolve(args.theme)
    if args.rotate is not None:
        cfg.rotate_interval = args.rotate
    if args.exit_filter is not None:
        cfg.exit_filter = args.exit_filter
    if args.log:
        cfg.log_file = args.log
    ui.set_theme(cfg.theme)
    return cfg


def main(argv: list[str] | None = None) -> int:
    ensure_dirs()
    parser = build_parser()
    args = parser.parse_args(argv)
    cfg = _apply_globals(args)
    eng = _engine(cfg)

    # apply exit filter (valid Tor syntax)
    if args.exit_filter:
        lines = torrc.exit_nodes_lines(args.exit_filter)
        if lines:
            base = torrc.ensure_control_port(cfg.control_port, cfg.socks_port)
            torrc.write_block(base + lines)
            torrc.reload_tor()
            ui.say(f"Exit filter applied: {args.exit_filter}")

    if args.leak_guard:
        firewall.set_ipv6(True)
        ui.say("IPv6 disabled (leak-guard).")
    if args.killswitch:
        ok, msg = firewall.enable(cfg.socks_port)
        (ui.ok if ok else ui.err)(msg)

    func = getattr(args, "func", cmd_start)
    try:
        return func(args, cfg, eng)
    except TorError as e:
        ui.err(str(e))
        return 1
    except KeyboardInterrupt:
        print()
        return 130
    except Exception as e:  # noqa: BLE001
        if args.debug:
            raise
        ui.err(f"{type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
