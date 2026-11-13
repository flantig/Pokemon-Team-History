// Package exporter generates .pk9/.pb8 files, Showdown_Export.txt, and Roster_Summary.md
// from Pokemon Scarlet and Pokemon Luminescent Platinum save files.
package exporter

import (
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	"pokemon-team-history/internal/pokecrypto"
	"pokemon-team-history/internal/swish"
)

var nonSafeRe = regexp.MustCompile(`[^A-Za-z0-9_-]`)

// BoxEntry pairs a box slot's display label and filename prefix with its parsed Pokemon.
type BoxEntry struct {
	LocationLabel  string
	FilenamePrefix string
	Mon            *pokecrypto.Pokemon
}

// GameExportConfig describes a roster export target.
type GameExportConfig struct {
	Dir       string
	Title     string
	Party     []*pokecrypto.Pokemon
	Boxes     []BoxEntry
	Extension string
	IsSV      bool
}

// SanitizeFilenamePart replaces characters outside [A-Za-z0-9_-] with underscores.
func SanitizeFilenamePart(s string) string {
	return nonSafeRe.ReplaceAllString(s, "_")
}

func formatSix(v [6]int) string {
	return fmt.Sprintf("%d/%d/%d/%d/%d/%d", v[0], v[1], v[2], v[3], v[4], v[5])
}

// ExportGame writes individual PK9/PB8 files, Showdown_Export.txt, and Roster_Summary.md.
func ExportGame(cfg GameExportConfig) error {
	pDir := filepath.Join(cfg.Dir, "pokemon_files")
	if err := os.MkdirAll(pDir, 0o755); err != nil {
		return fmt.Errorf("mkdir %s: %w", pDir, err)
	}

	entries, err := os.ReadDir(pDir)
	if err != nil {
		return fmt.Errorf("readdir %s: %w", pDir, err)
	}
	for _, e := range entries {
		if !e.IsDir() {
			if err := os.Remove(filepath.Join(pDir, e.Name())); err != nil {
				return fmt.Errorf("remove %s: %w", e.Name(), err)
			}
		}
	}

	var showdownBlocks []string
	mdLines := []string{
		fmt.Sprintf("# %s - Full Roster Backup\n", cfg.Title),
		fmt.Sprintf("## Active Party (%d Pokemon)\n", len(cfg.Party)),
	}

	if cfg.IsSV {
		mdLines = append(mdLines,
			"| Slot | Nickname | Species | Lv | Tera | Item | Ability | Nature | Stats (HP/Atk/Def/SpA/SpD/Spe) | EVs (HP/Atk/Def/SpA/SpD/Spe) | IVs (HP/Atk/Def/SpA/SpD/Spe) | Moves |",
			"|---|---|---|---|---|---|---|---|---|---|---|---|",
		)
	} else {
		mdLines = append(mdLines,
			"| Slot | Nickname | Species | Lv | Item | Ability | Nature | Stats (HP/Atk/Def/SpA/SpD/Spe) | EVs (HP/Atk/Def/SpA/SpD/Spe) | IVs (HP/Atk/Def/SpA/SpD/Spe) | Moves |",
			"|---|---|---|---|---|---|---|---|---|---|---|",
		)
	}

	for idx, mon := range cfg.Party {
		safeNick := SanitizeFilenamePart(mon.Nickname)
		safeSp := SanitizeFilenamePart(mon.SpeciesName)
		fname := fmt.Sprintf("Party_%02d_%s_%s_Lv%d.%s", idx+1, safeNick, safeSp, mon.Level, cfg.Extension)
		if err := os.WriteFile(filepath.Join(pDir, fname), mon.RawDec, 0o644); err != nil {
			return fmt.Errorf("write %s: %w", fname, err)
		}

		showdownBlocks = append(showdownBlocks, mon.ToShowdown())
		stStr := formatSix(mon.Stats)
		evStr := formatSix(mon.EVs)
		ivStr := formatSix(mon.IVs)
		mvStr := strings.Join(mon.Moves, ", ")

		if cfg.IsSV {
			mdLines = append(mdLines, fmt.Sprintf(
				"| Party %d | **%s** | %s | %d | %s | %s | %s | %s | `%s` | `%s` | `%s` | %s |",
				idx+1, mon.Nickname, mon.SpeciesName, mon.Level, mon.TeraType,
				mon.Item, mon.Ability, mon.Nature, stStr, evStr, ivStr, mvStr,
			))
		} else {
			mdLines = append(mdLines, fmt.Sprintf(
				"| Party %d | **%s** | %s | %d | %s | %s | %s | `%s` | `%s` | `%s` | %s |",
				idx+1, mon.Nickname, mon.SpeciesName, mon.Level,
				mon.Item, mon.Ability, mon.Nature, stStr, evStr, ivStr, mvStr,
			))
		}
	}

	if len(cfg.Boxes) > 0 {
		mdLines = append(mdLines,
			fmt.Sprintf("\n## PC Boxes (%d Pokemon)\n", len(cfg.Boxes)),
			"| Location | Nickname | Species | Lv | Item | Ability | Nature | IVs (HP/Atk/Def/SpA/SpD/Spe) | Moves |",
			"|---|---|---|---|---|---|---|---|---|",
		)
		for _, box := range cfg.Boxes {
			mon := box.Mon
			safeNick := SanitizeFilenamePart(mon.Nickname)
			safeSp := SanitizeFilenamePart(mon.SpeciesName)
			fname := fmt.Sprintf("%s_%s_%s_Lv%d.%s", box.FilenamePrefix, safeNick, safeSp, mon.Level, cfg.Extension)
			if err := os.WriteFile(filepath.Join(pDir, fname), mon.RawDec, 0o644); err != nil {
				return fmt.Errorf("write %s: %w", fname, err)
			}

			showdownBlocks = append(showdownBlocks, mon.ToShowdown())
			ivStr := formatSix(mon.IVs)
			mvStr := strings.Join(mon.Moves, ", ")
			mdLines = append(mdLines, fmt.Sprintf(
				"| %s | **%s** | %s | %d | %s | %s | %s | `%s` | %s |",
				box.LocationLabel, mon.Nickname, mon.SpeciesName, mon.Level,
				mon.Item, mon.Ability, mon.Nature, ivStr, mvStr,
			))
		}
	}

	if err := os.WriteFile(filepath.Join(cfg.Dir, "Showdown_Export.txt"), []byte(strings.Join(showdownBlocks, "\n")), 0o644); err != nil {
		return fmt.Errorf("write Showdown_Export.txt: %w", err)
	}
	if err := os.WriteFile(filepath.Join(cfg.Dir, "Roster_Summary.md"), []byte(strings.Join(mdLines, "\n")+"\n"), 0o644); err != nil {
		return fmt.Errorf("write Roster_Summary.md: %w", err)
	}

	fmt.Printf("Exported %s: %d Party, %d Box -> %s\n", cfg.Title, len(cfg.Party), len(cfg.Boxes), cfg.Dir)
	return nil
}

// ExportScarletAndSquad exports both Pokemon_Scarlet and Imagine_Killing_Dragons from Scarlet's main save.
func ExportScarletAndSquad(baseDir string, tables *pokecrypto.Tables) error {
	svDir := filepath.Join(baseDir, "Pokemon_Scarlet")
	svRaw, err := os.ReadFile(filepath.Join(svDir, "raw_saves", "main"))
	if err != nil {
		return fmt.Errorf("read Scarlet save: %w", err)
	}
	if len(svRaw) < 32 {
		return fmt.Errorf("Scarlet save too short: %d bytes", len(svRaw))
	}

	svDec := swish.CryptStaticXorpad(svRaw[:len(svRaw)-32])
	blocks, err := swish.FindSCBlocks(svDec, map[uint32]bool{
		swish.KeyParty: true,
		swish.KeyBox:   true,
	})
	if err != nil {
		return fmt.Errorf("parse Scarlet SCBlocks: %w", err)
	}

	partyBytes := blocks[swish.KeyParty].Data
	boxBytes := blocks[swish.KeyBox].Data

	var svParty []*pokecrypto.Pokemon
	for i := range 6 {
		off := i * pokecrypto.SlotSize
		if off+pokecrypto.SlotSize > len(partyBytes) {
			break
		}
		if mon, ok := pokecrypto.ParseMon(pokecrypto.DecryptPK(partyBytes[off:off+pokecrypto.SlotSize]), tables, true); ok {
			svParty = append(svParty, mon)
		}
	}

	var svBoxes []BoxEntry
	for b := range 32 {
		for s := range 30 {
			idx := b*30 + s
			off := idx * pokecrypto.SlotSize
			if off+pokecrypto.SlotSize > len(boxBytes) {
				break
			}
			if mon, ok := pokecrypto.ParseMon(pokecrypto.DecryptPK(boxBytes[off:off+pokecrypto.SlotSize]), tables, true); ok {
				svBoxes = append(svBoxes, BoxEntry{
					LocationLabel:  fmt.Sprintf("Box %d Slot %d", b+1, s+1),
					FilenamePrefix: fmt.Sprintf("Box%02d_Slot%02d", b+1, s+1),
					Mon:            mon,
				})
			}
		}
	}

	if err := ExportGame(GameExportConfig{
		Dir:       svDir,
		Title:     "Pokemon Scarlet (Ultimate Scarlet)",
		Party:     svParty,
		Boxes:     svBoxes,
		Extension: "pk9",
		IsSV:      true,
	}); err != nil {
		return err
	}

	var ikdSquad []*pokecrypto.Pokemon
	for idx := 24; idx < 30; idx++ {
		off := idx * pokecrypto.SlotSize
		if off+pokecrypto.SlotSize > len(boxBytes) {
			break
		}
		if mon, ok := pokecrypto.ParseMon(pokecrypto.DecryptPK(boxBytes[off:off+pokecrypto.SlotSize]), tables, true); ok {
			ikdSquad = append(ikdSquad, mon)
		}
	}

	return ExportGame(GameExportConfig{
		Dir:       filepath.Join(baseDir, "Imagine_Killing_Dragons"),
		Title:     "Imagine Killing Dragons (Pokemon Scarlet - Dragon Elite Four Trial Squad)",
		Party:     ikdSquad,
		Boxes:     nil,
		Extension: "pk9",
		IsSV:      true,
	})
}

func isZeroSlot(chunk []byte) bool {
	for i := range 8 {
		if chunk[i] != 0 {
			return false
		}
	}
	return true
}

// ExportLuminescentPlatinum exports Pokemon Luminescent Platinum from SaveData.bin.
func ExportLuminescentPlatinum(baseDir string, tables *pokecrypto.Tables) error {
	lumiDir := filepath.Join(baseDir, "Pokemon_Luminescent_Platinum")
	lumiRaw, err := os.ReadFile(filepath.Join(lumiDir, "raw_saves", "SaveData.bin"))
	if err != nil {
		return fmt.Errorf("read Luminescent Platinum save: %w", err)
	}

	var lumiParty []*pokecrypto.Pokemon
	for i := range 6 {
		off := 0x014098 + i*pokecrypto.SlotSize
		if off+pokecrypto.SlotSize > len(lumiRaw) {
			break
		}
		if mon, ok := pokecrypto.ParseMon(pokecrypto.DecryptPK(lumiRaw[off:off+pokecrypto.SlotSize]), tables, false); ok {
			lumiParty = append(lumiParty, mon)
		}
	}

	var lumiBoxes []BoxEntry
	for b := range 40 {
		for s := range 30 {
			idx := b*30 + s
			off := 0x014EF4 + idx*pokecrypto.SlotSize
			if off+pokecrypto.SlotSize > 0x090000 || off+pokecrypto.SlotSize > len(lumiRaw) {
				break
			}
			chunk := lumiRaw[off : off+pokecrypto.SlotSize]
			if isZeroSlot(chunk) || chunk[4] != 0 || chunk[5] != 0 {
				continue
			}
			dec := pokecrypto.DecryptPK(chunk)
			if pokecrypto.VerifyChecksum(dec) {
				if mon, ok := pokecrypto.ParseMon(dec, tables, false); ok {
					lumiBoxes = append(lumiBoxes, BoxEntry{
						LocationLabel:  fmt.Sprintf("Box %d Slot %d", b+1, s+1),
						FilenamePrefix: fmt.Sprintf("Box%02d_Slot%02d", b+1, s+1),
						Mon:            mon,
					})
				}
			}
		}
	}

	const dcOff = 0x096080
	if dcOff+pokecrypto.SlotSize <= len(lumiRaw) {
		dcDec := pokecrypto.DecryptPK(lumiRaw[dcOff : dcOff+pokecrypto.SlotSize])
		if pokecrypto.VerifyChecksum(dcDec) {
			if mon, ok := pokecrypto.ParseMon(dcDec, tables, false); ok {
				lumiBoxes = append(lumiBoxes, BoxEntry{
					LocationLabel:  "Daycare",
					FilenamePrefix: "Daycare_Slot01",
					Mon:            mon,
				})
			}
		}
	}

	return ExportGame(GameExportConfig{
		Dir:       lumiDir,
		Title:     "Pokemon Luminescent Platinum",
		Party:     lumiParty,
		Boxes:     lumiBoxes,
		Extension: "pb8",
		IsSV:      false,
	})
}

// ExportAll loads lookup tables and exports all games and squads under baseDir.
func ExportAll(baseDir string) error {
	tables, err := pokecrypto.LoadTables(filepath.Join(baseDir, "tools", "pkhex_text"))
	if err != nil {
		return fmt.Errorf("load pkhex tables: %w", err)
	}
	if err := ExportScarletAndSquad(baseDir, tables); err != nil {
		return err
	}
	return ExportLuminescentPlatinum(baseDir, tables)
}
