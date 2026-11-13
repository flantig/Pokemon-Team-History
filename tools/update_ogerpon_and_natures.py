#!/usr/bin/env python3
"""
Updates the user's Pokemon Scarlet save file (`main`):
1. Configures `Ocra` (Ogerpon) with the Smogon Cornerstone Mask build:
   - Form 3 (Cornerstone Mask), Held Item 2406 (Cornerstone Mask), Ability 5 (Sturdy)
   - TeraTypeOriginal = 11 (Grass), TeraTypeOverride = 5 (Rock)
   - Updates Bag (`KItem`) so Hearthflame Mask (2408) is returned to Bag (count=1)
     and Cornerstone Mask (2406) is equipped from Bag (count=0)
   - Jolly Nature (+Spe, -SpA), 31 IVs across all 6 stats, 252 Atk / 4 SpD / 252 Spe EVs
   - Moves: Ivy Cudgel (904), Horn Leech (532), Knock Off (282), Swords Dance (14)
   - Relearn Moves: Power Whip (438), U-turn (369), Superpower (276), Encore (227)
2. Fixes Natures and recalculates stats across both Party (`KParty`) and PC Boxes (`KBox`):
   - `Mesquite` (Ceruledge, sp_int=1005) -> Jolly (13, +Spe, -SpA)
   - `Potato` (Gardevoir, sp_int=282) -> Timid (10, +Spe, -Atk)
   - `Gala` (Gyarados, sp_int=130) -> Jolly (13, +Spe, -SpA)
   - `Spaghetti` (Meowscarada, sp_int=908) -> Jolly (13, +Spe, -SpA)
"""

import os
import shutil
import struct
import sys
from datetime import datetime

sys.path.insert(0, "/home/franklinl/.gemini/antigravity-cli/brain/51b0e9b6-5336-4a78-8edd-4989f4420637/scratch")
import inject_smogon_mons as m

K_ITEM = 0x21C9BD44

BASE_STATS_MAP = {
    130: (95, 125, 79, 60, 100, 81),    # Gyarados
    282: (68, 65, 65, 125, 115, 80),    # Gardevoir
    908: (76, 110, 70, 81, 70, 123),    # Meowscarada
    1005: (75, 125, 80, 60, 100, 85),   # Ceruledge
    1011: (80, 120, 84, 60, 96, 110),   # Ogerpon
}

NATURE_FIX_MAP = {
    130: (13, "Jolly"),    # Gala (Gyarados)
    282: (10, "Timid"),    # Potato (Gardevoir)
    908: (13, "Jolly"),    # Spaghetti (Meowscarada)
    1005: (13, "Jolly"),   # Mesquite (Ceruledge)
}

NATURES = [
    "Hardy", "Lonely", "Brave", "Adamant", "Naughty",
    "Bold", "Docile", "Relaxed", "Impish", "Lax",
    "Timid", "Hasty", "Serious", "Jolly", "Naive",
    "Modest", "Mild", "Quiet", "Bashful", "Rash",
    "Calm", "Gentle", "Sassy", "Careful", "Quirky",
]


def recalc_pk9_stats(pk_dec: bytearray, base_stats):
    lvl = pk_dec[0x148]
    nature_id = pk_dec[0x21]
    ev_hp, ev_atk, ev_def, ev_spe, ev_spa, ev_spd = pk_dec[0x26:0x2C]
    iv32 = struct.unpack_from("<I", pk_dec, 0x8C)[0]
    ht = pk_dec[0x126]
    iv_hp = 31 if (ht & (1 << 0)) else ((iv32 >> 0) & 0x1F)
    iv_atk = 31 if (ht & (1 << 1)) else ((iv32 >> 5) & 0x1F)
    iv_def = 31 if (ht & (1 << 2)) else ((iv32 >> 10) & 0x1F)
    iv_spa = 31 if (ht & (1 << 3)) else ((iv32 >> 20) & 0x1F)
    iv_spd = 31 if (ht & (1 << 4)) else ((iv32 >> 25) & 0x1F)
    iv_spe = 31 if (ht & (1 << 5)) else ((iv32 >> 15) & 0x1F)

    hp, atk, dfn, spe, spa, spd = m.calc_stats(
        base_stats,
        lvl,
        (iv_hp, iv_atk, iv_def, iv_spa, iv_spd, iv_spe),
        (ev_hp, ev_atk, ev_def, ev_spa, ev_spd, ev_spe),
        nature_id,
    )
    struct.pack_into("<H", pk_dec, 0x8A, hp)
    struct.pack_into("<HHHHHH", pk_dec, 0x14A, hp, atk, dfn, spe, spa, spd)
    return hp, atk, dfn, spe, spa, spd


def process_slot(container: bytearray, idx: int, label_prefix: str):
    raw_pk = container[idx * 344 : (idx + 1) * 344]
    pk_dec = m.decrypt_pk9(raw_pk)
    sp_int = struct.unpack_from("<H", pk_dec, 8)[0]
    if sp_int == 0:
        return False

    nick = pk_dec[0x58:0x72].decode("utf-16le", errors="ignore").split("\x00")[0]
    lvl = pk_dec[0x148]

    if sp_int == 1011:  # Ogerpon ('Ocra')
        old_nat = NATURES[pk_dec[0x20]]
        old_form = pk_dec[0x24]
        old_item = struct.unpack_from("<H", pk_dec, 0x0A)[0]

        # Configure Smogon Cornerstone Mask build
        struct.pack_into("<H", pk_dec, 0x24, 3)     # Form 3 = Cornerstone Mask
        struct.pack_into("<H", pk_dec, 0x0A, 2406)  # HeldItem = 2406 (Cornerstone Mask)
        struct.pack_into("<H", pk_dec, 0x14, 5)     # Ability = 5 (Sturdy)
        pk_dec[0x16] = (pk_dec[0x16] & ~7) | 1      # AbilityNumber = 1

        pk_dec[0x20] = 13  # Nature = Jolly (+Spe, -SpA)
        pk_dec[0x21] = 13  # StatNature = Jolly

        # 31 IVs across all 6 stats, preserving IsEgg (bit 30) and IsNicknamed (bit 31)
        old_iv32 = struct.unpack_from("<I", pk_dec, 0x8C)[0]
        new_iv32 = (old_iv32 & 0xC0000000) | 0x3FFFFFFF
        struct.pack_into("<I", pk_dec, 0x8C, new_iv32)
        pk_dec[0x126] = 0  # Clear HyperTrainFlags since all 6 IVs are natural 31

        # EVs: 252 Atk / 4 SpD / 252 Spe (order in PK9: HP, ATK, DEF, SPE, SPA, SPD)
        pk_dec[0x26:0x2C] = bytes([0, 252, 0, 252, 0, 4])

        # Tera Type for Cornerstone Mask: Original=11 (Grass), Override=5 (Rock)
        pk_dec[0x94] = 11
        pk_dec[0x95] = 5

        # Moves (with 3 PP Ups each):
        # Ivy Cudgel (904, 16 PP), Horn Leech (532, 16 PP), Knock Off (282, 32 PP), Swords Dance (14, 32 PP)
        moves_with_pp = [(904, 16), (532, 16), (282, 32), (14, 32)]
        for i, (m_id, m_pp) in enumerate(moves_with_pp):
            struct.pack_into("<H", pk_dec, 0x72 + i * 2, m_id)
            pk_dec[0x7A + i] = m_pp
            pk_dec[0x7E + i] = 3

        # Relearn Moves: Power Whip (438), U-turn (369), Superpower (276), Encore (227)
        relearn_moves = [438, 369, 276, 227]
        for i, rm_id in enumerate(relearn_moves):
            struct.pack_into("<H", pk_dec, 0x82 + i * 2, rm_id)

        pk_dec[0x112] = 255  # Max OT Friendship

        hp, atk, dfn, spe, spa, spd = recalc_pk9_stats(pk_dec, BASE_STATS_MAP[1011])
        enc_pk = m.encrypt_pk9(pk_dec)
        container[idx * 344 : (idx + 1) * 344] = enc_pk
        print(
            f"[{label_prefix}] Updated Ogerpon ({nick!r}, Lv.{lvl}): Form {old_form}->3 (Cornerstone Mask, Item {old_item}->2406), "
            f"Nature {old_nat}->Jolly, 6x31 IVs, 252 Atk / 4 SpD / 252 Spe EVs, "
            f"Stats: HP={hp}, Atk={atk}, Def={dfn}, Spe={spe}, SpA={spa}, SpD={spd}"
        )
        return True

    elif sp_int in NATURE_FIX_MAP:
        target_nat_id, target_nat_name = NATURE_FIX_MAP[sp_int]
        old_nat_id = pk_dec[0x20]
        old_snat_id = pk_dec[0x21]
        old_stats = struct.unpack_from("<HHHHHH", pk_dec, 0x14A)
        pk_dec[0x20] = target_nat_id
        pk_dec[0x21] = target_nat_id
        hp, atk, dfn, spe, spa, spd = recalc_pk9_stats(pk_dec, BASE_STATS_MAP[sp_int])
        new_stats = (hp, atk, dfn, spe, spa, spd)
        if old_nat_id != target_nat_id or old_snat_id != target_nat_id or old_stats != new_stats:
            enc_pk = m.encrypt_pk9(pk_dec)
            container[idx * 344 : (idx + 1) * 344] = enc_pk
            print(
                f"[{label_prefix}] Updated {nick!r} (sp_int={sp_int}, Lv.{lvl}): "
                f"Nature {NATURES[old_nat_id]}->{target_nat_name}, "
                f"Stats: HP={hp}, Atk={atk}, Def={dfn}, Spe={spe}, SpA={spa}, SpD={spd}"
            )
            return True

    return False


def main():
    save_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "/home/franklinl/.gemini/antigravity-cli/brain/51b0e9b6-5336-4a78-8edd-4989f4420637/scratch/save_backups/main_latest_working"
    )
    backup_dir = "/home/franklinl/.gemini/antigravity-cli/brain/51b0e9b6-5336-4a78-8edd-4989f4420637/scratch/save_backups"
    os.makedirs(backup_dir, exist_ok=True)

    with open(save_path, "rb") as f:
        raw_save = bytearray(f.read())

    if m.compute_save_hash(raw_save[:-32]) != bytes(raw_save[-32:]):
        raise RuntimeError("Initial save file SHA-256 hash verification failed!")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"main_pre_ogerpon_{ts}")
    if not os.path.exists(backup_path):
        shutil.copy2(save_path, backup_path)

    decrypted_payload = m.crypt_static_xorpad(raw_save[:-32])
    blocks = m.find_scblocks(decrypted_payload, {m.K_BOX, m.K_PARTY, K_ITEM})
    box_offset, box_len, box_ks, box_data = blocks[m.K_BOX]
    party_offset, party_len, party_ks, party_data = blocks[m.K_PARTY]
    item_offset, item_len, item_ks, item_data = blocks[K_ITEM]

    # Search Party
    for i in range(6):
        process_slot(party_data, i, f"Party[{i}]")

    # Search all 32 Boxes
    for slot_idx in range(30 * 32):
        box_num = (slot_idx // 30) + 1
        box_pos = (slot_idx % 30) + 1
        process_slot(box_data, slot_idx, f"Box{box_num}[{box_pos}]")

    # Update Bag mask counts so Hearthflame Mask (2408) is back in Bag (count=1)
    # and Cornerstone Mask (2406) is held by Ogerpon (count=0 in Bag)
    # Item 2406 (Cornerstone Mask): pouch=4 (Other), count=0, flags=0x4 (IsObtained)
    struct.pack_into("<IIII", item_data, 2406 * 16, 4, 0, 0x4, 0)
    # Item 2407 (Wellspring Mask): pouch=4 (Other), count=1, flags=0x4 (IsObtained)
    struct.pack_into("<IIII", item_data, 2407 * 16, 4, 1, 0x4, 0)
    # Item 2408 (Hearthflame Mask): pouch=4 (Other), count=1, flags=0x4 (IsObtained)
    struct.pack_into("<IIII", item_data, 2408 * 16, 4, 1, 0x4, 0)
    print("Updated Bag mask counts: Cornerstone Mask (equipped, bag=0), Wellspring Mask (bag=1), Hearthflame Mask (returned to bag=1)")

    # Re-encrypt modified blocks into decrypted_payload
    decrypted_payload[party_offset : party_offset + party_len] = bytearray(
        a ^ b for a, b in zip(party_data, party_ks)
    )
    decrypted_payload[box_offset : box_offset + box_len] = bytearray(
        a ^ b for a, b in zip(box_data, box_ks)
    )
    decrypted_payload[item_offset : item_offset + item_len] = bytearray(
        a ^ b for a, b in zip(item_data, item_ks)
    )

    new_encrypted_payload = m.crypt_static_xorpad(decrypted_payload)
    new_hash = m.compute_save_hash(new_encrypted_payload)
    out_save = new_encrypted_payload + bytearray(new_hash)

    assert len(out_save) == len(raw_save), "Save length changed!"
    assert m.compute_save_hash(out_save[:-32]) == bytes(out_save[-32:]), "Final hash invalid!"

    with open(save_path, "wb") as f:
        f.write(out_save)
    print("Successfully updated and verified save file:", save_path)


if __name__ == "__main__":
    main()
