package core

import (
	"fmt"
	"time"
)

const NetTimeout = 10 * time.Second

// Status is a JSON-friendly snapshot for the GUI and CLI.
type Status struct {
	Running    bool   `json:"running"`
	Control    bool   `json:"control"`
	Bootstrap  int    `json:"bootstrap"`
	ExitIP     string `json:"exitIP"`
	Country    string `json:"country"`
	Flag       string `json:"flag"`
	LatencyMS  int    `json:"latencyMs"`
	SocksPort  int    `json:"socksPort"`
	ControlPort int   `json:"controlPort"`
}

// GetStatus gathers a full status snapshot (network calls — run off the UI thread).
func GetStatus(c Config) Status {
	st := Status{SocksPort: c.SocksPort, ControlPort: c.ControlPort, Flag: "🏴", Country: "??"}
	st.Running = PortOpen(c.SocksAddr(), 2*time.Second)
	st.Control = PortOpen(c.ControlAddr(), time.Second)
	if st.Running {
		st.ExitIP = ExitIP(c.SocksAddr(), NetTimeout)
		if st.ExitIP != "" {
			st.Country, st.Flag = CountryOf(c.SocksAddr(), st.ExitIP, NetTimeout)
		}
		st.LatencyMS = LatencyMS(c.SocksAddr(), NetTimeout)
	}
	st.Bootstrap = -1
	if st.Control {
		if t, err := DialControl(c.ControlAddr(), c.ControlPassword, 4*time.Second); err == nil {
			st.Bootstrap = t.BootstrapPercent()
			t.Close()
		}
	}
	if st.Bootstrap < 0 {
		if st.Running {
			st.Bootstrap = 100
		} else {
			st.Bootstrap = 0
		}
	}
	return st
}

// RotateResult is returned after a NEWNYM.
type RotateResult struct {
	IP        string `json:"ip"`
	Country   string `json:"country"`
	Flag      string `json:"flag"`
	LatencyMS int    `json:"latencyMs"`
	Err       string `json:"err"`
}

func Rotate(c Config) RotateResult {
	t, err := DialControl(c.ControlAddr(), c.ControlPassword, NetTimeout)
	if err != nil {
		return RotateResult{Err: err.Error()}
	}
	defer t.Close()
	if err := t.NewIdentity(); err != nil {
		return RotateResult{Err: err.Error()}
	}
	time.Sleep(2 * time.Second)
	ip := ExitIP(c.SocksAddr(), NetTimeout)
	cc, flag := CountryOf(c.SocksAddr(), ip, NetTimeout)
	return RotateResult{IP: ip, Country: cc, Flag: flag, LatencyMS: LatencyMS(c.SocksAddr(), NetTimeout)}
}

// Circuit returns the active circuit hops (authenticated control call).
func GetCircuit(c Config) []Hop {
	t, err := DialControl(c.ControlAddr(), c.ControlPassword, 5*time.Second)
	if err != nil {
		return nil
	}
	defer t.Close()
	return t.Circuit()
}

// DoctorFix enables a password-auth control port. Returns the new Config + message.
func DoctorFix(c Config) (Config, error) {
	pw := RandomPassword()
	hashed, err := HashPassword(pw)
	if err != nil {
		return c, fmt.Errorf("tor --hash-password failed: %w", err)
	}
	if err := WriteManagedBlock(ManagedLines(c, hashed)); err != nil {
		return c, fmt.Errorf("write torrc failed: %w", err)
	}
	if err := ReloadTor(); err != nil {
		return c, fmt.Errorf("reload tor failed: %w", err)
	}
	c.ControlPassword = pw
	if err := c.Save(); err != nil {
		return c, fmt.Errorf("saved torrc but config write failed: %w", err)
	}
	return c, nil
}

// ApplyExitFilter rewrites the managed block keeping password auth.
func ApplyExitFilter(c Config, csv string) error {
	hashed := ""
	if c.ControlPassword != "" {
		if h, err := HashPassword(c.ControlPassword); err == nil {
			hashed = h
		}
	}
	lines := ManagedLines(c, hashed, ExitNodesLines(csv)...)
	if err := WriteManagedBlock(lines); err != nil {
		return err
	}
	return ReloadTor()
}

// Reset removes the managed block and clears the saved password.
func Reset(c Config) (Config, error) {
	if err := ClearManagedBlock(); err != nil {
		return c, err
	}
	_ = ReloadTor()
	c.ControlPassword = ""
	_ = c.Save()
	return c, nil
}
