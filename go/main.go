// VUNJA LUTI — Wails desktop GUI (Go backend + neon web frontend).
// Build: wails build   (needs libwebkit2gtk-4.1-dev + libgtk-3-dev on Linux)
package main

import (
	"embed"

	"github.com/wailsapp/wails/v2"
	"github.com/wailsapp/wails/v2/pkg/options"
	"github.com/wailsapp/wails/v2/pkg/options/assetserver"
	"github.com/wailsapp/wails/v2/pkg/options/linux"
)

//go:embed all:frontend/dist
var assets embed.FS

func main() {
	app := NewApp()
	err := wails.Run(&options.App{
		Title:     "VUNJA LUTI",
		Width:     980,
		Height:    760,
		MinWidth:  820,
		MinHeight: 600,
		AssetServer: &assetserver.Options{
			Assets: assets,
		},
		BackgroundColour: &options.RGBA{R: 11, G: 14, B: 20, A: 1},
		OnStartup:        app.startup,
		Bind:             []interface{}{app},
		Linux: &linux.Options{
			WindowIsTranslucent: false,
			ProgramName:         "vunja-luti",
		},
	})
	if err != nil {
		println("error:", err.Error())
	}
}
