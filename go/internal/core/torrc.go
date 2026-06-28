package core

// Managed torrc editing — same fenced markers as the Python build, so both
// tools manage one shared block. Privilege via pkexec (GUI) or sudo (terminal).

import (
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"os"
	"os/exec"
	"strings"
)

const (
	TorrcPath  = "/etc/tor/torrc"
	blockBegin = "# >>> VUNJA-LUTI managed block >>>"
	blockEnd   = "# <<< VUNJA-LUTI managed block <<<"
)

func Escalator() []string {
	if os.Geteuid() == 0 {
		return nil
	}
	if fi, _ := os.Stdin.Stat(); fi != nil && (fi.Mode()&os.ModeCharDevice) == 0 {
		if os.Getenv("DISPLAY") != "" {
			if _, err := exec.LookPath("pkexec"); err == nil {
				return []string{"pkexec"}
			}
		}
	}
	return []string{"sudo"}
}

func RunPriv(stdin string, argv ...string) error {
	full := append(Escalator(), argv...)
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

func ReadTorrc() string {
	if b, err := os.ReadFile(TorrcPath); err == nil {
		return string(b)
	}
	full := append(Escalator(), "cat", TorrcPath)
	out, _ := exec.Command(full[0], full[1:]...).Output()
	return string(out)
}

func StripBlock(text string) string {
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

func installTorrc(content string) error {
	tmp, err := os.CreateTemp("", "vl-torrc-*.conf")
	if err != nil {
		return err
	}
	name := tmp.Name()
	tmp.WriteString(content)
	tmp.Close()
	defer os.Remove(name)
	return RunPriv("", "install", "-m", "644", name, TorrcPath)
}

func WriteManagedBlock(lines []string) error {
	base := StripBlock(ReadTorrc())
	block := blockBegin + "\n" + strings.Join(lines, "\n") + "\n" + blockEnd
	return installTorrc(strings.TrimRight(base, "\n") + "\n\n" + block + "\n")
}

func ClearManagedBlock() error {
	return installTorrc(StripBlock(ReadTorrc()))
}

func ReloadTor() error {
	if err := RunPriv("", "systemctl", "reload", "tor"); err == nil {
		return nil
	}
	return RunPriv("", "systemctl", "reload", "tor@default")
}

func StartTor() error {
	if err := RunPriv("", "systemctl", "start", "tor"); err == nil {
		return nil
	}
	return RunPriv("", "systemctl", "start", "tor@default")
}

func StopTor() error {
	_ = RunPriv("", "systemctl", "stop", "tor@default")
	return RunPriv("", "systemctl", "stop", "tor")
}

func HashPassword(pw string) (string, error) {
	tor, err := exec.LookPath("tor")
	if err != nil {
		tor = "/usr/sbin/tor"
	}
	out, err := exec.Command(tor, "--hash-password", pw).Output()
	if err != nil {
		return "", err
	}
	for _, ln := range strings.Split(string(out), "\n") {
		if ln = strings.TrimSpace(ln); strings.HasPrefix(ln, "16:") {
			return ln, nil
		}
	}
	return "", fmt.Errorf("could not parse hashed password")
}

func RandomPassword() string {
	b := make([]byte, 24)
	_, _ = rand.Read(b)
	return base64.RawURLEncoding.EncodeToString(b)
}

func ManagedLines(c Config, hashed string, extra ...string) []string {
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

// ExitNodesLines builds valid Tor syntax: ExitNodes {us},{nl},{de}
func ExitNodesLines(csv string) []string {
	var codes []string
	for _, p := range strings.Split(csv, ",") {
		if p = strings.ToLower(strings.TrimSpace(p)); p != "" {
			codes = append(codes, "{"+p+"}")
		}
	}
	if len(codes) == 0 {
		return nil
	}
	return []string{"ExitNodes " + strings.Join(codes, ","), "StrictNodes 1"}
}
