--There's a known bug that doesnt let the updater copy the mods in the game's mod folder, because it doesnt have rights to write on another disk, for now, until i fix it i suggest to run it in the same disk as the mod folder

﻿# Steam Workshop Mod Updater

Aggiorna o scarica in blocco tutte le mod di Steam Workshop presenti nella cartella **Mods** (es. RimWorld, Project Zomboid, Factorio etc.) usando **SteamCMD** ed un semplice script **Python** con **interfaccia grafica**.

---

## Funzionalità

* **Interfaccia grafica intuitiva** con pulsanti per selezionare cartelle e file
* Legge automaticamente gli *ID* delle mod dalle sottocartelle numeriche all'interno della directory *Mods*
* Genera un file `runscript` per SteamCMD con tutti i comandi `workshop_download_item <AppID> <ModID>`
* Avvia una sola sessione SteamCMD ("`login anonymous`"), scarica/aggiorna le mod e chiude
* Sposta le cartelle delle mod scaricate nella directory *Mods* **oppure** crea collegamenti simbolici/junction per risparmiare spazio
* **Log in tempo reale** con tutti i dettagli del processo di aggiornamento
* Ritorno su shell con codice ≠ 0 se qualche download fallisce (`@ShutdownOnFailedCommand 1`)

---

## Requisiti

| Strumento | Versione minima | Note |
|-----------|-----------------|------|
| **Python** | 3.8 | Per l'interfaccia grafica |
| **SteamCMD** | ultima (autoupdate interno) | [Installazione Valve](https://developer.valvesoftware.com/wiki/SteamCMD) |
| **Windows 10/11** o Linux/macOS | — | Su Windows serve Developer Mode *oppure* prompt Administrator per creare symlink |

---

## Installazione

```powershell
# 1. Scarica SteamCMD e scompattalo (es. D:\steamcmd)
# 2. Clona o scarica questo repo
# 3. (Windows) Installa Python e aggiungilo al PATH
```
Linux/macOS:
sudo apt install steamcmd python3 python3-pip python3-tkinter   # Debian/Ubuntu


Uso con Interfaccia Grafica
Versione Eseguibile (Windows)
Scarica ModUpdater.exe dalla cartella dist/
Avvia l'applicazione con doppio click
Configura i parametri nell'interfaccia:
SteamCMD: Clicca "Sfoglia" e seleziona steamcmd.exe
Cartella Mod: Clicca "Sfoglia" e seleziona la cartella Mods del gioco
AppID Steam: Inserisci l'ID del gioco (es. 294100 per RimWorld)
Collegamenti simbolici: Spunta per creare symlink invece di copiare
Clicca "🔄 Aggiorna Mod"
Monitora il progresso nell'area Log
Versione Python
python update_mods_gui.py

**Parametri da configurare nell'interfaccia:**

| Campo | Descrizione | Esempio |
|-------|-------------|---------|
| **SteamCMD** | Percorso completo a `steamcmd.exe` | `D:\steamcmd\steamcmd.exe` |
| **Cartella Mod** | Directory *Mods* del gioco | `C:\GOG Games\RimWorld\Mods` |
| **AppID Steam** | *AppID* Steam del gioco | `294100` (RimWorld) |
| **Collegamenti simbolici** | Crea symlink invece di copiare | ☑️ (opzionale) |



Parametri da configurare nell'interfaccia:
Uso a Riga di Comando (Avanzato)
Windows
python update_mods.py ^
  --mods-dir "C:\GOG Games\RimWorld\Mods" ^
  --steamcmd  "D:\steamcmd\steamcmd.exe" ^
  --appid 294100 ^
  --link            # facoltativo (symlink)

Linux/macOS
python3 update_mods.py \
  --mods-dir "/home/user/GOG/RimWorld/Mods" \
  --steamcmd  "/opt/steamcmd/steamcmd.sh" \
  --appid 294100 \
  --link

Caratteristiche Interfaccia Grafica
Selezione file/cartelle: Pulsanti "Sfoglia" aprono finestre di dialogo
Validazione input: Controlla che i percorsi esistano prima di procedere
Progress bar: Mostra che il processo è in corso
Log dettagliato: Area di testo scorrevole con tutti i messaggi
Threading: L'interfaccia non si blocca durante l'aggiornamento
Emoji informativi: Log colorato con icone per facilitare la lettura
