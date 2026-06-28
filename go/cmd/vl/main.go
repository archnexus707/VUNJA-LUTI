// VUNJA LUTI — Go CLI. A single static binary sharing the engine in internal/core
// with the Wails GUI.
package main

import (
	"fmt"
	"os"
	"time"

	"github.com/archnexus707/vunja-luti/internal/core"
)

const version = "6.0.1"

func main() {
	args := os.Args[1:]
	cmd := "status"
	if len(args) > 0 {
		cmd = args[0]
		args = args[1:]
	}
	cfg := core.Load()

	switch cmd {
	case "version", "--version", "-v":
		fmt.Printf("VUNJA LUTI v%s (go)\n", version)
	case "status":
		cmdStatus(cfg)
	case "rotate":
		cmdRotate(cfg)
	case "doctor":
		cmdDoctor(cfg, has(args, "--fix"))
	case "anoncheck":
		cmdAnon(cfg)
	case "reset":
		cmdReset(cfg)
	case "help", "--help", "-h":
		usage()
	default:
		errMsg("unknown command: " + cmd)
		usage()
		os.Exit(2)
	}
}

func has(args []string, flag string) bool {
	for _, a := range args {
		if a == flag {
			return true
		}
	}
	return false
}

func cmdStatus(c core.Config) {
	printBanner()
	st := core.GetStatus(c)
	state := col(cRed, "⛔ DEAD")
	if st.Running {
		state = col(cGreen, "🌐 RUNNING")
	}
	fmt.Printf("   Tor service   %s\n", state)
	fmt.Printf("   Exit IP       %s%s%s  %s %s\n", bold, orDash(st.ExitIP), reset, st.Flag, st.Country)
	fmt.Printf("   Latency       %s %d ms\n", core.Quality(st.LatencyMS), st.LatencyMS)
	fmt.Printf("   SOCKS5        %s\n", col(cCyan, c.SocksAddr()))
	cs := col(cYellow, "closed (vl doctor --fix)")
	if st.Control {
		cs = col(cGreen, "open")
	}
	fmt.Printf("   Control port  %s\n", cs)
	if hops := core.GetCircuit(c); len(hops) > 0 {
		line := "  Circuit: "
		for _, h := range hops {
			line += fmt.Sprintf("%s %s%s%s  ", h.Flag, col(cAccent, h.Nick), "", "")
		}
		fmt.Println()
		fmt.Println(line + col(cGreen, "🌐"))
	}
	fmt.Println()
}

func cmdRotate(c core.Config) {
	say("Requesting new identity…")
	old := core.ExitIP(c.SocksAddr(), core.NetTimeout)
	r := core.Rotate(c)
	if r.Err != "" {
		errMsg("rotate failed: " + r.Err)
		os.Exit(1)
	}
	fmt.Printf("  %s%s%s %s→%s %s%s%s  %s %s  %d ms\n",
		dim, orDash(old), reset, dim, reset, bold, orDash(r.IP), reset, r.Flag, r.Country, r.LatencyMS)
}

func cmdAnon(c core.Config) {
	printBanner()
	tor := core.ExitIP(c.SocksAddr(), core.NetTimeout)
	real := core.DirectIP(8 * time.Second)
	fmt.Printf("  Tor exit IP : %s\n", col(cAccent, orDash(tor)))
	fmt.Printf("  Real IP     : %s\n", col(dim, orDash(real)))
	switch {
	case tor == "":
		errMsg("Tor not connected")
		os.Exit(1)
	case real != "" && tor != real:
		okMsg("ANONYMOUS — exit IP differs from real IP")
	default:
		errMsg("EXPOSED — IPs match!")
		os.Exit(2)
	}
}

func cmdDoctor(c core.Config, fix bool) {
	printBanner()
	say("Diagnostics…")
	fmt.Println()
	running := core.PortOpen(c.SocksAddr(), 2*time.Second)
	ctrlOpen := core.PortOpen(c.ControlAddr(), time.Second)
	authOK := false
	if ctrlOpen {
		if t, err := core.DialControl(c.ControlAddr(), c.ControlPassword, 4*time.Second); err == nil {
			authOK = true
			t.Close()
		}
	}
	row("tor running", running, ifElse(running, "SOCKS on "+c.SocksAddr(), "not listening — start tor"))
	row("control auth", authOK, ifElse(authOK, "authenticated on "+c.ControlAddr(), "needs setup — run with --fix"))
	fmt.Println()
	if fix && !authOK {
		say("Setting up password-auth control port…")
		nc, err := core.DoctorFix(c)
		if err != nil {
			errMsg(err.Error())
			os.Exit(1)
		}
		_ = nc
		okMsg("control port enabled with password auth; tor reloaded")
	} else if !authOK {
		warn("Re-run with `vl doctor --fix` to enable rotation.")
	}
}

func cmdReset(c core.Config) {
	say("Reverting VL torrc changes…")
	if _, err := core.Reset(c); err != nil {
		errMsg(err.Error())
		os.Exit(1)
	}
	okMsg("managed torrc block removed; tor reloaded")
}

func row(name string, ok bool, note string) {
	mark := col(cGreen, "✔")
	if !ok {
		mark = col(cRed, "✖")
	}
	fmt.Printf("   %s  %-14s %s\n", mark, name, col(dim, note))
}

func orDash(s string) string {
	if s == "" {
		return "—"
	}
	return s
}

func ifElse(c bool, a, b string) string {
	if c {
		return a
	}
	return b
}

func usage() {
	fmt.Printf(`VUNJA LUTI v%s (go) — Tor proxy + IP rotator

usage: vl <command>

  status          exit IP, country, latency, circuit, control state
  rotate          request a new Tor identity (needs `+"`vl doctor --fix`"+`)
  anoncheck       verify exit IP differs from real IP
  doctor [--fix]  diagnose; --fix enables password-auth control port
  reset           remove VL's torrc managed block
  version

Shares ~/.config/vl/config.json + /etc/tor/torrc with the Python build & GUI.
`, version)
}
