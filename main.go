package main

import (
	"fmt"
	"os"

	"pokemon-team-history/internal/exporter"
)

func main() {
	if err := exporter.ExportAll("."); err != nil {
		fmt.Fprintf(os.Stderr, "export failed: %v\n", err)
		os.Exit(1)
	}
}
