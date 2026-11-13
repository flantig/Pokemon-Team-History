#!/usr/bin/env python3
"""
Injects Smogon-configured Pokemon into the first available PC Box slots
of a Pokemon Scarlet save file (`main`):
  1. Palafin (Choice Band All-Out Attacker)
  2. Goodra-Hisui (Assault Vest Tank)
  3. Clodsire (Water Absorb Special Wall / Hazard Setter)
  4. Porygon2 (Eviolite Defensive Tank & Pivot)
  5. Porygon (Eviolite Little Cup / NFE Tank)
"""

import hashlib
import os
import shutil
import struct
import sys
from datetime import datetime

INTRO_HASH_BYTES = bytes([
    0x9E, 0xC9, 0x9C, 0xD7, 0x0E, 0xD3, 0x3C, 0x44, 0xFB, 0x93, 0x03, 0xDC, 0xEB, 0x39, 0xB4, 0x2A,
    0x19, 0x47, 0xE9, 0x63, 0x4B, 0xA2, 0x33, 0x44, 0x16, 0xBF, 0x82, 0xA2, 0xBA, 0x63, 0x55, 0xB6,
    0x3D, 0x9D, 0xF2, 0x4B, 0x5F, 0x7B, 0x6A, 0xB2, 0x62, 0x1D, 0xC2, 0x1B, 0x68, 0xE5, 0xC8, 0xB5,
    0x3A, 0x05, 0x90, 0x00, 0xE8, 0xA8, 0x10, 0x3D, 0xE2, 0xEC, 0xF0, 0x0C, 0xB2, 0xED, 0x4F, 0x6D,
])

OUTRO_HASH_BYTES = bytes([
    0xD6, 0xC0, 0x1C, 0x59, 0x8B, 0xC8, 0xB8, 0xCB, 0x46, 0xE1, 0x53, 0xFC, 0x82, 0x8C, 0x75, 0x75,
    0x13, 0xE0, 0x45, 0xDF, 0x32, 0x69, 0x3C, 0x75, 0xF0, 0x59, 0xF8, 0xD9, 0xA2, 0x5F, 0xB2, 0x17,
    0xE0, 0x80, 0x52, 0xDB, 0xEA, 0x89, 0x73, 0x99, 0x75, 0x79, 0xAF, 0xCB, 0x2E, 0x80, 0x07, 0xE6,
    0xF1, 0x26, 0xE0, 0x03, 0x0A, 0xE6, 0x6F, 0xF6, 0x41, 0xBF, 0x7E, 0x59, 0xC2, 0xAE, 0x55, 0xFD,
])

STATIC_XORPAD = bytes([
    0xA0, 0x92, 0xD1, 0x06, 0x07, 0xDB, 0x32, 0xA1, 0xAE, 0x01, 0xF5, 0xC5, 0x1E, 0x84, 0x4F, 0xE3,
    0x53, 0xCA, 0x37, 0xF4, 0xA7, 0xB0, 0x4D, 0xA0, 0x18, 0xB7, 0xC2, 0x97, 0xDA, 0x5F, 0x53, 0x2B,
    0x75, 0xFA, 0x48, 0x16, 0xF8, 0xD4, 0x8A, 0x6F, 0x61, 0x05, 0xF4, 0xE2, 0xFD, 0x04, 0xB5, 0xA3,
    0x0F, 0xFC, 0x44, 0x92, 0xCB, 0x32, 0xE6, 0x1B, 0xB9, 0xB1, 0x2E, 0x01, 0xB0, 0x56, 0x53, 0x36,
    0xD2, 0xD1, 0x50, 0x3D, 0xDE, 0x5B, 0x2E, 0x0E, 0x52, 0xFD, 0xDF, 0x2F, 0x7B, 0xCA, 0x63, 0x50,
    0xA4, 0x67, 0x5D, 0x23, 0x17, 0xC0, 0x52, 0xE1, 0xA6, 0x30, 0x7C, 0x2B, 0xB6, 0x70, 0x36, 0x5B,
    0x2A, 0x27, 0x69, 0x33, 0xF5, 0x63, 0x7B, 0x36, 0x3F, 0x26, 0x9B, 0xA3, 0xED, 0x7A, 0x53, 0x00,
    0xA4, 0x48, 0xB3, 0x50, 0x9E, 0x14, 0xA0, 0x52, 0xDE, 0x7E, 0x10, 0x2B, 0x1B, 0x77, 0x6E,
])

BLOCK_POS = [
    0, 1, 2, 3,  0, 1, 3, 2,  0, 2, 1, 3,  0, 3, 1, 2,
    0, 2, 3, 1,  0, 3, 2, 1,  1, 0, 2, 3,  1, 0, 3, 2,
    2, 0, 1, 3,  3, 0, 1, 2,  2, 0, 3, 1,  3, 0, 2, 1,
    1, 2, 0, 3,  1, 3, 0, 2,  2, 1, 0, 3,  3, 1, 0, 2,
    2, 3, 0, 1,  3, 2, 0, 1,  1, 2, 3, 0,  1, 3, 2, 0,
    2, 1, 3, 0,  3, 1, 2, 0,  2, 3, 1, 0,  3, 2, 1, 0,
    0, 1, 2, 3,  0, 1, 3, 2,  0, 2, 1, 3,  0, 3, 1, 2,
    0, 2, 3, 1,  0, 3, 2, 1,  1, 0, 2, 3,  1, 0, 3, 2,
]

BLOCK_POS_INVERT = [
    0, 1, 2, 4, 3, 5, 6, 7, 12, 18, 13, 19, 8, 10, 14, 20,
    16, 22, 9, 11, 15, 21, 17, 23, 0, 1, 2, 4, 3, 5, 6, 7,
]

TYPE_SIZES = {3: 1, 8: 1, 9: 2, 10: 4, 11: 8, 12: 1, 13: 2, 14: 4, 15: 8, 16: 4, 17: 8}

K_BOX = 0x0D66012C
K_PARTY = 0x3AA1A9AD


class XorShift32:
    def __init__(self, seed: int):
        s = seed & 0xFFFFFFFF
        for _ in range(bin(s).count("1")):
            s = self._adv(s)
        self.state = s
        self.counter = 0

    @staticmethod
    def _adv(s: int) -> int:
        s ^= (s << 2) & 0xFFFFFFFF
        s ^= s >> 15
        s ^= (s << 13) & 0xFFFFFFFF
        return s

    def next_byte(self) -> int:
        c = self.counter
        res = (self.state >> (c << 3)) & 0xFF
        if c == 3:
            self.state = self._adv(self.state)
            self.counter = 0
        else:
            self.counter += 1
        return res

    def next_i32(self) -> int:
        return (
            self.next_byte()
            | (self.next_byte() << 8)
            | (self.next_byte() << 16)
            | (self.next_byte() << 24)
        )

    def get_keystream(self, n: int) -> bytearray:
        out = bytearray(n)
        s, c = self.state, self.counter
        for i in range(n):
            out[i] = (s >> (c << 3)) & 0xFF
            if c == 3:
                s ^= (s << 2) & 0xFFFFFFFF
                s ^= s >> 15
                s ^= (s << 13) & 0xFFFFFFFF
                c = 0
            else:
                c += 1
        self.state, self.counter = s, c
        return out


def compute_save_hash(encrypted_payload: bytes) -> bytes:
    h = hashlib.sha256()
    h.update(INTRO_HASH_BYTES)
    h.update(encrypted_payload)
    h.update(OUTRO_HASH_BYTES)
    return h.digest()


def crypt_static_xorpad(payload: bytearray) -> bytearray:
    xp_rep = (STATIC_XORPAD * (len(payload) // len(STATIC_XORPAD) + 1))[: len(payload)]
    return bytearray(a ^ b for a, b in zip(payload, xp_rep))


def find_scblocks(decrypted_payload: bytearray, target_keys: set) -> dict:
    offset = 0
    found = {}
    while offset < len(decrypted_payload):
        key = struct.unpack_from("<I", decrypted_payload, offset)[0]
        offset += 4
        xk = XorShift32(key)
        btype = decrypted_payload[offset] ^ xk.next_byte()
        offset += 1
        if btype in (1, 2, 3):
            continue
        elif btype == 4:
            nbytes = struct.unpack_from("<I", decrypted_payload, offset)[0] ^ xk.next_i32()
            offset += 4
            if key in target_keys:
                ks = xk.get_keystream(nbytes)
                bdata = bytearray(a ^ b for a, b in zip(decrypted_payload[offset : offset + nbytes], ks))
                found[key] = (offset, nbytes, ks, bdata)
            offset += nbytes
        elif btype == 5:
            nentries = struct.unpack_from("<I", decrypted_payload, offset)[0] ^ xk.next_i32()
            offset += 4
            subtype = decrypted_payload[offset] ^ xk.next_byte()
            offset += 1
            offset += nentries * TYPE_SIZES[subtype]
        else:
            offset += TYPE_SIZES[btype]
    return found


def crypt_lcrng(buf: bytes, seed: int) -> bytearray:
    out = bytearray(buf)
    for i in range(0, len(out), 2):
        seed = (seed * 0x41C64E6D + 0x00006073) & 0xFFFFFFFF
        xor_val = (seed >> 16) & 0xFFFF
        out[i] ^= xor_val & 0xFF
        out[i + 1] ^= (xor_val >> 8) & 0xFF
    return out


def shuffle_blocks(body: bytes, sv: int) -> bytearray:
    out = bytearray(320)
    for i in range(4):
        src_blk = BLOCK_POS[sv * 4 + i]
        out[i * 80 : (i + 1) * 80] = body[src_blk * 80 : (src_blk + 1) * 80]
    return out


def decrypt_pk9(raw_pk: bytes) -> bytearray:
    pk = bytearray(raw_pk)
    ec = struct.unpack_from("<I", pk, 0)[0]
    sv = (ec >> 13) & 31
    body = crypt_lcrng(pk[8:328], ec)
    stats = crypt_lcrng(pk[328:344], ec)
    pk[8:328] = shuffle_blocks(body, sv)
    pk[328:344] = stats
    return pk


def encrypt_pk9(dec_pk: bytearray) -> bytearray:
    pk = bytearray(dec_pk)
    chk = sum(struct.unpack_from("<160H", pk, 8)) & 0xFFFF
    struct.pack_into("<H", pk, 4, 0)
    struct.pack_into("<H", pk, 6, chk)
    ec = struct.unpack_from("<I", pk, 0)[0]
    sv = BLOCK_POS_INVERT[(ec >> 13) & 31]
    shuffled = shuffle_blocks(pk[8:328], sv)
    pk[8:328] = crypt_lcrng(shuffled, ec)
    pk[328:344] = crypt_lcrng(pk[328:344], ec)
    return pk


def set_utf16_string(buf: bytearray, offset: int, max_bytes: int, text: str):
    buf[offset : offset + max_bytes] = b"\x00" * max_bytes
    encoded = (text + "\x00").encode("utf-16le")[:max_bytes]
    buf[offset : offset + len(encoded)] = encoded


def calc_stats(base_stats, level: int, ivs, evs, nature_id: int):
    hp_b, atk_b, def_b, spa_b, spd_b, spe_b = base_stats
    hp_i, atk_i, def_i, spa_i, spd_i, spe_i = ivs
    hp_e, atk_e, def_e, spa_e, spd_e, spe_e = evs

    hp = ((2 * hp_b + hp_i + (hp_e // 4)) * level) // 100 + level + 10

    raw = [
        ((2 * atk_b + atk_i + (atk_e // 4)) * level) // 100 + 5,
        ((2 * def_b + def_i + (def_e // 4)) * level) // 100 + 5,
        ((2 * spe_b + spe_i + (spe_e // 4)) * level) // 100 + 5,
        ((2 * spa_b + spa_i + (spa_e // 4)) * level) // 100 + 5,
        ((2 * spd_b + spd_i + (spd_e // 4)) * level) // 100 + 5,
    ]
    plus = nature_id // 5
    minus = nature_id % 5
    if plus != minus:
        raw[plus] = (raw[plus] * 110) // 100
        raw[minus] = (raw[minus] * 90) // 100

    return hp, raw[0], raw[1], raw[2], raw[3], raw[4]


def build_smogon_pk9(
    donor_dec: bytearray,
    *,
    ec: int,
    pid: int,
    species_internal: int,
    form: int,
    nickname: str,
    level: int,
    exp_growth: int,
    ability_id: int,
    ability_num: int,
    nature_id: int,
    gender: int,
    held_item: int,
    tera_type: int,
    evs_h_a_b_s_c_d,
    ivs_h_a_b_s_c_d=(31, 31, 31, 31, 31, 31),
    moves_with_pp,
    relearn_moves,
    base_stats_h_a_b_c_d_s,
    ball: int,
    met_loc: int,
    met_lvl: int,
) -> bytearray:
    pk = bytearray(donor_dec)

    pk[0x34:0x48] = b"\x00" * (0x48 - 0x34)
    pk[0x4B:0x58] = b"\x00" * (0x58 - 0x4B)
    pk[0x12F:0x148] = b"\x00" * (0x148 - 0x12F)
    pk[0x126] = 0
    struct.pack_into("<Q", pk, 0x127, 0)

    struct.pack_into("<I", pk, 0x00, ec)
    struct.pack_into("<H", pk, 0x08, species_internal)
    struct.pack_into("<H", pk, 0x0A, held_item)

    if exp_growth == 5:  # Slow
        exp = (5 * (level ** 3)) // 4
    else:  # Medium Fast (0)
        exp = level ** 3
    struct.pack_into("<I", pk, 0x10, exp)
    struct.pack_into("<H", pk, 0x14, ability_id)
    pk[0x16] = ability_num & 7
    struct.pack_into("<H", pk, 0x18, 0)
    struct.pack_into("<I", pk, 0x1C, pid)
    pk[0x20] = nature_id
    pk[0x21] = nature_id
    pk[0x22] = (gender & 3) << 1
    struct.pack_into("<H", pk, 0x24, form)

    for i, ev_val in enumerate(evs_h_a_b_s_c_d):
        pk[0x26 + i] = ev_val

    pk[0x48] = 128
    pk[0x49] = 128
    pk[0x4A] = 128

    set_utf16_string(pk, 0x58, 26, nickname)

    for i in range(4):
        m_id, m_pp = moves_with_pp[i] if i < len(moves_with_pp) else (0, 0)
        struct.pack_into("<H", pk, 0x72 + i * 2, m_id)
        pk[0x7A + i] = m_pp
        pk[0x7E + i] = 3 if m_id else 0

    for i in range(4):
        rm_id = relearn_moves[i] if i < len(relearn_moves) else 0
        struct.pack_into("<H", pk, 0x82 + i * 2, rm_id)

    iv_hp, iv_atk, iv_def, iv_spe, iv_spa, iv_spd = ivs_h_a_b_s_c_d
    iv32 = (
        (iv_hp & 0x1F)
        | ((iv_atk & 0x1F) << 5)
        | ((iv_def & 0x1F) << 10)
        | ((iv_spe & 0x1F) << 15)
        | ((iv_spa & 0x1F) << 20)
        | ((iv_spd & 0x1F) << 25)
    )
    struct.pack_into("<I", pk, 0x8C, iv32)
    struct.pack_into("<i", pk, 0x90, 0)
    pk[0x94] = tera_type
    pk[0x95] = 19

    pk[0xA8:0xC2] = b"\x00" * 26
    pk[0xC2] = 0
    pk[0xC3] = 0
    pk[0xC4] = 0
    pk[0xC8] = 0
    pk[0xD0:0xD4] = b"\x00" * 4
    pk[0xD4] = 0xFF

    pk[0x112] = 255
    pk[0x11F] = met_lvl
    struct.pack_into("<H", pk, 0x120, 0)
    struct.pack_into("<H", pk, 0x122, met_loc)
    pk[0x124] = ball
    ot_gender = pk[0x125] & 0x80
    pk[0x125] = ot_gender | (met_lvl & 0x7F)

    ev_hp, ev_atk, ev_def, ev_spe, ev_spa, ev_spd = evs_h_a_b_s_c_d
    hp, atk, dfn, spe, spa, spd = calc_stats(
        base_stats_h_a_b_c_d_s,
        level,
        (iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe),
        (ev_hp, ev_atk, ev_def, ev_spa, ev_spd, ev_spe),
        nature_id,
    )
    struct.pack_into("<H", pk, 0x8A, hp)
    pk[0x148] = level
    pk[0x149] = 0
    struct.pack_into("<HHHHHH", pk, 0x14A, hp, atk, dfn, spe, spa, spd)

    return pk


def main():
    save_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "/home/franklinl/.gemini/antigravity-cli/brain/51b0e9b6-5336-4a78-8edd-4989f4420637/scratch/save_backups/main_working"
    )
    backup_dir = "/home/franklinl/.gemini/antigravity-cli/brain/51b0e9b6-5336-4a78-8edd-4989f4420637/scratch/save_backups"
    os.makedirs(backup_dir, exist_ok=True)

    with open(save_path, "rb") as f:
        raw_save = bytearray(f.read())

    if compute_save_hash(raw_save[:-32]) != bytes(raw_save[-32:]):
        raise RuntimeError("Initial save file SHA-256 hash verification failed!")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"main_pre_inject_{ts}")
    if not os.path.exists(backup_path):
        shutil.copy2(save_path, backup_path)

    decrypted_payload = crypt_static_xorpad(raw_save[:-32])
    blocks = find_scblocks(decrypted_payload, {K_BOX, K_PARTY})
    box_offset, box_len, box_ks, box_data = blocks[K_BOX]
    party_offset, party_len, party_ks, party_data = blocks[K_PARTY]

    donor_dec = None
    party_levels = []
    for i in range(6):
        pk_dec = decrypt_pk9(party_data[i * 344 : (i + 1) * 344])
        sp_int = struct.unpack_from("<H", pk_dec, 8)[0]
        if sp_int != 0:
            party_levels.append(pk_dec[0x148])
            if donor_dec is None:
                donor_dec = pk_dec
            if sp_int == 908:  # Meowscarada ("Spaghetti")
                nick = pk_dec[0x58:0x72].decode("utf-16le", errors="ignore").split("\x00")[0]
                old_nat = pk_dec[0x20]
                pk_dec[0x20] = 13  # Jolly (+Spe, -SpA)
                pk_dec[0x21] = 13  # StatNature = Jolly
                lvl = pk_dec[0x148]
                ev_hp, ev_atk, ev_def, ev_spe, ev_spa, ev_spd = pk_dec[0x26:0x2C]
                iv32 = struct.unpack_from("<I", pk_dec, 0x8C)[0]
                ht = pk_dec[0x126]
                iv_hp = 31 if (ht & (1 << 0)) else ((iv32 >> 0) & 0x1F)
                iv_atk = 31 if (ht & (1 << 1)) else ((iv32 >> 5) & 0x1F)
                iv_def = 31 if (ht & (1 << 2)) else ((iv32 >> 10) & 0x1F)
                iv_spa = 31 if (ht & (1 << 3)) else ((iv32 >> 20) & 0x1F)
                iv_spd = 31 if (ht & (1 << 4)) else ((iv32 >> 25) & 0x1F)
                iv_spe = 31 if (ht & (1 << 5)) else ((iv32 >> 15) & 0x1F)
                hp, atk, dfn, spe, spa, spd = calc_stats(
                    (76, 110, 70, 81, 70, 123),
                    lvl,
                    (iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe),
                    (ev_hp, ev_atk, ev_def, ev_spa, ev_spd, ev_spe),
                    13,
                )
                struct.pack_into("<H", pk_dec, 0x8A, hp)
                struct.pack_into("<HHHHHH", pk_dec, 0x14A, hp, atk, dfn, spe, spa, spd)
                enc_meow = encrypt_pk9(pk_dec)
                party_data[i * 344 : (i + 1) * 344] = enc_meow
                print(
                    f"Updated Party[{i}] Meowscarada ({nick!r}) nature from {old_nat} to 13 (Jolly), new stats: HP={hp}, Atk={atk}, Def={dfn}, Spe={spe}, SpA={spa}, SpD={spd}"
                )

    decrypted_payload[party_offset : party_offset + party_len] = bytearray(
        a ^ b for a, b in zip(party_data, party_ks)
    )

    if donor_dec is None:
        raise RuntimeError("No donor Pokemon found in party!")

    target_level = max(party_levels) if party_levels else 88
    tid, sid = struct.unpack_from("<HH", donor_dec, 0x0C)
    ot_name = donor_dec[0xF8:0x112].decode("utf-16le", errors="ignore").split("\x00")[0]
    print(f"Donor OT: {ot_name} (TID={tid}, SID={sid}), Party max level: {target_level}")

    tsv = (tid ^ sid) >> 4

    def safe_pid(base_pid: int) -> int:
        if (((base_pid >> 16) ^ (base_pid & 0xFFFF)) >> 4) == tsv:
            return base_pid ^ 0x10000000
        return base_pid

    # 1. Palafin (Choice Band All-Out Attacker)
    palafin_dec = build_smogon_pk9(
        donor_dec,
        ec=0x4D91A2E7,
        pid=safe_pid(0x8421B93C),
        species_internal=934,
        form=0,
        nickname="Palafin",
        level=target_level,
        exp_growth=5,
        ability_id=278,  # Zero to Hero
        ability_num=1,
        nature_id=13,  # Jolly (+Spe, -SpA)
        gender=0,
        held_item=220,  # Choice Band
        tera_type=10,  # Water
        evs_h_a_b_s_c_d=(0, 252, 0, 252, 0, 4),
        moves_with_pp=[(857, 24), (834, 16), (812, 32), (370, 8)],
        relearn_moves=[857, 834, 812, 8],
        base_stats_h_a_b_c_d_s=(100, 70, 72, 53, 62, 100),
        ball=6,
        met_loc=40,
        met_lvl=38,
    )

    # 2. Goodra-Hisui (Assault Vest Tank)
    goodra_dec = build_smogon_pk9(
        donor_dec,
        ec=0x7C38E512,
        pid=safe_pid(0x5E9A31C4),
        species_internal=706,
        form=1,
        nickname="Goodra",
        level=target_level,
        exp_growth=5,
        ability_id=157,  # Sap Sipper
        ability_num=1,
        nature_id=15,  # Modest (+SpA, -Atk)
        gender=1,
        held_item=640,  # Assault Vest
        tera_type=8,  # Steel
        evs_h_a_b_s_c_d=(248, 0, 0, 0, 252, 8),
        moves_with_pp=[(434, 8), (430, 16), (53, 24), (85, 24)],
        relearn_moves=[484, 776, 282, 58],
        base_stats_h_a_b_c_d_s=(80, 100, 100, 110, 150, 60),
        ball=9,
        met_loc=40,
        met_lvl=50,
    )

    # 3. Clodsire (Water Absorb Special Wall & Hazard Setter)
    # SpeciesInternal = 1009 (National Dex #980), Form = 0
    # Ability = 11 (Water Absorb), AbilityNumber = 2
    # Nature = 23 (Careful: +SpD, -SpA), Held Item = 1120 (Heavy-Duty Boots), Tera Type = 8 (Steel)
    # EVs: 248 HP / 8 Def / 252 SpD -> (HP=248, ATK=0, DEF=8, SPE=0, SPA=0, SPD=252)
    # Moves: Earthquake (89), Recover (105), Toxic (92), Stealth Rock (446)
    # Relearn: Spikes (191), Poison Jab (398), Curse (174), Amnesia (133)
    clodsire_dec = build_smogon_pk9(
        donor_dec,
        ec=0x3B82D419,
        pid=safe_pid(0x61C49E2A),
        species_internal=1009,
        form=0,
        nickname="Clodsire",
        level=target_level,
        exp_growth=0,
        ability_id=11,  # Water Absorb
        ability_num=2,  # Ability 2
        nature_id=23,  # Careful (+SpD, -SpA)
        gender=1,
        held_item=1120,  # Heavy-Duty Boots
        tera_type=8,  # Steel
        evs_h_a_b_s_c_d=(248, 0, 8, 0, 0, 252),
        moves_with_pp=[(89, 16), (105, 8), (92, 16), (446, 32)],
        relearn_moves=[191, 398, 174, 133],
        base_stats_h_a_b_c_d_s=(130, 75, 60, 45, 100, 20),
        ball=4,  # Poke Ball
        met_loc=6,  # South Province (Area One)
        met_lvl=20,
    )

    # 4. Porygon2 (Eviolite Defensive Tank / Pivot)
    # SpeciesInternal = 233 (National Dex #233), Form = 0
    # Ability = 36 (Trace), AbilityNumber = 1 (or Download=88 / Analytic=148)
    # Nature = 20 (Calm: +SpD, -Atk), Held Item = 538 (Eviolite), Tera Type = 17 (Fairy)
    # EVs: 252 HP / 120 Def / 136 SpD -> (HP=252, ATK=0, DEF=120, SPE=0, SPA=0, SPD=136)
    # Moves: Tri Attack (161), Ice Beam (58), Recover (105), Discharge (435)
    # Relearn: Trick Room (433), Thunderbolt (85), Foul Play (492), Thunder Wave (86)
    porygon2_dec = build_smogon_pk9(
        donor_dec,
        ec=0x9A47C10B,
        pid=safe_pid(0x2F8E4D11),
        species_internal=233,
        form=0,
        nickname="Porygon2",
        level=target_level,
        exp_growth=0,
        ability_id=36,  # Trace
        ability_num=1,
        nature_id=20,  # Calm (+SpD, -Atk)
        gender=2,  # Genderless
        held_item=538,  # Eviolite
        tera_type=17,  # Fairy
        evs_h_a_b_s_c_d=(252, 0, 120, 0, 0, 136),
        moves_with_pp=[(161, 16), (58, 16), (105, 8), (435, 24)],
        relearn_moves=[433, 85, 492, 86],
        base_stats_h_a_b_c_d_s=(85, 80, 90, 105, 95, 60),
        ball=4,
        met_loc=40,
        met_lvl=35,
    )

    # 5. Porygon (Base Porygon Eviolite Bulky Attacker / Tank)
    # SpeciesInternal = 137 (National Dex #137), Form = 0
    # Ability = 88 (Download), AbilityNumber = 2
    # Nature = 15 (Modest: +SpA, -Atk), Held Item = 538 (Eviolite), Tera Type = 0 (Normal)
    # EVs: 252 HP / 252 SpA / 4 SpD -> (HP=252, ATK=0, DEF=0, SPE=0, SPA=252, SPD=4)
    # Moves: Tri Attack (161), Ice Beam (58), Thunderbolt (85), Recover (105)
    # Relearn: Trick Room (433), Shadow Ball (247), Discharge (435), Thunder Wave (86)
    porygon_dec = build_smogon_pk9(
        donor_dec,
        ec=0xE1529B84,
        pid=safe_pid(0x73D1A059),
        species_internal=137,
        form=0,
        nickname="Porygon",
        level=target_level,
        exp_growth=0,
        ability_id=88,  # Download
        ability_num=2,
        nature_id=15,  # Modest (+SpA, -Atk)
        gender=2,  # Genderless
        held_item=538,  # Eviolite
        tera_type=0,  # Normal
        evs_h_a_b_s_c_d=(252, 0, 0, 0, 252, 4),
        moves_with_pp=[(161, 16), (58, 16), (85, 24), (105, 8)],
        relearn_moves=[433, 247, 435, 86],
        base_stats_h_a_b_c_d_s=(65, 60, 70, 85, 75, 40),
        ball=4,
        met_loc=40,
        met_lvl=25,
    )

    mons_to_inject = [
        (palafin_dec, "Palafin"),
        (goodra_dec, "Goodra-Hisui"),
        (clodsire_dec, "Clodsire (Water Absorb)"),
        (porygon2_dec, "Porygon2 (Eviolite)"),
        (porygon_dec, "Porygon (Eviolite)"),
    ]

    our_ecs = {0x4D91A2E7, 0x7C38E512, 0x3B82D419, 0x9A47C10B, 0xE1529B84}
    target_slots = []
    for slot_idx in range(30 * 32):
        pk_dec = decrypt_pk9(box_data[slot_idx * 344 : (slot_idx + 1) * 344])
        sp_int = struct.unpack_from("<H", pk_dec, 8)[0]
        ec_val = struct.unpack_from("<I", pk_dec, 0)[0]
        if ec_val in our_ecs or sp_int == 0:
            target_slots.append(slot_idx)
            if len(target_slots) == len(mons_to_inject):
                break

    if len(target_slots) < len(mons_to_inject):
        raise RuntimeError("Could not find enough available box slots!")

    for slot_idx, (mon_dec, label) in zip(target_slots, mons_to_inject):
        enc_pk = encrypt_pk9(mon_dec)
        rt_dec = decrypt_pk9(enc_pk)
        chk_stored = struct.unpack_from("<H", rt_dec, 6)[0]
        chk_calc = sum(struct.unpack_from("<160H", rt_dec, 8)) & 0xFFFF
        assert chk_stored == chk_calc, f"Checksum mismatch on {label}!"
        assert bytes(rt_dec[8:]) == bytes(mon_dec[8:]), f"Roundtrip mismatch on {label}!"
        box_data[slot_idx * 344 : (slot_idx + 1) * 344] = enc_pk
        box_num = (slot_idx // 30) + 1
        box_pos = (slot_idx % 30) + 1
        print(f"Injected {label} (Lv. {target_level}) into Box {box_num}, Slot {box_pos} (index {slot_idx})")

    decrypted_payload[box_offset : box_offset + box_len] = bytearray(
        a ^ b for a, b in zip(box_data, box_ks)
    )

    new_encrypted_payload = crypt_static_xorpad(decrypted_payload)
    new_hash = compute_save_hash(new_encrypted_payload)
    out_save = new_encrypted_payload + bytearray(new_hash)

    assert len(out_save) == len(raw_save), "Save length changed!"
    assert compute_save_hash(out_save[:-32]) == bytes(out_save[-32:]), "Final hash invalid!"

    with open(save_path, "wb") as f:
        f.write(out_save)
    print("Successfully updated and verified save file:", save_path)


if __name__ == "__main__":
    main()
