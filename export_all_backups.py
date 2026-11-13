#!/usr/bin/env python3
"""
Exports full Party and Box backups for both Pokemon Scarlet and Pokemon Luminescent Platinum
into /home/franklinl/Documents/Pokemon_Backups/:
- Individual decrypted .pk9 and .pb8 files in pokemon_files/
- Showdown_Export.txt
- Roster_Summary.md
- Top-level README.md
"""

import os
import re
import struct
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "tools"))
import inject_smogon_mons as m
from update_ogerpon_and_natures import NATURES

TXT_DIR = os.path.join(BASE_DIR, "tools", "pkhex_text")
with open(f"{TXT_DIR}/species.txt") as f:
    SPECIES = [l.strip() for l in f]
with open(f"{TXT_DIR}/moves.txt") as f:
    MOVES = [l.strip() for l in f]
with open(f"{TXT_DIR}/items.txt") as f:
    ITEMS = [l.strip() for l in f]
with open(f"{TXT_DIR}/abilities.txt") as f:
    ABILITIES = [l.strip() for l in f]

TERA_TYPES = [
    "Normal", "Fighting", "Flying", "Poison", "Ground", "Rock", "Bug", "Ghost", "Steel",
    "Fire", "Water", "Grass", "Electric", "Psychic", "Ice", "Dragon", "Dark", "Fairy", "Stellar"
]

SV_INT_TO_NAT = {
    908: 908,
    915: 915,
    934: 964,
    944: 922,
    945: 923,
    1005: 937,
    1009: 980,
    1011: 1017,
}


def get_species_name(sp_id: int, form: int, is_sv: bool = False) -> str:
    nat_id = SV_INT_TO_NAT.get(sp_id, sp_id) if is_sv else sp_id
    base = SPECIES[nat_id] if 0 <= nat_id < len(SPECIES) else f"Species#{nat_id}"
    if nat_id == 103 and form == 1:
        return "Exeggutor-Alola"
    if nat_id == 706 and form == 1:
        return "Goodra-Hisui"
    if nat_id == 1017:
        if form == 1:
            return "Ogerpon-Wellspring"
        if form == 2:
            return "Ogerpon-Hearthflame"
        if form == 3:
            return "Ogerpon-Cornerstone"
    return base


def parse_mon(dec: bytes, is_sv: bool = False):
    sp_raw = struct.unpack_from("<H", dec, 0x08)[0]
    if sp_raw == 0:
        return None
    it_id = struct.unpack_from("<H", dec, 0x0A)[0]
    ab_id = struct.unpack_from("<H", dec, 0x14)[0]
    snat_id = dec[0x21]
    form = dec[0x24]
    ev_hp, ev_atk, ev_def, ev_spe, ev_spa, ev_spd = dec[0x26:0x2C]
    nick = dec[0x58:0x72].decode("utf-16-le", errors="ignore").split("\x00")[0]
    m_ids = struct.unpack_from("<HHHH", dec, 0x72)
    iv32 = struct.unpack_from("<I", dec, 0x8C)[0]
    is_egg = bool((iv32 >> 30) & 1)
    ivs = [((iv32 >> (s * 5)) & 0x1F) for s in range(6)]  # HP, ATK, DEF, SPE, SPA, SPD
    lv = dec[0x148]
    mhp, atk, dfn, spe, spa, spd = struct.unpack_from("<HHHHHH", dec, 0x14A)
    sp_name = get_species_name(sp_raw, form, is_sv=is_sv)
    item_name = ITEMS[it_id] if (0 < it_id < len(ITEMS)) else "None"
    abil_name = ABILITIES[ab_id] if (0 < ab_id < len(ABILITIES)) else f"Ability#{ab_id}"
    nat_name = NATURES[snat_id] if snat_id < len(NATURES) else "Hardy"
    move_names = []
    for mv in m_ids:
        if mv == 0:
            continue
        if not is_sv and mv == 603 and sp_raw == 959:
            move_names.append("Gigaton Hammer")
        elif 0 < mv < len(MOVES):
            move_names.append(MOVES[mv])
    tera_str = ""
    if is_sv:
        t_orig, t_over = dec[0x94], dec[0x95]
        t_idx = t_over if t_over < len(TERA_TYPES) else (t_orig if t_orig < len(TERA_TYPES) else 0)
        tera_str = TERA_TYPES[t_idx]
    return {
        "sp_raw": sp_raw,
        "sp_name": sp_name,
        "nick": nick,
        "lv": lv,
        "is_egg": is_egg,
        "item": item_name,
        "ability": abil_name,
        "nature": nat_name,
        "tera": tera_str,
        "evs": (ev_hp, ev_atk, ev_def, ev_spa, ev_spd, ev_spe),
        "ivs": (ivs[0], ivs[1], ivs[2], ivs[4], ivs[5], ivs[3]),
        "stats": (mhp, atk, dfn, spa, spd, spe),
        "moves": move_names,
        "raw_dec": dec,
    }


def to_showdown(info: dict) -> str:
    sp_name = info["sp_name"]
    nick = info["nick"]
    lv = info["lv"]
    item = info["item"]
    ability = info["ability"]
    tera = info["tera"]
    nature = info["nature"]
    if info["is_egg"]:
        return f"Egg ({sp_name})\nLevel: {lv}\n"
    hdr = f"{nick} ({sp_name})" if nick and nick != sp_name else sp_name
    if item != "None":
        hdr += f" @ {item}"
    lines = [hdr, f"Ability: {ability}", f"Level: {lv}"]
    if tera:
        lines.append(f"Tera Type: {tera}")
    ev_labels = ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]
    ev_parts = [f"{v} {l}" for v, l in zip(info["evs"], ev_labels) if v > 0]
    if ev_parts:
        lines.append("EVs: " + " / ".join(ev_parts))
    lines.append(f"{nature} Nature")
    iv_parts = [f"{v} {l}" for v, l in zip(info["ivs"], ev_labels) if v < 31]
    if iv_parts:
        lines.append("IVs: " + " / ".join(iv_parts))
    for mv in info["moves"]:
        lines.append(f"- {mv}")
    return "\n".join(lines) + "\n"


def export_game(game_dir: str, title: str, party_mons: list, box_mons: list, ext: str, is_sv: bool):
    p_dir = os.path.join(game_dir, "pokemon_files")
    os.makedirs(p_dir, exist_ok=True)
    for f in os.listdir(p_dir):
        os.remove(os.path.join(p_dir, f))

    showdown_blocks = []
    md_lines = [f"# {title} - Full Roster Backup\n", "## Active Party (6 Pokemon)\n"]
    if is_sv:
        md_lines.append("| Slot | Nickname | Species | Lv | Tera | Item | Ability | Nature | Stats (HP/Atk/Def/SpA/SpD/Spe) | EVs (HP/Atk/Def/SpA/SpD/Spe) | IVs (HP/Atk/Def/SpA/SpD/Spe) | Moves |")
        md_lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    else:
        md_lines.append("| Slot | Nickname | Species | Lv | Item | Ability | Nature | Stats (HP/Atk/Def/SpA/SpD/Spe) | EVs (HP/Atk/Def/SpA/SpD/Spe) | IVs (HP/Atk/Def/SpA/SpD/Spe) | Moves |")
        md_lines.append("|---|---|---|---|---|---|---|---|---|---|---|")

    for idx, info in enumerate(party_mons, 1):
        nick = info["nick"]
        sp_name = info["sp_name"]
        lv = info["lv"]
        tera = info["tera"]
        item = info["item"]
        ability = info["ability"]
        nature = info["nature"]
        safe_nick = re.sub(r"[^A-Za-z0-9_-]", "_", nick)
        safe_sp = re.sub(r"[^A-Za-z0-9_-]", "_", sp_name)
        fname = f"Party_{idx:02d}_{safe_nick}_{safe_sp}_Lv{lv}.{ext}"
        with open(os.path.join(p_dir, fname), "wb") as f:
            f.write(info["raw_dec"])
        showdown_blocks.append(to_showdown(info))
        st_str = "/".join(str(x) for x in info["stats"])
        ev_str = "/".join(str(x) for x in info["evs"])
        iv_str = "/".join(str(x) for x in info["ivs"])
        mv_str = ", ".join(info["moves"])
        if is_sv:
            md_lines.append(f"| Party {idx} | **{nick}** | {sp_name} | {lv} | {tera} | {item} | {ability} | {nature} | `{st_str}` | `{ev_str}` | `{iv_str}` | {mv_str} |")
        else:
            md_lines.append(f"| Party {idx} | **{nick}** | {sp_name} | {lv} | {item} | {ability} | {nature} | `{st_str}` | `{ev_str}` | `{iv_str}` | {mv_str} |")

    if box_mons:
        md_lines.append(f"\n## PC Boxes ({len(box_mons)} Pokemon)\n")
        md_lines.append("| Location | Nickname | Species | Lv | Item | Ability | Nature | IVs (HP/Atk/Def/SpA/SpD/Spe) | Moves |")
        md_lines.append("|---|---|---|---|---|---|---|---|---|")
        for loc_label, fname_prefix, info in box_mons:
            nick = info["nick"]
            sp_name = info["sp_name"]
            lv = info["lv"]
            item = info["item"]
            ability = info["ability"]
            nature = info["nature"]
            safe_nick = re.sub(r"[^A-Za-z0-9_-]", "_", nick)
            safe_sp = re.sub(r"[^A-Za-z0-9_-]", "_", sp_name)
            fname = f"{fname_prefix}_{safe_nick}_{safe_sp}_Lv{lv}.{ext}"
            with open(os.path.join(p_dir, fname), "wb") as f:
                f.write(info["raw_dec"])
            showdown_blocks.append(to_showdown(info))
            iv_str = "/".join(str(x) for x in info["ivs"])
            mv_str = ", ".join(info["moves"])
            md_lines.append(f"| {loc_label} | **{nick}** | {sp_name} | {lv} | {item} | {ability} | {nature} | `{iv_str}` | {mv_str} |")

    with open(os.path.join(game_dir, "Showdown_Export.txt"), "w") as f:
        f.write("\n".join(showdown_blocks))
    with open(os.path.join(game_dir, "Roster_Summary.md"), "w") as f:
        f.write("\n".join(md_lines) + "\n")
    print(f"Exported {title}: {len(party_mons)} Party, {len(box_mons)} Box -> {game_dir}")


def main():
    # 1. Export Scarlet
    sv_dir = os.path.join(BASE_DIR, "Pokemon_Scarlet")
    with open(os.path.join(sv_dir, "raw_saves", "main"), "rb") as f:
        sv_raw = bytearray(f.read())
    sv_dec = m.crypt_static_xorpad(sv_raw[:-32])
    sv_blocks = m.find_scblocks(sv_dec, {m.K_PARTY, m.K_BOX})
    sv_party_bytes = sv_blocks[m.K_PARTY][3]
    sv_box_bytes = sv_blocks[m.K_BOX][3]

    sv_party = []
    for i in range(6):
        info = parse_mon(m.decrypt_pk9(sv_party_bytes[i * 344 : (i + 1) * 344]), is_sv=True)
        if info:
            sv_party.append(info)

    sv_boxes = []
    for b in range(32):
        for s in range(30):
            idx = b * 30 + s
            info = parse_mon(m.decrypt_pk9(sv_box_bytes[idx * 344 : (idx + 1) * 344]), is_sv=True)
            if info:
                sv_boxes.append((f"Box {b + 1} Slot {s + 1}", f"Box{b + 1:02d}_Slot{s + 1:02d}", info))

    export_game(
        sv_dir,
        "Pokemon Scarlet (Ultimate Scarlet)",
        sv_party,
        sv_boxes,
        "pk9",
        is_sv=True,
    )

    # 1b. Export Imagine Killing Dragons (Box 1 Slots 25-30)
    ikd_dir = os.path.join(BASE_DIR, "Imagine_Killing_Dragons")
    ikd_squad = [
        parse_mon(m.decrypt_pk9(sv_box_bytes[idx * 344 : (idx + 1) * 344]), is_sv=True)
        for idx in range(24, 30)
    ]
    ikd_squad = [mon for mon in ikd_squad if mon is not None]
    export_game(
        ikd_dir,
        "Imagine Killing Dragons (Pokemon Scarlet - Anti-Dragon Squad)",
        ikd_squad,
        [],
        "pk9",
        is_sv=True,
    )

    # 2. Export Luminescent Platinum
    lumi_dir = os.path.join(BASE_DIR, "Pokemon_Luminescent_Platinum")
    with open(os.path.join(lumi_dir, "raw_saves", "SaveData.bin"), "rb") as f:
        lumi_raw = f.read()

    lumi_party = []
    for i in range(6):
        off = 0x014098 + i * 344
        info = parse_mon(m.decrypt_pk9(lumi_raw[off : off + 344]), is_sv=False)
        if info:
            lumi_party.append(info)

    lumi_boxes = []
    for b in range(40):
        for s in range(30):
            idx = b * 30 + s
            off = 0x014EF4 + idx * 344
            if off + 344 > 0x090000:
                break
            chunk = lumi_raw[off : off + 344]
            if chunk[:8] == b"\x00" * 8 or chunk[4:6] != b"\x00\x00":
                continue
            dec = m.decrypt_pk9(chunk)
            chk_stored = struct.unpack_from("<H", dec, 0x06)[0]
            chk_calc = sum(struct.unpack_from("<160H", dec, 0x08)) & 0xFFFF
            if chk_stored != 0 and chk_stored == chk_calc:
                info = parse_mon(dec, is_sv=False)
                if info:
                    lumi_boxes.append((f"Box {b + 1} Slot {s + 1}", f"Box{b + 1:02d}_Slot{s + 1:02d}", info))

    dc_chunk = lumi_raw[0x096080 : 0x096080 + 344]
    dc_dec = m.decrypt_pk9(dc_chunk)
    if struct.unpack_from("<H", dc_dec, 0x06)[0] == (sum(struct.unpack_from("<160H", dc_dec, 0x08)) & 0xFFFF):
        dc_info = parse_mon(dc_dec, is_sv=False)
        if dc_info:
            lumi_boxes.append(("Daycare", "Daycare_Slot01", dc_info))

    export_game(
        lumi_dir,
        "Pokemon Luminescent Platinum",
        lumi_party,
        lumi_boxes,
        "pb8",
        is_sv=False,
    )


if __name__ == "__main__":
    main()
