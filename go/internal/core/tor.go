package core

// Tor control-protocol client (text protocol over TCP), standard library only.
// Password auth (HashedControlPassword) — same scheme as the Python build.

import (
	"bufio"
	"fmt"
	"net"
	"strconv"
	"strings"
	"time"
)

type TorCtl struct {
	conn net.Conn
	r    *bufio.Reader
}

func DialControl(addr, password string, timeout time.Duration) (*TorCtl, error) {
	c, err := net.DialTimeout("tcp", addr, timeout)
	if err != nil {
		return nil, fmt.Errorf("cannot reach control port %s (run `vl doctor --fix`)", addr)
	}
	_ = c.SetDeadline(time.Now().Add(timeout))
	t := &TorCtl{conn: c, r: bufio.NewReader(c)}

	auth := "AUTHENTICATE"
	if password != "" {
		auth = fmt.Sprintf("AUTHENTICATE %q", password)
	}
	if _, err := t.cmd(auth); err != nil {
		c.Close()
		return nil, fmt.Errorf("control authentication failed: %w (run `vl doctor --fix`)", err)
	}
	return t, nil
}

func (t *TorCtl) cmd(line string) ([]string, error) {
	if _, err := t.conn.Write([]byte(line + "\r\n")); err != nil {
		return nil, err
	}
	var lines []string
	for {
		s, err := t.r.ReadString('\n')
		if err != nil {
			return lines, err
		}
		s = strings.TrimRight(s, "\r\n")
		if len(s) < 4 {
			continue
		}
		code, sep := s[:3], s[3]
		lines = append(lines, s[4:])
		if sep == ' ' {
			if !strings.HasPrefix(code, "2") {
				return lines, fmt.Errorf("%s", s)
			}
			return lines, nil
		}
	}
}

func (t *TorCtl) Close() {
	if t.conn != nil {
		_, _ = t.conn.Write([]byte("QUIT\r\n"))
		t.conn.Close()
	}
}

func (t *TorCtl) NewIdentity() error {
	_, err := t.cmd("SIGNAL NEWNYM")
	return err
}

// BootstrapPercent returns 0..100, or -1 if unknown.
func (t *TorCtl) BootstrapPercent() int {
	lines, err := t.cmd("GETINFO status/bootstrap-phase")
	if err != nil {
		return -1
	}
	for _, ln := range lines {
		for _, tok := range strings.Fields(ln) {
			if strings.HasPrefix(tok, "PROGRESS=") {
				if n, err := strconv.Atoi(strings.TrimPrefix(tok, "PROGRESS=")); err == nil {
					return n
				}
			}
		}
	}
	return -1
}

// Hop is one relay in a circuit.
type Hop struct {
	Nick    string `json:"nick"`
	Country string `json:"country"`
	Flag    string `json:"flag"`
}

// Circuit returns the first BUILT general-purpose circuit's hops.
func (t *TorCtl) Circuit() []Hop {
	lines, err := t.cmd("GETINFO circuit-status")
	if err != nil {
		return nil
	}
	for _, ln := range lines {
		// e.g. "5 BUILT $FP~Nick,$FP~Nick PURPOSE=GENERAL ..."
		if !strings.Contains(ln, "BUILT") || !strings.Contains(ln, "PURPOSE=GENERAL") {
			continue
		}
		fields := strings.Fields(ln)
		if len(fields) < 3 {
			continue
		}
		var hops []Hop
		for _, relay := range strings.Split(fields[2], ",") {
			nick := relay
			if i := strings.Index(relay, "~"); i >= 0 {
				nick = relay[i+1:]
			}
			fp := relay
			if i := strings.Index(relay, "~"); i >= 0 {
				fp = strings.TrimPrefix(relay[:i], "$")
			}
			cc := "??"
			if cl, err := t.cmd("GETINFO ip-to-country/relay/" + fp); err == nil && len(cl) > 0 {
				if i := strings.Index(cl[0], "="); i >= 0 {
					cc = strings.ToUpper(strings.TrimSpace(cl[0][i+1:]))
				}
			}
			hops = append(hops, Hop{Nick: nick, Country: cc, Flag: CCToFlag(cc)})
		}
		if len(hops) > 0 {
			return hops
		}
	}
	return nil
}

// PortOpen reports whether something is listening (fast).
func PortOpen(addr string, timeout time.Duration) bool {
	c, err := net.DialTimeout("tcp", addr, timeout)
	if err != nil {
		return false
	}
	c.Close()
	return true
}
