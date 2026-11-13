# Pokemon Team History

Archive of Nintendo Switch Pokemon save files, individual `.pk9` / `.pb8` Pokemon files, and Showdown exports.

## Games

| Game | Current Party | Roster | Showdown | Files |
|---|---|---|---|---|
| **Pokemon Scarlet** *(Ultimate Scarlet)* | Palafin, Gardevoir, Meowscarada, Goodra-H, Ceruledge, Clodsire | [Roster](Pokemon_Scarlet/Roster_Summary.md) | [Showdown](Pokemon_Scarlet/Showdown_Export.txt) | [.pk9](Pokemon_Scarlet/pokemon_files/) · [Saves](Pokemon_Scarlet/raw_saves/) |
| **Imagine Killing Dragons** *(Pokemon Scarlet - Dragon Elite Four Trial Squad)* | Golurk, Flygon, Exeggutor-Alola, Araquanid, Blissey, Abomasnow | [Roster](Imagine_Killing_Dragons/Roster_Summary.md) | [Showdown](Imagine_Killing_Dragons/Showdown_Export.txt) | [.pk9](Imagine_Killing_Dragons/pokemon_files/) |
| **Pokemon Luminescent Platinum** | Tinkaton, Ludicolo, Metagross, Sneasler, Chandelure, Altaria | [Roster](Pokemon_Luminescent_Platinum/Roster_Summary.md) | [Showdown](Pokemon_Luminescent_Platinum/Showdown_Export.txt) | [.pb8](Pokemon_Luminescent_Platinum/pokemon_files/) · [Saves](Pokemon_Luminescent_Platinum/raw_saves/) |

## Quick Update

After copying new save files into `<Game>/raw_saves/`:

```bash
go run .
git add -A && git commit -m "Update team snapshot" && git push
```
