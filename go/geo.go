package main

import (
	"crypto/tls"
	"fmt"
	"net"
	"strings"
	"time"
)

// exitIP returns the current Tor exit IP via an IP-echo service over SOCKS.
func exitIP(socksAddr string, timeout time.Duration) string {
	for _, h := range []string{"api.ipify.org", "icanhazip.com"} {
		if ip, err := httpGetViaSocks(socksAddr, h, "/", true, timeout); err == nil {
			ip = strings.TrimSpace(ip)
			if ip != "" && len(ip) <= 45 {
				return ip
			}
		}
	}
	return ""
}

// countryOf returns (cc, flag) for an IP, looked up through Tor.
func countryOf(socksAddr, ip string, timeout time.Duration) (string, string) {
	if ip == "" {
		return "??", "🏴"
	}
	body, err := httpGetViaSocks(socksAddr, "ip-api.com", "/json/"+ip+"?fields=countryCode", false, timeout)
	if err != nil {
		return "??", "🏴"
	}
	// crude JSON pluck: {"countryCode":"NL"}
	cc := between(body, `"countryCode":"`, `"`)
	if len(cc) != 2 {
		return "??", "🏴"
	}
	return cc, ccToFlag(cc)
}

func latencyMS(socksAddr string, timeout time.Duration) int {
	start := time.Now()
	if _, err := httpGetViaSocks(socksAddr, "check.torproject.org", "/", true, timeout); err != nil {
		return 0
	}
	return int(time.Since(start).Milliseconds())
}

func ccToFlag(cc string) string {
	cc = strings.ToUpper(cc)
	if len(cc) != 2 {
		return "🏴"
	}
	r := []rune{rune(cc[0]) + 127397, rune(cc[1]) + 127397}
	return string(r)
}

func quality(ms int) string {
	switch {
	case ms <= 0:
		return "⚫"
	case ms < 300:
		return "🟢"
	case ms < 800:
		return "🟡"
	default:
		return "🔴"
	}
}

func between(s, a, b string) string {
	i := strings.Index(s, a)
	if i < 0 {
		return ""
	}
	s = s[i+len(a):]
	j := strings.Index(s, b)
	if j < 0 {
		return ""
	}
	return s[:j]
}

// directIP returns the real (non-Tor) IP for the anonymity check.
func directIP(timeout time.Duration) string {
	// reuse the socks path? No — we want a *direct* fetch. Use a plain dialer.
	return directHTTPGet("api.ipify.org", "/", timeout)
}

func directHTTPGet(host, path string, timeout time.Duration) string {
	out, err := plainTLSGet(host, path, timeout)
	if err != nil {
		return ""
	}
	return strings.TrimSpace(out)
}

func plainTLSGet(host, path string, timeout time.Duration) (string, error) {
	// minimal direct TLS GET (no proxy)
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
