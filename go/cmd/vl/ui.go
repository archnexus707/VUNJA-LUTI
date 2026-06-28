package main

import (
	"fmt"
	"os"
)

var (
	cAccent = rgb(0xff, 0x2a, 0x6d)
	cCyan   = rgb(0x05, 0xd9, 0xe8)
	cGreen  = rgb(0x39, 0xff, 0x14)
	cYellow = rgb(0xf9, 0xf0, 0x02)
	cRed    = rgb(0xff, 0x00, 0x3c)
	cSub    = rgb(0x8b, 0x98, 0xa9)
	reset   = "\033[0m"
	bold    = "\033[1m"
	dim     = "\033[2m"
)

func rgb(r, g, b int) string { return fmt.Sprintf("\033[38;2;%d;%d;%dm", r, g, b) }

func tty() bool {
	fi, _ := os.Stdout.Stat()
	return fi != nil && (fi.Mode()&os.ModeCharDevice) != 0
}

func col(c, s string) string {
	if !tty() {
		return s
	}
	return c + s + reset
}

func say(s string)    { fmt.Printf("  %s  %s\n", col(cAccent, "◆"), s) }
func okMsg(s string)  { fmt.Printf("  %s  %s\n", col(cGreen, "✔"), s) }
func warn(s string)   { fmt.Printf("  %s  %s\n", col(cYellow, "◇"), s) }
func errMsg(s string) { fmt.Printf("  %s  %s\n", col(cRed, "✖"), s) }

const banner = `
   ██╗   ██╗██╗   ██╗███╗   ██╗      ██╗  █████╗     ██╗     ██╗   ██╗████████╗██╗
   ██║   ██║██║   ██║████╗  ██║      ██║ ██╔══██╗    ██║     ██║   ██║╚══██╔══╝██║
   ╚██╗ ██╔╝██║   ██║██║╚██╗██║ ██   ██║ ██╔══██║    ██║     ██║   ██║   ██║   ██║
    ╚████╔╝ ╚██████╔╝██║ ╚████║ ╚█████╔╝ ██║  ██║    ███████╗╚██████╔╝   ██║   ██║
     ╚═══╝   ╚═════╝ ╚═╝  ╚═══╝  ╚════╝  ╚═╝  ╚═╝    ╚══════╝ ╚═════╝    ╚═╝   ╚═╝`

func printBanner() {
	fmt.Println(col(cAccent, banner))
	fmt.Printf("  %sVUNJA LUTI%s %s— v%s (go)%s   %s\n\n",
		bold, reset, dim, version, reset,
		col(cSub, "Tor Proxy · IP Rotator · single static binary"))
}
