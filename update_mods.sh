#!/usr/bin/env bash
# update_mods.sh <MODS_DIR> <APPID> <PATH_STEAMCMD>
set -euo pipefail
MODS_DIR="$(realpath "$1")"
APPID="$2"
STEAMCMD="$3"

mapfile -t IDS < <(find "$MODS_DIR" -maxdepth 1 -mindepth 1 -type d -printf '%f\n')
[[ ${#IDS[@]} -eq 0 ]] && { echo "Nessuna mod trovata."; exit 0; }

SCRIPT=$(mktemp)
{
  echo "@ShutdownOnFailedCommand 1"
  echo "@NoPromptForPassword 1"
  echo "login anonymous"
  for ID in "${IDS[@]}"; do
    echo "workshop_download_item $APPID $ID"
  done
  echo "quit"
} > "$SCRIPT"

LOG="$("$STEAMCMD" +runscript "$SCRIPT")"
rm -f "$SCRIPT"

echo "$LOG" | grep -Eo 'Downloaded item [0-9]+ to ".+"' |
while read -r line; do
  ID=$(sed -E 's/Downloaded item ([0-9]+).*/\1/' <<< "$line")
  SRC=$(sed -E 's/.*to "(.*)".*/\1/' <<< "$line")
  mv -f "$SRC" "$MODS_DIR/$ID"
done
echo "Aggiornamento completato."
