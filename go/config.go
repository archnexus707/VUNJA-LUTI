package main

// Reads/writes the SAME ~/.config/vl/config.json the Python build uses, so the
// Go and Python tools share the control password and settings.

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

type Config struct {
	Theme           string `json:"theme"`
	RotateInterval  int    `json:"rotate_interval"`
	ExitFilter      string `json:"exit_filter"`
	SocksPort       int    `json:"socks_port"`
	ControlPort     int    `json:"control_port"`
	ControlPassword string `json:"control_password"`

	rest map[string]json.RawMessage `json:"-"`
}

func configDir() string {
	if d := os.Getenv("VL_CONFIG_DIR"); d != "" {
		return d
	}
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".config", "vl")
}

func configPath() string { return filepath.Join(configDir(), "config.json") }

func defaultConfig() Config {
	return Config{Theme: "cyberpunk", RotateInterval: 60, SocksPort: 9050, ControlPort: 9051}
}

func loadConfig() Config {
	c := defaultConfig()
	data, err := os.ReadFile(configPath())
	if err != nil {
		return c
	}
	// preserve unknown keys so we don't clobber Python-written fields
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

func (c Config) save() error {
	if err := os.MkdirAll(configDir(), 0o755); err != nil {
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
	if err := os.WriteFile(configPath(), b, 0o600); err != nil {
		return err
	}
	return nil
}

func (c Config) socksAddr() string   { return fmt.Sprintf("127.0.0.1:%d", c.SocksPort) }
func (c Config) controlAddr() string { return fmt.Sprintf("127.0.0.1:%d", c.ControlPort) }
