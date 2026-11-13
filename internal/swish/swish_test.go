package swish

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"
)

func TestCryptStaticXorpadRoundtrip(t *testing.T) {
	orig := []byte("Pokemon Scarlet SwishCrypto test payload with > 128 bytes! " +
		"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
	enc := CryptStaticXorpad(orig)
	if bytes.Equal(orig, enc) {
		t.Fatal("encrypted payload should differ from original")
	}
	dec := CryptStaticXorpad(enc)
	if !bytes.Equal(orig, dec) {
		t.Fatalf("roundtrip mismatch: got %q, want %q", dec, orig)
	}
}

func TestXorShift32Deterministic(t *testing.T) {
	a := NewXorShift32(KeyBox)
	b := NewXorShift32(KeyBox)
	if !bytes.Equal(a.Keystream(64), b.Keystream(64)) {
		t.Fatal("XorShift32 keystream should be deterministic for identical seeds")
	}
}

func TestRealScarletSaveHashAndSCBlocks(t *testing.T) {
	savePath := filepath.Join("..", "..", "Pokemon_Scarlet", "raw_saves", "main")
	raw, err := os.ReadFile(savePath)
	if err != nil {
		t.Fatalf("read save: %v", err)
	}
	if len(raw) < 32 {
		t.Fatalf("unexpected save length: %d", len(raw))
	}

	gotHash := ComputeSaveHash(raw[:len(raw)-32])
	if !bytes.Equal(gotHash[:], raw[len(raw)-32:]) {
		t.Fatal("Scarlet save SHA-256 footer mismatch")
	}

	dec := CryptStaticXorpad(raw[:len(raw)-32])
	blocks, err := FindSCBlocks(dec, map[uint32]bool{KeyParty: true, KeyBox: true})
	if err != nil {
		t.Fatalf("FindSCBlocks failed: %v", err)
	}
	if len(blocks[KeyParty].Data) < 6*344 {
		t.Fatalf("unexpected party block size: %d", len(blocks[KeyParty].Data))
	}
	if len(blocks[KeyBox].Data) < 32*30*344 {
		t.Fatalf("unexpected box block size: %d", len(blocks[KeyBox].Data))
	}
}
