package core

import (
	"strings"
	"time"
)

// ExitIP returns the current Tor exit IP via an IP-echo service over SOCKS.
func ExitIP(socksAddr string, timeout time.Duration) string {
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

// CountryOf returns (cc, flag) for an IP, looked up through Tor.
func CountryOf(socksAddr, ip string, timeout time.Duration) (string, string) {
	if ip == "" {
		return "??", "🏴"
	}
	body, err := httpGetViaSocks(socksAddr, "ip-api.com", "/json/"+ip+"?fields=countryCode", false, timeout)
	if err != nil {
		return "??", "🏴"
	}
	cc := between(body, `"countryCode":"`, `"`)
	if len(cc) != 2 {
		return "??", "🏴"
	}
	return cc, CCToFlag(cc)
}

func LatencyMS(socksAddr string, timeout time.Duration) int {
	start := time.Now()
	if _, err := httpGetViaSocks(socksAddr, "check.torproject.org", "/", true, timeout); err != nil {
		return 0
	}
	return int(time.Since(start).Milliseconds())
}

func CCToFlag(cc string) string {
	cc = strings.ToUpper(cc)
	if len(cc) != 2 {
		return "🏴"
	}
	return string([]rune{rune(cc[0]) + 127397, rune(cc[1]) + 127397})
}

func Quality(ms int) string {
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

// DirectIP returns the real (non-Tor) IP for the anonymity check.
func DirectIP(timeout time.Duration) string {
	out, err := plainTLSGet("api.ipify.org", "/", timeout)
	if err != nil {
		return ""
	}
	return strings.TrimSpace(out)
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
