package main

// Managed torrc editing + doctor fix. Uses the SAME fenced markers as the Python
// build so both tools manage one shared block.

import (
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"os"
	"os/exec"
	"strings"
)

const (
	torrcPath  = "/etc/tor/torrc"
	blockBegin = "# >>> VUNJA-LUTI managed block >>>"
	blockEnd   = "# <<< VUNJA-LUTI managed block <<<"
)

func escalator() []string {
	if os.Geteuid() == 0 {
		return nil
	}
	// no controlling terminal + a display -> graphical prompt
	if fi, _ := os.Stdin.Stat(); fi != nil && (fi.Mode()&os.ModeCharDevice) == 0 {
		if os.Getenv("DISPLAY") != "" {
			if _, err := exec.LookPath("pkexec"); err == nil {
				return []string{"pkexec"}
			}
		}
	}
	return []string{"sudo"}
}

func runPriv(stdin string, argv ...string) error {
	full := append(escalator(), argv...)
	cmd := exec.Command(full[0], full[1:]...)
	if stdin != "" {
		cmd.Stdin = strings.NewReader(stdin)
	}
	out, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("%v: %s", err, strings.TrimSpace(string(out)))
	}
	return nil
}

func readTorrc() string {
	b, err := os.ReadFile(torrcPath)
	if err == nil {
		return string(b)
	}
	// privileged read
	full := append(escalator(), "cat", torrcPath)
	out, _ := exec.Command(full[0], full[1:]...).Output()
	return string(out)
}

func stripBlock(text string) string {
	var out []string
	skip := false
	for _, ln := range strings.Split(text, "\n") {
		t := strings.TrimSpace(ln)
		if t == blockBegin {
			skip = true
			continue
		}
		if t == blockEnd {
			skip = false
			continue
		}
		if !skip {
			out = append(out, ln)
		}
	}
	return strings.TrimRight(strings.Join(out, "\n"), "\n") + "\n"
}

func writeManagedBlock(lines []string) error {
	base := stripBlock(readTorrc())
	block := blockBegin + "\n" + strings.Join(lines, "\n") + "\n" + blockEnd
	content := strings.TrimRight(base, "\n") + "\n\n" + block + "\n"

	tmp, err := os.CreateTemp("", "vl-torrc-*.conf")
	if err != nil {
		return err
	}
	tmpName := tmp.Name()
	tmp.WriteString(content)
	tmp.Close()
	defer os.Remove(tmpName)
	return runPriv("", "install", "-m", "644", tmpName, torrcPath)
}

func reloadTor() error {
	if err := runPriv("", "systemctl", "reload", "tor"); err == nil {
		return nil
	}
	return runPriv("", "systemctl", "reload", "tor@default")
}

func hashPassword(pw string) (string, error) {
	tor, err := exec.LookPath("tor")
	if err != nil {
		tor = "/usr/sbin/tor"
	}
	out, err := exec.Command(tor, "--hash-password", pw).Output()
	if err != nil {
		return "", err
	}
	for _, ln := range strings.Split(string(out), "\n") {
		ln = strings.TrimSpace(ln)
		if strings.HasPrefix(ln, "16:") {
			return ln, nil
		}
	}
	return "", fmt.Errorf("could not parse hashed password")
}

func randomPassword() string {
	b := make([]byte, 24)
	_, _ = rand.Read(b)
	return base64.RawURLEncoding.EncodeToString(b)
}

func managedLines(c Config, hashed string, extra ...string) []string {
	lines := []string{
		fmt.Sprintf("SocksPort %d", c.SocksPort),
		fmt.Sprintf("ControlPort %d", c.ControlPort),
	}
	if hashed != "" {
		lines = append(lines, "HashedControlPassword "+hashed)
	} else {
		lines = append(lines, "CookieAuthentication 1", "CookieAuthFileGroupReadable 1")
	}
	return append(lines, extra...)
}

// exitNodesLines builds valid Tor syntax: ExitNodes {us},{nl},{de}
func exitNodesLines(csv string) []string {
	var codes []string
	for _, p := range strings.Split(csv, ",") {
		p = strings.ToLower(strings.TrimSpace(p))
		if p != "" {
			codes = append(codes, "{"+p+"}")
		}
	}
	if len(codes) == 0 {
		return nil
	}
	return []string{"ExitNodes " + strings.Join(codes, ","), "StrictNodes 1"}
}
