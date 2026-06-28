package main

import (
	"context"
	"sync"
	"time"

	"github.com/archnexus707/vunja-luti/internal/core"
	"github.com/wailsapp/wails/v2/pkg/runtime"
)

// App is the Wails-bound backend. Every method runs on a worker goroutine, so
// the UI thread never blocks — there is no perceptible lag in the GUI.
type App struct {
	ctx      context.Context
	mu       sync.Mutex
	cfg      core.Config
	autoStop chan struct{}
}

func NewApp() *App { return &App{cfg: core.Load()} }

func (a *App) startup(ctx context.Context) { a.ctx = ctx }

func (a *App) config() core.Config {
	a.mu.Lock()
	defer a.mu.Unlock()
	return a.cfg
}

func (a *App) setConfig(c core.Config) {
	a.mu.Lock()
	a.cfg = c
	a.mu.Unlock()
}

// ── bound methods (callable from JS as window.go.main.App.*) ──────────────

func (a *App) Status() core.Status      { return core.GetStatus(a.config()) }
func (a *App) Circuit() []core.Hop      { return core.GetCircuit(a.config()) }
func (a *App) GetConfig() core.Config   { return a.config() }
func (a *App) ToolTemplates() map[string]string { return core.ToolTemplates }

func (a *App) Rotate() core.RotateResult {
	r := core.Rotate(a.config())
	if r.Err == "" {
		runtime.EventsEmit(a.ctx, "rotated", r)
	}
	return r
}

func (a *App) SetTheme(t string) {
	c := a.config()
	c.Theme = t
	c.Save()
	a.setConfig(c)
}

func (a *App) SetInterval(n int) {
	c := a.config()
	if n < 5 {
		n = 5
	}
	c.RotateInterval = n
	c.Save()
	a.setConfig(c)
}

func (a *App) StartTor() string {
	if err := core.StartTor(); err != nil {
		return err.Error()
	}
	return ""
}

func (a *App) StopTor() string {
	a.StopAuto()
	if err := core.StopTor(); err != nil {
		return err.Error()
	}
	return ""
}

type DoctorCheck struct {
	Name string `json:"name"`
	OK   bool   `json:"ok"`
	Note string `json:"note"`
}

func (a *App) Doctor() []DoctorCheck {
	c := a.config()
	running := core.PortOpen(c.SocksAddr(), 2*time.Second)
	authOK := false
	if core.PortOpen(c.ControlAddr(), time.Second) {
		if t, err := core.DialControl(c.ControlAddr(), c.ControlPassword, 4*time.Second); err == nil {
			authOK = true
			t.Close()
		}
	}
	return []DoctorCheck{
		{"tor running", running, ifElse(running, "SOCKS on "+c.SocksAddr(), "not listening")},
		{"control auth", authOK, ifElse(authOK, "authenticated", "needs setup")},
		{"proxychains", core.HasProxychains(), ifElse(core.HasProxychains(), "found", "optional")},
	}
}

func (a *App) DoctorFix() string {
	nc, err := core.DoctorFix(a.config())
	if err != nil {
		return err.Error()
	}
	a.setConfig(nc)
	return ""
}

func (a *App) ApplyExitFilter(csv string) string {
	c := a.config()
	c.ExitFilter = csv
	c.Save()
	a.setConfig(c)
	if err := core.ApplyExitFilter(c, csv); err != nil {
		return err.Error()
	}
	return ""
}

func (a *App) Reset() string {
	nc, err := core.Reset(a.config())
	if err != nil {
		return err.Error()
	}
	a.setConfig(nc)
	return ""
}

// StartAuto rotates on the configured interval, emitting "rotated" events.
func (a *App) StartAuto() {
	a.mu.Lock()
	if a.autoStop != nil {
		a.mu.Unlock()
		return
	}
	stop := make(chan struct{})
	a.autoStop = stop
	interval := a.cfg.RotateInterval
	a.mu.Unlock()
	if interval < 5 {
		interval = 5
	}
	go func() {
		tk := time.NewTicker(time.Duration(interval) * time.Second)
		defer tk.Stop()
		for {
			select {
			case <-stop:
				return
			case <-tk.C:
				if r := core.Rotate(a.config()); r.Err == "" {
					runtime.EventsEmit(a.ctx, "rotated", r)
				}
			}
		}
	}()
}

func (a *App) StopAuto() {
	a.mu.Lock()
	defer a.mu.Unlock()
	if a.autoStop != nil {
		close(a.autoStop)
		a.autoStop = nil
	}
}

// RunTool routes a command (argv) through Tor, streaming "tool:line" events and
// a final "tool:done" event with the exit code.
func (a *App) RunTool(args []string) {
	go func() {
		c := a.config()
		code, err := core.Wrap(c, args, c.RotateInterval, func(line string) {
			runtime.EventsEmit(a.ctx, "tool:line", line)
		})
		if err != nil {
			runtime.EventsEmit(a.ctx, "tool:line", "[error] "+err.Error())
		}
		runtime.EventsEmit(a.ctx, "tool:done", code)
	}()
}

func ifElse(c bool, a, b string) string {
	if c {
		return a
	}
	return b
}
