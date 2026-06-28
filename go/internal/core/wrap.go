package core

// Route a command through Tor via proxychains, streaming output and optionally
// rotating the exit IP while it runs.

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"time"
)

func HasProxychains() bool {
	_, err := exec.LookPath("proxychains4")
	if err == nil {
		return true
	}
	_, err = exec.LookPath("proxychains")
	return err == nil
}

func proxychainsBin() string {
	if p, err := exec.LookPath("proxychains4"); err == nil {
		return p
	}
	if p, err := exec.LookPath("proxychains"); err == nil {
		return p
	}
	return "proxychains4"
}

func BuildProxychainsConf(socksPort int) (string, error) {
	content := fmt.Sprintf(`# VUNJA-LUTI auto-generated
strict_chain
proxy_dns
remote_dns_subnet 224
tcp_read_time_out 15000
tcp_connect_time_out 8000

[ProxyList]
socks5 127.0.0.1 %d
`, socksPort)
	f, err := os.CreateTemp("", "vl_proxychains_*.conf")
	if err != nil {
		return "", err
	}
	f.WriteString(content)
	f.Close()
	return f.Name(), nil
}

// Wrap runs args through proxychains. onLine receives each output line. If
// rotateEvery>0 and a control password is set, the exit IP rotates in the
// background. Returns the child exit code.
func Wrap(c Config, args []string, rotateEvery int, onLine func(string)) (int, error) {
	if !HasProxychains() {
		return 1, fmt.Errorf("proxychains4 not installed (sudo apt install proxychains4)")
	}
	conf, err := BuildProxychainsConf(c.SocksPort)
	if err != nil {
		return 1, err
	}
	full := append([]string{proxychainsBin(), "-f", conf}, args...)
	cmd := exec.Command(full[0], full[1:]...)
	stdout, _ := cmd.StdoutPipe()
	cmd.Stderr = cmd.Stdout // merge

	if err := cmd.Start(); err != nil {
		return 1, err
	}

	stop := make(chan struct{})
	if rotateEvery > 0 && c.ControlPassword != "" {
		go func() {
			tk := time.NewTicker(time.Duration(rotateEvery) * time.Second)
			defer tk.Stop()
			for {
				select {
				case <-stop:
					return
				case <-tk.C:
					if t, err := DialControl(c.ControlAddr(), c.ControlPassword, 8*time.Second); err == nil {
						_ = t.NewIdentity()
						t.Close()
					}
				}
			}
		}()
	}

	sc := bufio.NewScanner(stdout)
	sc.Buffer(make([]byte, 0, 64*1024), 1024*1024)
	for sc.Scan() {
		if onLine != nil {
			onLine(sc.Text())
		}
	}
	err = cmd.Wait()
	close(stop)
	code := 0
	if ee, ok := err.(*exec.ExitError); ok {
		code = ee.ExitCode()
	} else if err != nil {
		code = 1
	}
	return code, nil
}

// ToolTemplates mirrors the Python toolbox.
var ToolTemplates = map[string]string{
	"hydra":    "hydra {auth} -P {passlist} {service}://{target}",
	"ffuf":     "ffuf -u {target}/FUZZ -w {wordlist} -mc 200,301,302,403",
	"gobuster": "gobuster dir -u {target} -w {wordlist}",
	"sqlmap":   "sqlmap -u {target} --batch",
	"nmap":     "nmap -sT -Pn -p {ports} {target}",
	"nikto":    "nikto -h {target}",
	"wpscan":   "wpscan --url {target} --random-user-agent",
	"curl":     "curl -sSL {target}",
}
