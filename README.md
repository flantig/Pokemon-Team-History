# Pokemon Team History & Save Backups

Version-controlled archive of Nintendo Switch Pokemon save files, individual `.pk9` / `.pb8` Pokemon files (compatible with PKHeX), Pokemon Showdown exports, and full roster tables for **Pokemon Scarlet (Ultimate Scarlet)** and **Pokemon Luminescent Platinum**.

---

## 1. Pokemon Scarlet (Ultimate Scarlet) Active Party

- **Full Roster Table (Party + 16 Box Pokemon)**: [Pokemon_Scarlet/Roster_Summary.md](Pokemon_Scarlet/Roster_Summary.md)
- **Pokemon Showdown Export**: [Pokemon_Scarlet/Showdown_Export.txt](Pokemon_Scarlet/Showdown_Export.txt)
- **Individual `.pk9` Files**: [Pokemon_Scarlet/pokemon_files/](Pokemon_Scarlet/pokemon_files/)
- **Raw Switch Saves**: [Pokemon_Scarlet/raw_saves/](Pokemon_Scarlet/raw_saves/)

| Slot | Nickname | Species | Lv | Tera | Held Item | Ability | Nature | Stats (HP/Atk/Def/SpA/SpD/Spe) | EVs (HP/Atk/Def/SpA/SpD/Spe) | Moves |
|---|---|---|---|---|---|---|---|---|---|---|
| Party 1 | **Pastelito** | Palafin | 88 | Water | Choice Band | Zero to Hero | Jolly | `301/210/159/112/142/289` (`369` Atk in Hero Form) | `0/252/0/2/4/252` | Jet Punch, Wave Crash, Flip Turn, Close Combat |
| Party 2 | **Potato** | Gardevoir | 88 | Psychic | Choice Scarf | Trace | Timid | `245/131/146/307/234/250` (`375` Spe with Scarf) | `4/0/0/252/0/252` | Moonblast, Calm Mind, Psychic, Mystical Fire |
| Party 3 | **Ocra** | Ogerpon-Cornerstone | 98 | Rock | Cornerstone Mask | Sturdy | Jolly | `295/332/200/136/224/343` | `0/252/0/0/4/252` | Ivy Cudgel, Horn Leech, Knock Off, Swords Dance |
| Party 4 | **Tamarind** | Goodra-Hisui | 88 | Steel | Assault Vest | Sap Sipper | Modest | `320/187/208/309/298/137` (`447` SpD with AV) | `248/2/0/252/8/0` | Draco Meteor, Flash Cannon, Flamethrower, Thunderbolt |
| Party 5 | **Mesquite** | Ceruledge | 88 | Fire | Focus Sash | Flash Fire | Jolly | `258/305/173/124/208/260` | `4/245/4/5/0/252` | Bitter Blade, Shadow Sneak, Swords Dance, Shadow Claw |
| Party 6 | **Mudpie** | Clodsire | 88 | Steel | Heavy-Duty Boots | Water Absorb | Careful | `408/164/139/99/289/67` | `248/2/8/0/252/0` | Earthquake, Recover, Toxic, Stealth Rock |
| Box 1 (Alt) | **Spaghetti** | Meowscarada | 88 | Grass | Miracle Seed | Overgrow | Jolly | `261/276/156/158/155/334` | `93/113/68/76/39/121` | Play Rough, Night Slash, Flower Trick, Hone Claws |

---

## 2. Pokemon Luminescent Platinum Active Party

- **Full Roster Table (Party + 52 Box/Daycare Pokemon)**: [Pokemon_Luminescent_Platinum/Roster_Summary.md](Pokemon_Luminescent_Platinum/Roster_Summary.md)
- **Pokemon Showdown Export**: [Pokemon_Luminescent_Platinum/Showdown_Export.txt](Pokemon_Luminescent_Platinum/Showdown_Export.txt)
- **Individual `.pb8` Files**: [Pokemon_Luminescent_Platinum/pokemon_files/](Pokemon_Luminescent_Platinum/pokemon_files/)
- **Raw Switch Saves**: [Pokemon_Luminescent_Platinum/raw_saves/](Pokemon_Luminescent_Platinum/raw_saves/)

| Slot | Nickname | Species | Lv | Held Item | Ability | Nature | Stats (HP/Atk/Def/SpA/SpD/Spe) | EVs (HP/Atk/Def/SpA/SpD/Spe) | Moves |
|---|---|---|---|---|---|---|---|---|---|
| Party 1 | **Cotton Candy** | Tinkaton | 78 | Leftovers | Own Tempo | Jolly | `293/169/146/106/239/195` | `252/0/0/0/240/18` | Play Rough, Gigaton Hammer, Stealth Rock, Knock Off |
| Party 2 | **Tallow** | Ludicolo | 78 | Life Orb | Swift Swim | Modest | `236/124/135/239/185/182` (`364` Spe in Rain) | `0/0/0/252/6/252` | Rain Dance, Ice Beam, Giga Drain, Surf |
| Party 3 | **Melon** | Metagross | 78 | Leftovers | Clear Body | Adamant | `279/316/231/159/170/138` | `252/252/0/0/6/0` | Thunder Punch, Zen Headbutt, Bullet Punch, Hammer Arm |
| Party 4 | **Paneer** | Sneasler | 78 | Life Orb | Technician | Jolly | `236/281/115/81/153/291` | `0/252/3/1/2/252` | Poison Jab, Shadow Claw, Mach Punch, Close Combat |
| Party 5 | **Wasabi** | Chandelure | 78 | Choice Scarf | Flame Body | Modest | `205/102/166/334/170/203` (`304` Spe with Scarf) | `0/0/0/252/6/252` | Shadow Ball, Energy Ball, Overheat, Psychic |
| Party 6 | **Garlic** | Altaria | 78 | Leftovers | Natural Cure | Adamant | `229/239/169/152/192/203` | `6/252/0/0/0/252` | Earthquake, Brave Bird, Dragon Claw, Dragon Dance |

---

## 3. Repository Structure & Refreshing Snapshots

```text
Pokemon-Team-History/
├── README.md
├── export_all_backups.py
├── tools/
│   ├── inject_smogon_mons.py
│   ├── update_ogerpon_and_natures.py
│   └── pkhex_text/
├── Pokemon_Scarlet/
│   ├── Roster_Summary.md
│   ├── Showdown_Export.txt
│   ├── pokemon_files/       # 22 individual .pk9 files (Party + Boxes)
│   └── raw_saves/           # main and backup save files
└── Pokemon_Luminescent_Platinum/
    ├── Roster_Summary.md
    ├── Showdown_Export.txt
    ├── pokemon_files/       # 58 individual .pb8 files (Party + Boxes + Daycare)
    └── raw_saves/           # SaveData.bin and Backup.bin
```

### How to Refresh After Copying New Saves from DBI

1. Copy updated save files from DBI MTP (`7: Saves/Installed games/...`) into `Pokemon_Scarlet/raw_saves/` or `Pokemon_Luminescent_Platinum/raw_saves/`.
2. Run the exporter script to regenerate all `.pk9` / `.pb8` files, Showdown exports, and Markdown roster tables:
   ```bash
   python3 export_all_backups.py
   ```
3. Commit and push the new snapshot:
   ```bash
   git add -A && git commit -m "Update team snapshot" && git push
   ```
