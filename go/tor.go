package main

// Tor control-protocol client (text protocol over TCP), standard library only.
// Supports password auth (HashedControlPassword) — the same scheme the Python
// build's `vl doctor --fix` configures, so the two are interoperable.

import (
	"bufio"
	"fmt"
	"net"
	"strconv"
	"strings"
	"time"
)

type torCtl struct {
	conn net.Conn
	r    *bufio.Reader
}

func dialControl(addr, password string, timeout time.Duration) (*torCtl, error) {
	c, err := net.DialTimeout("tcp", addr, timeout)
	if err != nil {
		return nil, fmt.Errorf("cannot reach control port %s (run `vl doctor --fix`)", addr)
	}
	_ = c.SetDeadline(time.Now().Add(timeout))
	t := &torCtl{conn: c, r: bufio.NewReader(c)}

	auth := "AUTHENTICATE"
	if password != "" {
		auth = fmt.Sprintf("AUTHENTICATE %q", password) // %q gives a valid Tor CString
	}
	if _, err := t.cmd(auth); err != nil {
		c.Close()
		return nil, fmt.Errorf("control authentication failed: %w (run `vl doctor --fix`)", err)
	}
	return t, nil
}

// cmd sends one command and returns the reply lines, erroring on non-2xx.
func (t *torCtl) cmd(line string) ([]string, error) {
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
		code := s[:3]
		sep := s[3] // '-' = more lines, ' ' = final, '+' = data
		lines = append(lines, s[4:])
		if sep == ' ' {
			if !strings.HasPrefix(code, "2") {
				return lines, fmt.Errorf("%s", s)
			}
			return lines, nil
		}
	}
}

func (t *torCtl) close() {
	if t.conn != nil {
		_, _ = t.conn.Write([]byte("QUIT\r\n"))
		t.conn.Close()
	}
}

func (t *torCtl) newIdentity() error {
	_, err := t.cmd("SIGNAL NEWNYM")
	return err
}

// bootstrapPercent returns 0..100, or -1 if unknown.
func (t *torCtl) bootstrapPercent() int {
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

// portOpen reports whether something is listening (fast, used for status).
func portOpen(addr string, timeout time.Duration) bool {
	c, err := net.DialTimeout("tcp", addr, timeout)
	if err != nil {
		return false
	}
	c.Close()
	return true
}
