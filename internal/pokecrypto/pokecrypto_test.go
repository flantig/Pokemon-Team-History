package pokecrypto

import (
	"bytes"
	"encoding/binary"
	"path/filepath"
	"testing"
)

func TestEncryptDecryptRoundtripAndChecksum(t *testing.T) {
	dec := make([]byte, SlotSize)
	binary.LittleEndian.PutUint32(dec[0x00:0x04], 0x12345678) // Encryption Constant
	binary.LittleEndian.PutUint16(dec[0x08:0x0A], 908)        // Species: Meowscarada
	dec[0x148] = 100                                          // Level

	enc := EncryptPK(dec)
	if bytes.Equal(enc[8:], dec[8:]) {
		t.Fatal("encrypted PK9 should differ from decrypted PK9")
	}

	dec2 := DecryptPK(enc)
	if !VerifyChecksum(dec2) {
		t.Fatal("VerifyChecksum failed after EncryptPK -> DecryptPK roundtrip")
	}
	if binary.LittleEndian.Uint16(dec2[0x08:0x0A]) != 908 || dec2[0x148] != 100 {
		t.Fatal("decrypted fields do not match original")
	}
}

func TestCalcStats(t *testing.T) {
	// Golurk Lv. 100 Adamant (natureID=3), 6x31 IVs, 252 HP / 252 Atk / 4 Def
	got := CalcStats(
		[6]int{89, 124, 80, 55, 80, 55},
		[6]int{31, 31, 31, 31, 31, 31},
		[6]int{252, 252, 4, 0, 0, 0},
		100,
		3,
	)
	want := [6]int{382, 381, 197, 146, 131, 196} // HP, Atk, Def, Spe, SpA, SpD
	if got != want {
		t.Fatalf("CalcStats got %v, want %v", got, want)
	}
}

func TestParseMonAndShowdown(t *testing.T) {
	tables, err := LoadTables(filepath.Join("..", "..", "tools", "pkhex_text"))
	if err != nil {
		t.Fatalf("LoadTables failed: %v", err)
	}

	dec := make([]byte, SlotSize)
	binary.LittleEndian.PutUint16(dec[0x08:0x0A], 103) // Exeggutor
	binary.LittleEndian.PutUint16(dec[0x0A:0x0C], 158) // Sitrus Berry
	binary.LittleEndian.PutUint16(dec[0x14:0x16], 139) // Harvest
	dec[0x21] = 15                                     // Modest
	dec[0x24] = 1                                      // Alolan form
	dec[0x26] = 248                                    // 248 HP EV
	dec[0x2A] = 252                                    // 252 SpA EV
	dec[0x2B] = 8                                      // 8 SpD EV
	binary.LittleEndian.PutUint32(dec[0x8C:0x90], 0x3FFFFFFF)
	dec[0x94] = 15 // Dragon
	dec[0x95] = 19 // None override
	dec[0x148] = 100
	binary.LittleEndian.PutUint16(dec[0x72:0x74], 406) // Dragon Pulse

	mon, ok := ParseMon(dec, tables, true)
	if !ok {
		t.Fatal("ParseMon returned false for valid mon")
	}
	if mon.SpeciesName != "Exeggutor-Alola" {
		t.Fatalf("got species %q, want Exeggutor-Alola", mon.SpeciesName)
	}
	sd := mon.ToShowdown()
	for _, substr := range []string{"Exeggutor-Alola @ Sitrus Berry", "Ability: Harvest", "Tera Type: Dragon", "Modest Nature", "- Dragon Pulse"} {
		if !bytes.Contains([]byte(sd), []byte(substr)) {
			t.Errorf("Showdown output missing %q:\n%s", substr, sd)
		}
	}
}
