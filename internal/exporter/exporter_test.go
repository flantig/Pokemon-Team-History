package exporter

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"pokemon-team-history/internal/pokecrypto"
)

func TestSanitizeFilenamePart(t *testing.T) {
	if got := SanitizeFilenamePart("Ogerpon-Cornerstone!"); got != "Ogerpon-Cornerstone_" {
		t.Fatalf("got %q", got)
	}
}

func TestExportGameCreatesExpectedFiles(t *testing.T) {
	tmp := t.TempDir()
	mon := &pokecrypto.Pokemon{
		SpeciesName: "Golurk",
		Nickname:    "Soju",
		Level:       100,
		Item:        "Assault Vest",
		Ability:     "Iron Fist",
		Nature:      "Adamant",
		TeraType:    "Ghost",
		EVs:         [6]int{252, 252, 4, 0, 0, 0},
		IVs:         [6]int{31, 31, 31, 31, 31, 31},
		Stats:       [6]int{382, 381, 197, 131, 196, 146},
		Moves:       []string{"Ice Punch", "High Horsepower"},
		RawDec:      make([]byte, pokecrypto.SlotSize),
	}

	err := ExportGame(GameExportConfig{
		Dir:       tmp,
		Title:     "Test Squad",
		Party:     []*pokecrypto.Pokemon{mon},
		Extension: "pk9",
		IsSV:      true,
	})
	if err != nil {
		t.Fatalf("ExportGame failed: %v", err)
	}

	if _, err := os.Stat(filepath.Join(tmp, "pokemon_files", "Party_01_Soju_Golurk_Lv100.pk9")); err != nil {
		t.Fatalf("expected .pk9 file missing: %v", err)
	}
	mdBytes, err := os.ReadFile(filepath.Join(tmp, "Roster_Summary.md"))
	if err != nil {
		t.Fatalf("read Roster_Summary.md: %v", err)
	}
	if strings.Contains(string(mdBytes), "## PC Boxes") {
		t.Fatal("Roster_Summary.md should not include PC Boxes section when empty")
	}
}
