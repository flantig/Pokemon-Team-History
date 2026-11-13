// Package pokecrypto implements PK9/PB8 encryption, decryption, checksums,
// stat calculation, and metadata parsing for modern Pokemon saves.
package pokecrypto

import (
	"bufio"
	"encoding/binary"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"unicode/utf16"
)

// SlotSize is the fixed byte size of a PK9 / PB8 party or box slot.
const SlotSize = 344

var (
	blockPos = []byte{
		0, 1, 2, 3, 0, 1, 3, 2, 0, 2, 1, 3, 0, 3, 1, 2,
		0, 2, 3, 1, 0, 3, 2, 1, 1, 0, 2, 3, 1, 0, 3, 2,
		2, 0, 1, 3, 3, 0, 1, 2, 2, 0, 3, 1, 3, 0, 2, 1,
		1, 2, 0, 3, 1, 3, 0, 2, 2, 1, 0, 3, 3, 1, 0, 2,
		2, 3, 0, 1, 3, 2, 0, 1, 1, 2, 3, 0, 1, 3, 2, 0,
		2, 1, 3, 0, 3, 1, 2, 0, 2, 3, 1, 0, 3, 2, 1, 0,
		0, 1, 2, 3, 0, 1, 3, 2, 0, 2, 1, 3, 0, 3, 1, 2,
		0, 2, 3, 1, 0, 3, 2, 1, 1, 0, 2, 3, 1, 0, 3, 2,
	}

	blockPosInvert = []byte{
		0, 1, 2, 4, 3, 5, 6, 7, 12, 18, 13, 19, 8, 10, 14, 20,
		16, 22, 9, 11, 15, 21, 17, 23, 0, 1, 2, 4, 3, 5, 6, 7,
	}

	// Natures lists all 25 Pokemon natures indexed by ID.
	Natures = []string{
		"Hardy", "Lonely", "Brave", "Adamant", "Naughty",
		"Bold", "Docile", "Relaxed", "Impish", "Lax",
		"Timid", "Hasty", "Serious", "Jolly", "Naive",
		"Modest", "Mild", "Quiet", "Bashful", "Rash",
		"Calm", "Gentle", "Sassy", "Careful", "Quirky",
	}

	// TeraTypes lists all 19 Tera types indexed by ID.
	TeraTypes = []string{
		"Normal", "Fighting", "Flying", "Poison", "Ground", "Rock", "Bug", "Ghost", "Steel",
		"Fire", "Water", "Grass", "Electric", "Psychic", "Ice", "Dragon", "Dark", "Fairy", "Stellar",
	}

	svInternalToNational = map[uint16]uint16{
		908:  908,
		915:  915,
		934:  964,
		944:  922,
		945:  923,
		1005: 937,
		1009: 980,
		1011: 1017,
	}
)

// Tables holds PKHeX text lookup tables for species, moves, items, and abilities.
type Tables struct {
	Species   []string
	Moves     []string
	Items     []string
	Abilities []string
}

// LoadTables reads species.txt, moves.txt, items.txt, and abilities.txt from dir.
func LoadTables(dir string) (*Tables, error) {
	load := func(name string) ([]string, error) {
		f, err := os.Open(filepath.Join(dir, name))
		if err != nil {
			return nil, fmt.Errorf("open %s: %w", name, err)
		}
		defer f.Close()

		var lines []string
		sc := bufio.NewScanner(f)
		for sc.Scan() {
			lines = append(lines, strings.TrimSpace(sc.Text()))
		}
		if err := sc.Err(); err != nil {
			return nil, fmt.Errorf("scan %s: %w", name, err)
		}
		return lines, nil
	}

	sp, err := load("species.txt")
	if err != nil {
		return nil, err
	}
	mv, err := load("moves.txt")
	if err != nil {
		return nil, err
	}
	it, err := load("items.txt")
	if err != nil {
		return nil, err
	}
	ab, err := load("abilities.txt")
	if err != nil {
		return nil, err
	}

	return &Tables{
		Species:   sp,
		Moves:     mv,
		Items:     it,
		Abilities: ab,
	}, nil
}

// CryptLCRNG applies the Pokemon LCRNG XOR stream to buf in-place on a copy.
func CryptLCRNG(buf []byte, seed uint32) []byte {
	out := make([]byte, len(buf))
	copy(out, buf)
	for i := 0; i+1 < len(out); i += 2 {
		seed = seed*0x41C64E6D + 0x00006073
		xorVal := uint16(seed >> 16)
		out[i] ^= byte(xorVal & 0xFF)
		out[i+1] ^= byte(xorVal >> 8)
	}
	return out
}

func shuffleBlocks(body []byte, sv byte) []byte {
	out := make([]byte, 320)
	base := int(sv) * 4
	for i := range 4 {
		srcBlk := int(blockPos[base+i])
		copy(out[i*80:(i+1)*80], body[srcBlk*80:(srcBlk+1)*80])
	}
	return out
}

// DecryptPK decrypts and unshuffles a 344-byte PK9/PB8 byte slice.
func DecryptPK(raw []byte) []byte {
	pk := make([]byte, SlotSize)
	copy(pk, raw)
	ec := binary.LittleEndian.Uint32(pk[0:4])
	sv := byte((ec >> 13) & 31)
	body := CryptLCRNG(pk[8:328], ec)
	stats := CryptLCRNG(pk[328:344], ec)
	copy(pk[8:328], shuffleBlocks(body, sv))
	copy(pk[328:344], stats)
	return pk
}

// ComputeChecksum computes the 16-bit sum over the 160 uint16 words in [8:328].
func ComputeChecksum(dec []byte) uint16 {
	var sum uint16
	for i := 8; i < 328; i += 2 {
		sum += binary.LittleEndian.Uint16(dec[i : i+2])
	}
	return sum
}

// VerifyChecksum checks that the stored checksum at 0x06 matches the computed checksum.
func VerifyChecksum(dec []byte) bool {
	stored := binary.LittleEndian.Uint16(dec[0x06:0x08])
	return stored != 0 && stored == ComputeChecksum(dec)
}

// EncryptPK updates the checksum, shuffles, and encrypts a decrypted 344-byte PK9/PB8.
func EncryptPK(dec []byte) []byte {
	pk := make([]byte, SlotSize)
	copy(pk, dec)
	chk := ComputeChecksum(pk)
	binary.LittleEndian.PutUint16(pk[4:6], 0)
	binary.LittleEndian.PutUint16(pk[6:8], chk)
	ec := binary.LittleEndian.Uint32(pk[0:4])
	sv := blockPosInvert[(ec>>13)&31]
	shuffled := shuffleBlocks(pk[8:328], sv)
	copy(pk[8:328], CryptLCRNG(shuffled, ec))
	copy(pk[328:344], CryptLCRNG(pk[328:344], ec))
	return pk
}

// CalcStats computes level-scaled stats in (HP, Atk, Def, Spe, SpA, SpD) order.
// baseStats, ivs, and evs are in (HP, Atk, Def, SpA, SpD, Spe) order.
func CalcStats(baseStats, ivs, evs [6]int, level int, natureID int) [6]int {
	hp := ((2*baseStats[0]+ivs[0]+(evs[0]/4))*level)/100 + level + 10
	raw := [5]int{
		((2*baseStats[1]+ivs[1]+(evs[1]/4))*level)/100 + 5,
		((2*baseStats[2]+ivs[2]+(evs[2]/4))*level)/100 + 5,
		((2*baseStats[5]+ivs[5]+(evs[5]/4))*level)/100 + 5,
		((2*baseStats[3]+ivs[3]+(evs[3]/4))*level)/100 + 5,
		((2*baseStats[4]+ivs[4]+(evs[4]/4))*level)/100 + 5,
	}
	plus := natureID / 5
	minus := natureID % 5
	if plus != minus {
		raw[plus] = (raw[plus] * 110) / 100
		raw[minus] = (raw[minus] * 90) / 100
	}
	return [6]int{hp, raw[0], raw[1], raw[2], raw[3], raw[4]}
}

// GetSpeciesName resolves the display species name including regional/form variants.
func GetSpeciesName(spID uint16, form byte, tables *Tables, isSV bool) string {
	natID := spID
	if isSV {
		if mapped, ok := svInternalToNational[spID]; ok {
			natID = mapped
		}
	}

	base := fmt.Sprintf("Species#%d", natID)
	if int(natID) < len(tables.Species) {
		base = tables.Species[natID]
	}

	switch {
	case natID == 103 && form == 1:
		return "Exeggutor-Alola"
	case natID == 706 && form == 1:
		return "Goodra-Hisui"
	case natID == 1017:
		switch form {
		case 1:
			return "Ogerpon-Wellspring"
		case 2:
			return "Ogerpon-Hearthflame"
		case 3:
			return "Ogerpon-Cornerstone"
		}
	}
	return base
}

func decodeUTF16LE(b []byte) string {
	u16 := make([]uint16, 0, len(b)/2)
	for i := 0; i+1 < len(b); i += 2 {
		v := binary.LittleEndian.Uint16(b[i : i+2])
		if v == 0 {
			break
		}
		u16 = append(u16, v)
	}
	return string(utf16.Decode(u16))
}

// Pokemon holds parsed fields from a decrypted PK9/PB8 slot.
type Pokemon struct {
	SpeciesRaw  uint16
	SpeciesName string
	Nickname    string
	Level       int
	IsEgg       bool
	Item        string
	Ability     string
	Nature      string
	TeraType    string
	EVs         [6]int // HP, Atk, Def, SpA, SpD, Spe
	IVs         [6]int // HP, Atk, Def, SpA, SpD, Spe
	Stats       [6]int // HP, Atk, Def, SpA, SpD, Spe
	Moves       []string
	RawDec      []byte
}

// ParseMon decodes a decrypted 344-byte PK9/PB8 slice into a Pokemon struct.
func ParseMon(dec []byte, tables *Tables, isSV bool) (*Pokemon, bool) {
	if len(dec) < SlotSize {
		return nil, false
	}
	spRaw := binary.LittleEndian.Uint16(dec[0x08:0x0A])
	if spRaw == 0 {
		return nil, false
	}

	itID := int(binary.LittleEndian.Uint16(dec[0x0A:0x0C]))
	abID := int(binary.LittleEndian.Uint16(dec[0x14:0x16]))
	snatID := int(dec[0x21])
	form := dec[0x24]

	evHP, evAtk, evDef, evSpe, evSpA, evSpD := int(dec[0x26]), int(dec[0x27]), int(dec[0x28]), int(dec[0x29]), int(dec[0x2A]), int(dec[0x2B])
	nick := decodeUTF16LE(dec[0x58:0x72])

	iv32 := binary.LittleEndian.Uint32(dec[0x8C:0x90])
	isEgg := ((iv32 >> 30) & 1) != 0
	var rawIVs [6]int
	for s := range 6 {
		rawIVs[s] = int((iv32 >> (s * 5)) & 0x1F)
	}

	lv := int(dec[0x148])
	mhp := int(binary.LittleEndian.Uint16(dec[0x14A:0x14C]))
	atk := int(binary.LittleEndian.Uint16(dec[0x14C:0x14E]))
	dfn := int(binary.LittleEndian.Uint16(dec[0x14E:0x150]))
	spe := int(binary.LittleEndian.Uint16(dec[0x150:0x152]))
	spa := int(binary.LittleEndian.Uint16(dec[0x152:0x154]))
	spd := int(binary.LittleEndian.Uint16(dec[0x154:0x156]))

	spName := GetSpeciesName(spRaw, form, tables, isSV)
	itemName := "None"
	if itID > 0 && itID < len(tables.Items) {
		itemName = tables.Items[itID]
	}
	abilName := fmt.Sprintf("Ability#%d", abID)
	if abID > 0 && abID < len(tables.Abilities) {
		abilName = tables.Abilities[abID]
	}
	natName := "Hardy"
	if snatID >= 0 && snatID < len(Natures) {
		natName = Natures[snatID]
	}

	var moveNames []string
	for i := range 4 {
		mv := int(binary.LittleEndian.Uint16(dec[0x72+i*2 : 0x74+i*2]))
		if mv == 0 {
			continue
		}
		if !isSV && mv == 603 && spRaw == 959 {
			moveNames = append(moveNames, "Gigaton Hammer")
		} else if mv > 0 && mv < len(tables.Moves) {
			moveNames = append(moveNames, tables.Moves[mv])
		}
	}

	teraStr := ""
	if isSV {
		tOrig, tOver := int(dec[0x94]), int(dec[0x95])
		tIdx := 0
		if tOver < len(TeraTypes) {
			tIdx = tOver
		} else if tOrig < len(TeraTypes) {
			tIdx = tOrig
		}
		teraStr = TeraTypes[tIdx]
	}

	rawCopy := make([]byte, SlotSize)
	copy(rawCopy, dec[:SlotSize])

	return &Pokemon{
		SpeciesRaw:  spRaw,
		SpeciesName: spName,
		Nickname:    nick,
		Level:       lv,
		IsEgg:       isEgg,
		Item:        itemName,
		Ability:     abilName,
		Nature:      natName,
		TeraType:    teraStr,
		EVs:         [6]int{evHP, evAtk, evDef, evSpA, evSpD, evSpe},
		IVs:         [6]int{rawIVs[0], rawIVs[1], rawIVs[2], rawIVs[4], rawIVs[5], rawIVs[3]},
		Stats:       [6]int{mhp, atk, dfn, spa, spd, spe},
		Moves:       moveNames,
		RawDec:      rawCopy,
	}, true
}

// ToShowdown formats the Pokemon as a Pokemon Showdown export block.
func (p *Pokemon) ToShowdown() string {
	if p.IsEgg {
		return fmt.Sprintf("Egg (%s)\nLevel: %d\n", p.SpeciesName, p.Level)
	}

	hdr := p.SpeciesName
	if p.Nickname != "" && p.Nickname != p.SpeciesName {
		hdr = fmt.Sprintf("%s (%s)", p.Nickname, p.SpeciesName)
	}
	if p.Item != "None" {
		hdr += fmt.Sprintf(" @ %s", p.Item)
	}

	lines := []string{
		hdr,
		fmt.Sprintf("Ability: %s", p.Ability),
		fmt.Sprintf("Level: %d", p.Level),
	}
	if p.TeraType != "" {
		lines = append(lines, fmt.Sprintf("Tera Type: %s", p.TeraType))
	}

	labels := [6]string{"HP", "Atk", "Def", "SpA", "SpD", "Spe"}
	var evParts []string
	for i, v := range p.EVs {
		if v > 0 {
			evParts = append(evParts, fmt.Sprintf("%d %s", v, labels[i]))
		}
	}
	if len(evParts) > 0 {
		lines = append(lines, "EVs: "+strings.Join(evParts, " / "))
	}

	lines = append(lines, fmt.Sprintf("%s Nature", p.Nature))

	var ivParts []string
	for i, v := range p.IVs {
		if v < 31 {
			ivParts = append(ivParts, fmt.Sprintf("%d %s", v, labels[i]))
		}
	}
	if len(ivParts) > 0 {
		lines = append(lines, "IVs: "+strings.Join(ivParts, " / "))
	}

	for _, mv := range p.Moves {
		lines = append(lines, fmt.Sprintf("- %s", mv))
	}
	return strings.Join(lines, "\n") + "\n"
}
