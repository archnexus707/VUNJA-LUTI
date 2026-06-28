// VUNJA LUTI — Go proof-of-concept CLI.
//
// A single static binary (no runtime deps) that controls Tor over the control
// protocol with password auth, rotates exit IPs, and shares the Python build's
// ~/.config/vl/config.json + /etc/tor/torrc managed block.
package main

import (
	"fmt"
	"os"
	"time"
)

const version = "6.0.1"

const netTimeout = 10 * time.Second

func main() {
	args := os.Args[1:]
	cmd := "status"
	if len(args) > 0 {
		cmd = args[0]
		args = args[1:]
	}
	cfg := loadConfig()

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

func cmdStatus(c Config) {
	printBanner()
	running := portOpen(c.socksAddr(), 2*time.Second)
	state := col(cRed, "⛔ DEAD")
	if running {
		state = col(cGreen, "🌐 RUNNING")
	}
	fmt.Printf("   Tor service   %s\n", state)
	var ip, cc, flag string
	ms := 0
	if running {
		ip = exitIP(c.socksAddr(), netTimeout)
		if ip != "" {
			cc, flag = countryOf(c.socksAddr(), ip, netTimeout)
		}
		ms = latencyMS(c.socksAddr(), netTimeout)
	}
	if ip == "" {
		ip = "—"
	}
	fmt.Printf("   Exit IP       %s%s%s  %s %s\n", bold, ip, reset, flag, cc)
	fmt.Printf("   Latency       %s %d ms\n", quality(ms), ms)
	fmt.Printf("   SOCKS5        %s\n", col(cCyan, c.socksAddr()))
	ctrl := portOpen(c.controlAddr(), time.Second)
	cs := col(cYellow, "closed (vl doctor --fix)")
	if ctrl {
		cs = col(cGreen, "open")
	}
	fmt.Printf("   Control port  %s\n", cs)
	fmt.Println()
}

func cmdRotate(c Config) {
	say("Requesting new identity…")
	old := exitIP(c.socksAddr(), netTimeout)
	t, err := dialControl(c.controlAddr(), c.ControlPassword, netTimeout)
	if err != nil {
		errMsg(err.Error())
		os.Exit(1)
	}
	defer t.close()
	if err := t.newIdentity(); err != nil {
		errMsg("rotate failed: " + err.Error())
		os.Exit(1)
	}
	time.Sleep(2 * time.Second)
	ip := exitIP(c.socksAddr(), netTimeout)
	cc, flag := countryOf(c.socksAddr(), ip, netTimeout)
	ms := latencyMS(c.socksAddr(), netTimeout)
	if old == "" {
		old = "—"
	}
	if ip == "" {
		ip = "—"
	}
	fmt.Printf("  %s%s%s %s→%s %s%s%s  %s %s  %d ms\n",
		dim, old, reset, dim, reset, bold, ip, reset, flag, cc, ms)
}

func cmdAnon(c Config) {
	printBanner()
	tor := exitIP(c.socksAddr(), netTimeout)
	real := directIP(8 * time.Second)
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

func cmdDoctor(c Config, fix bool) {
	printBanner()
	say("Diagnostics…")
	fmt.Println()
	type chk struct {
		name string
		ok   bool
		note string
	}
	running := portOpen(c.socksAddr(), 2*time.Second)
	ctrlOpen := portOpen(c.controlAddr(), time.Second)
	authOK := false
	if ctrlOpen {
		if t, err := dialControl(c.controlAddr(), c.ControlPassword, 4*time.Second); err == nil {
			authOK = true
			t.close()
		}
	}
	checks := []chk{
		{"tor running", running, ifElse(running, "SOCKS on "+c.socksAddr(), "not listening — start tor")},
		{"control auth", authOK, ifElse(authOK, "authenticated on "+c.controlAddr(), "needs setup — run with --fix")},
	}
	for _, k := range checks {
		mark := col(cGreen, "✔")
		if !k.ok {
			mark = col(cRed, "✖")
		}
		fmt.Printf("   %s  %-14s %s\n", mark, k.name, col(dim, k.note))
	}
	fmt.Println()
	if fix && !authOK {
		say("Setting up password-auth control port…")
		pw := randomPassword()
		hashed, err := hashPassword(pw)
		if err != nil {
			errMsg("tor --hash-password failed: " + err.Error())
			os.Exit(1)
		}
		if err := writeManagedBlock(managedLines(c, hashed)); err != nil {
			errMsg("write torrc failed: " + err.Error())
			os.Exit(1)
		}
		if err := reloadTor(); err != nil {
			errMsg("reload tor failed: " + err.Error())
			os.Exit(1)
		}
		c.ControlPassword = pw
		if err := c.save(); err != nil {
			warn("saved torrc but could not write config: " + err.Error())
		}
		okMsg("control port enabled with password auth; tor reloaded")
	} else if !authOK {
		warn("Re-run with `vl doctor --fix` to enable rotation.")
	}
}

func cmdReset(c Config) {
	say("Reverting VL torrc changes…")
	if err := writeManagedBlockEmpty(); err != nil {
		errMsg(err.Error())
		os.Exit(1)
	}
	reloadTor()
	c.ControlPassword = ""
	c.save()
	okMsg("managed torrc block removed; tor reloaded")
}

func writeManagedBlockEmpty() error {
	base := stripBlock(readTorrc())
	tmp, err := os.CreateTemp("", "vl-torrc-*.conf")
	if err != nil {
		return err
	}
	name := tmp.Name()
	tmp.WriteString(base)
	tmp.Close()
	defer os.Remove(name)
	return runPriv("", "install", "-m", "644", name, torrcPath)
}

func orDash(s string) string {
	if s == "" {
		return "—"
	}
	return s
}

func ifElse(cond bool, a, b string) string {
	if cond {
		return a
	}
	return b
}

func usage() {
	fmt.Printf(`VUNJA LUTI v%s (go) — Tor proxy + IP rotator

usage: vl <command>

  status        show exit IP, country, latency, control state
  rotate        request a new Tor identity (needs `+"`vl doctor --fix`"+`)
  anoncheck     verify exit IP differs from real IP
  doctor [--fix]  diagnose, and with --fix enable password-auth control port
  reset         remove VL's torrc managed block
  version       print version

Shares ~/.config/vl/config.json + /etc/tor/torrc with the Python build.
`, version)
}
