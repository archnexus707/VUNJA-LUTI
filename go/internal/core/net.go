package core

// Minimal SOCKS5 client (RFC 1928) + tiny HTTP, standard library only.
// Destinations are sent as domain names so Tor resolves them — no DNS leak.

import (
	"crypto/tls"
	"encoding/binary"
	"fmt"
	"io"
	"net"
	"strings"
	"time"
)

func socksDial(proxyAddr, host string, port uint16, timeout time.Duration) (net.Conn, error) {
	c, err := net.DialTimeout("tcp", proxyAddr, timeout)
	if err != nil {
		return nil, err
	}
	_ = c.SetDeadline(time.Now().Add(timeout))

	if _, err := c.Write([]byte{0x05, 0x01, 0x00}); err != nil {
		c.Close()
		return nil, err
	}
	resp := make([]byte, 2)
	if _, err := io.ReadFull(c, resp); err != nil {
		c.Close()
		return nil, err
	}
	if resp[0] != 0x05 || resp[1] != 0x00 {
		c.Close()
		return nil, fmt.Errorf("socks5: no acceptable auth method")
	}
	if len(host) > 255 {
		c.Close()
		return nil, fmt.Errorf("socks5: host too long")
	}
	req := []byte{0x05, 0x01, 0x00, 0x03, byte(len(host))}
	req = append(req, []byte(host)...)
	p := make([]byte, 2)
	binary.BigEndian.PutUint16(p, port)
	req = append(req, p...)
	if _, err := c.Write(req); err != nil {
		c.Close()
		return nil, err
	}
	head := make([]byte, 4)
	if _, err := io.ReadFull(c, head); err != nil {
		c.Close()
		return nil, err
	}
	if head[1] != 0x00 {
		c.Close()
		return nil, fmt.Errorf("socks5: connect failed (code %d)", head[1])
	}
	switch head[3] {
	case 0x01:
		io.CopyN(io.Discard, c, 4+2)
	case 0x03:
		l := make([]byte, 1)
		io.ReadFull(c, l)
		io.CopyN(io.Discard, c, int64(l[0])+2)
	case 0x04:
		io.CopyN(io.Discard, c, 16+2)
	}
	_ = c.SetDeadline(time.Time{})
	return c, nil
}

func httpGetViaSocks(proxyAddr, host, path string, useTLS bool, timeout time.Duration) (string, error) {
	port := uint16(80)
	if useTLS {
		port = 443
	}
	conn, err := socksDial(proxyAddr, host, port, timeout)
	if err != nil {
		return "", err
	}
	defer conn.Close()
	_ = conn.SetDeadline(time.Now().Add(timeout))

	var rw net.Conn = conn
	if useTLS {
		tc := tls.Client(conn, &tls.Config{ServerName: host})
		if err := tc.Handshake(); err != nil {
			return "", err
		}
		rw = tc
	}
	req := fmt.Sprintf("GET %s HTTP/1.1\r\nHost: %s\r\nUser-Agent: vunja-luti\r\nConnection: close\r\n\r\n", path, host)
	if _, err := rw.Write([]byte(req)); err != nil {
		return "", err
	}
	raw, err := io.ReadAll(rw)
	if err != nil && len(raw) == 0 {
		return "", err
	}
	parts := strings.SplitN(string(raw), "\r\n\r\n", 2)
	if len(parts) != 2 {
		return "", fmt.Errorf("malformed HTTP response")
	}
	return strings.TrimSpace(stripChunking(parts[1])), nil
}

func plainTLSGet(host, path string, timeout time.Duration) (string, error) {
	raw, err := net.DialTimeout("tcp", host+":443", timeout)
	if err != nil {
		return "", err
	}
	defer raw.Close()
	_ = raw.SetDeadline(time.Now().Add(timeout))
	conn := tls.Client(raw, &tls.Config{ServerName: host})
	if err := conn.Handshake(); err != nil {
		return "", err
	}
	req := fmt.Sprintf("GET %s HTTP/1.1\r\nHost: %s\r\nConnection: close\r\n\r\n", path, host)
	conn.Write([]byte(req))
	buf := make([]byte, 4096)
	n, _ := conn.Read(buf)
	parts := strings.SplitN(string(buf[:n]), "\r\n\r\n", 2)
	if len(parts) != 2 {
		return "", fmt.Errorf("bad response")
	}
	return stripChunking(parts[1]), nil
}

func stripChunking(body string) string {
	var out []string
	for _, ln := range strings.Split(body, "\r\n") {
		t := strings.TrimSpace(ln)
		if t == "" || isHex(t) {
			continue
		}
		out = append(out, ln)
	}
	return strings.Join(out, "")
}

func isHex(s string) bool {
	if s == "" || len(s) > 4 {
		return false
	}
	for _, r := range s {
		if !strings.ContainsRune("0123456789abcdefABCDEF", r) {
			return false
		}
	}
	return true
}
