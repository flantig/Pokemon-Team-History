// Package swish implements SwishCrypto block decryption and save hashing for Pokemon Scarlet/Violet saves.
package swish

import (
	"crypto/sha256"
	"encoding/binary"
	"fmt"
	"math/bits"
)

const (
	// KeyBox is the SCBlock key for PC Boxes in Pokemon Scarlet/Violet.
	KeyBox uint32 = 0x0D66012C
	// KeyParty is the SCBlock key for the active Party in Pokemon Scarlet/Violet.
	KeyParty uint32 = 0x3AA1A9AD
)

var (
	introHashBytes = []byte{
		0x9E, 0xC9, 0x9C, 0xD7, 0x0E, 0xD3, 0x3C, 0x44, 0xFB, 0x93, 0x03, 0xDC, 0xEB, 0x39, 0xB4, 0x2A,
		0x19, 0x47, 0xE9, 0x63, 0x4B, 0xA2, 0x33, 0x44, 0x16, 0xBF, 0x82, 0xA2, 0xBA, 0x63, 0x55, 0xB6,
		0x3D, 0x9D, 0xF2, 0x4B, 0x5F, 0x7B, 0x6A, 0xB2, 0x62, 0x1D, 0xC2, 0x1B, 0x68, 0xE5, 0xC8, 0xB5,
		0x3A, 0x05, 0x90, 0x00, 0xE8, 0xA8, 0x10, 0x3D, 0xE2, 0xEC, 0xF0, 0x0C, 0xB2, 0xED, 0x4F, 0x6D,
	}

	outroHashBytes = []byte{
		0xD6, 0xC0, 0x1C, 0x59, 0x8B, 0xC8, 0xB8, 0xCB, 0x46, 0xE1, 0x53, 0xFC, 0x82, 0x8C, 0x75, 0x75,
		0x13, 0xE0, 0x45, 0xDF, 0x32, 0x69, 0x3C, 0x75, 0xF0, 0x59, 0xF8, 0xD9, 0xA2, 0x5F, 0xB2, 0x17,
		0xE0, 0x80, 0x52, 0xDB, 0xEA, 0x89, 0x73, 0x99, 0x75, 0x79, 0xAF, 0xCB, 0x2E, 0x80, 0x07, 0xE6,
		0xF1, 0x26, 0xE0, 0x03, 0x0A, 0xE6, 0x6F, 0xF6, 0x41, 0xBF, 0x7E, 0x59, 0xC2, 0xAE, 0x55, 0xFD,
	}

	staticXorpad = []byte{
		0xA0, 0x92, 0xD1, 0x06, 0x07, 0xDB, 0x32, 0xA1, 0xAE, 0x01, 0xF5, 0xC5, 0x1E, 0x84, 0x4F, 0xE3,
		0x53, 0xCA, 0x37, 0xF4, 0xA7, 0xB0, 0x4D, 0xA0, 0x18, 0xB7, 0xC2, 0x97, 0xDA, 0x5F, 0x53, 0x2B,
		0x75, 0xFA, 0x48, 0x16, 0xF8, 0xD4, 0x8A, 0x6F, 0x61, 0x05, 0xF4, 0xE2, 0xFD, 0x04, 0xB5, 0xA3,
		0x0F, 0xFC, 0x44, 0x92, 0xCB, 0x32, 0xE6, 0x1B, 0xB9, 0xB1, 0x2E, 0x01, 0xB0, 0x56, 0x53, 0x36,
		0xD2, 0xD1, 0x50, 0x3D, 0xDE, 0x5B, 0x2E, 0x0E, 0x52, 0xFD, 0xDF, 0x2F, 0x7B, 0xCA, 0x63, 0x50,
		0xA4, 0x67, 0x5D, 0x23, 0x17, 0xC0, 0x52, 0xE1, 0xA6, 0x30, 0x7C, 0x2B, 0xB6, 0x70, 0x36, 0x5B,
		0x2A, 0x27, 0x69, 0x33, 0xF5, 0x63, 0x7B, 0x36, 0x3F, 0x26, 0x9B, 0xA3, 0xED, 0x7A, 0x53, 0x00,
		0xA4, 0x48, 0xB3, 0x50, 0x9E, 0x14, 0xA0, 0x52, 0xDE, 0x7E, 0x10, 0x2B, 0x1B, 0x77, 0x6E,
	}

	typeSizes = map[byte]int{
		3:  1,
		8:  1,
		9:  2,
		10: 4,
		11: 8,
		12: 1,
		13: 2,
		14: 4,
		15: 8,
		16: 4,
		17: 8,
	}
)

// XorShift32 implements the SCBlock keystream PRNG.
type XorShift32 struct {
	state   uint32
	counter int
}

// NewXorShift32 initializes the PRNG from a 32-bit block key.
func NewXorShift32(seed uint32) *XorShift32 {
	s := seed
	ones := bits.OnesCount32(s)
	for range ones {
		s = advance(s)
	}
	return &XorShift32{state: s}
}

func advance(s uint32) uint32 {
	s ^= s << 2
	s ^= s >> 15
	s ^= s << 13
	return s
}

// NextByte returns the next keystream byte.
func (x *XorShift32) NextByte() byte {
	res := byte((x.state >> (x.counter << 3)) & 0xFF)
	if x.counter == 3 {
		x.state = advance(x.state)
		x.counter = 0
	} else {
		x.counter++
	}
	return res
}

// NextUint32 returns the next 4 keystream bytes as a little-endian uint32.
func (x *XorShift32) NextUint32() uint32 {
	b0 := uint32(x.NextByte())
	b1 := uint32(x.NextByte()) << 8
	b2 := uint32(x.NextByte()) << 16
	b3 := uint32(x.NextByte()) << 24
	return b0 | b1 | b2 | b3
}

// Keystream returns n consecutive keystream bytes.
func (x *XorShift32) Keystream(n int) []byte {
	out := make([]byte, n)
	for i := range n {
		out[i] = x.NextByte()
	}
	return out
}

// ComputeSaveHash computes the 32-byte salted SHA-256 hash for an encrypted save payload.
func ComputeSaveHash(encryptedPayload []byte) [32]byte {
	h := sha256.New()
	h.Write(introHashBytes)
	h.Write(encryptedPayload)
	h.Write(outroHashBytes)
	var sum [32]byte
	copy(sum[:], h.Sum(nil))
	return sum
}

// CryptStaticXorpad XORs payload with the repeating 128-byte static xorpad.
func CryptStaticXorpad(payload []byte) []byte {
	out := make([]byte, len(payload))
	xpLen := len(staticXorpad)
	for i, b := range payload {
		out[i] = b ^ staticXorpad[i%xpLen]
	}
	return out
}

// Block represents a decrypted SCBlock payload and its location/keystream metadata.
type Block struct {
	Offset    int
	Keystream []byte
	Data      []byte
}

// FindSCBlocks scans a decrypted SwishCrypto payload and extracts the requested block keys.
func FindSCBlocks(decryptedPayload []byte, targetKeys map[uint32]bool) (map[uint32]Block, error) {
	found := make(map[uint32]Block, len(targetKeys))
	offset := 0
	n := len(decryptedPayload)

	for offset < n {
		if offset+5 > n {
			return nil, fmt.Errorf("truncated SCBlock header at offset %d", offset)
		}
		key := binary.LittleEndian.Uint32(decryptedPayload[offset:])
		offset += 4

		xk := NewXorShift32(key)
		btype := decryptedPayload[offset] ^ xk.NextByte()
		offset++

		switch btype {
		case 1, 2, 3:
			continue
		case 4:
			if offset+4 > n {
				return nil, fmt.Errorf("truncated type-4 SCBlock length at offset %d", offset)
			}
			nbytes := int(binary.LittleEndian.Uint32(decryptedPayload[offset:]) ^ xk.NextUint32())
			offset += 4
			if offset+nbytes > n {
				return nil, fmt.Errorf("truncated type-4 SCBlock data at offset %d (need %d)", offset, nbytes)
			}
			if targetKeys[key] {
				ks := xk.Keystream(nbytes)
				data := make([]byte, nbytes)
				for i := range nbytes {
					data[i] = decryptedPayload[offset+i] ^ ks[i]
				}
				found[key] = Block{
					Offset:    offset,
					Keystream: ks,
					Data:      data,
				}
			}
			offset += nbytes
		case 5:
			if offset+5 > n {
				return nil, fmt.Errorf("truncated type-5 SCBlock header at offset %d", offset)
			}
			nentries := int(binary.LittleEndian.Uint32(decryptedPayload[offset:]) ^ xk.NextUint32())
			offset += 4
			subtype := decryptedPayload[offset] ^ xk.NextByte()
			offset++
			sz, ok := typeSizes[subtype]
			if !ok {
				return nil, fmt.Errorf("unknown SCBlock array subtype %d at offset %d", subtype, offset)
			}
			offset += nentries * sz
		default:
			sz, ok := typeSizes[btype]
			if !ok {
				return nil, fmt.Errorf("unknown SCBlock type %d at offset %d", btype, offset)
			}
			offset += sz
		}
	}

	return found, nil
}
