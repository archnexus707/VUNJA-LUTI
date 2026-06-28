// Package core holds the shared VUNJA LUTI engine used by both the CLI (cmd/vl)
// and the Wails GUI. Standard-library only.
package core

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// Config mirrors the Python build's ~/.config/vl/config.json so the two tools
// share settings (notably the control password).
type Config struct {
	Theme           string `json:"theme"`
	RotateInterval  int    `json:"rotate_interval"`
	ExitFilter      string `json:"exit_filter"`
	SocksPort       int    `json:"socks_port"`
	ControlPort     int    `json:"control_port"`
	ControlPassword string `json:"control_password"`

	rest map[string]json.RawMessage
}

func ConfigDir() string {
	if d := os.Getenv("VL_CONFIG_DIR"); d != "" {
		return d
	}
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".config", "vl")
}

func ConfigPath() string { return filepath.Join(ConfigDir(), "config.json") }

func Default() Config {
	return Config{Theme: "cyberpunk", RotateInterval: 60, SocksPort: 9050, ControlPort: 9051}
}

func Load() Config {
	c := Default()
	data, err := os.ReadFile(ConfigPath())
	if err != nil {
		return c
	}
	c.rest = map[string]json.RawMessage{}
	_ = json.Unmarshal(data, &c.rest)
	_ = json.Unmarshal(data, &c)
	if c.SocksPort == 0 {
		c.SocksPort = 9050
	}
	if c.ControlPort == 0 {
		c.ControlPort = 9051
	}
	return c
}

func (c Config) Save() error {
	if err := os.MkdirAll(ConfigDir(), 0o755); err != nil {
		return err
	}
	merged := map[string]any{}
	for k, v := range c.rest {
		merged[k] = v
	}
	merged["theme"] = c.Theme
	merged["rotate_interval"] = c.RotateInterval
	merged["exit_filter"] = c.ExitFilter
	merged["socks_port"] = c.SocksPort
	merged["control_port"] = c.ControlPort
	merged["control_password"] = c.ControlPassword
	b, _ := json.MarshalIndent(merged, "", "  ")
	return os.WriteFile(ConfigPath(), b, 0o600)
}

func (c Config) SocksAddr() string   { return fmt.Sprintf("127.0.0.1:%d", c.SocksPort) }
func (c Config) ControlAddr() string { return fmt.Sprintf("127.0.0.1:%d", c.ControlPort) }
