#!/usr/bin/env python3

import argparse, os, re, shutil, subprocess, sys, tempfile, pathlib

DL_RE = re.compile(r'Downloaded item (\d+) to "(.+?)"')

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument('--mods-dir', required=True, help='Cartella Mods del gioco')
    p.add_argument('--steamcmd', required=True, help='Percorso steamcmd/steamcmd.exe')
    p.add_argument('--appid', required=True, type=int, help='AppID Steam del gioco')
    p.add_argument('--link', action='store_true',
                   help='Crea un symlink invece di copiare')
    args = p.parse_args()
    
    # Validazione percorsi
    if not pathlib.Path(args.mods_dir).exists():
        print(f"Errore: cartella mod non trovata: {args.mods_dir}", file=sys.stderr)
        sys.exit(1)
    if not pathlib.Path(args.steamcmd).exists():
        print(f"Errore: SteamCMD non trovato: {args.steamcmd}", file=sys.stderr)
        sys.exit(1)
    
    return args
def run_steamcmd(cmd_path, script_path) -> str:
    print(f"Eseguendo SteamCMD: {cmd_path}")
    print(f"Script: {script_path}")
    
    res = subprocess.run([cmd_path, '+runscript', script_path],
                         text=True, capture_output=True)
    
    # Mostra output in tempo reale
    if res.stdout:
        print("=== OUTPUT STEAMCMD ===")
        print(res.stdout)
        print("=== FINE OUTPUT ===")
    
    if res.stderr:
        print("=== ERRORI STEAMCMD ===")
        print(res.stderr)
        print("=== FINE ERRORI ===")
    
    if res.returncode != 0:
        print(f"SteamCMD terminato con codice: {res.returncode}", file=sys.stderr)
        sys.exit(res.returncode)
    
    return res.stdout
def build_runscript(mod_ids, appid) -> str:
    fd, path = tempfile.mkstemp(suffix='.txt', text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write('@ShutdownOnFailedCommand 1\n@NoPromptForPassword 1\n')
        f.write('login anonymous\n')
        for mid in mod_ids:
            f.write(f'workshop_download_item {appid} {mid}\n')
        f.write('quit\n')
    return path

def move_or_link(src, dest, as_link: bool):
    if dest.exists():
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        else:
            shutil.rmtree(dest)
    if as_link:
        dest.symlink_to(src, target_is_directory=True)
    else:
        shutil.move(src, dest)

def main():
        args = parse_args()
        mods_dir = pathlib.Path(args.mods_dir).resolve()
    
        # Filtra solo ID numerici validi
        ids = [d.name for d in mods_dir.iterdir()
               if d.is_dir() and d.name.isdigit()]
    
        if not ids:
            print('Nessuna mod con ID valido trovata in', mods_dir)
            return
    
        print(f'Trovate {len(ids)} mod da aggiornare: {", ".join(ids)}')
        print(f'Cartella mod: {mods_dir}')
        print(f'SteamCMD: {args.steamcmd}')
        print(f'AppID: {args.appid}')
        print('Iniziando aggiornamento...\n')
    
        try:
            script = build_runscript(ids, args.appid)
            print(f"Script temporaneo creato: {script}")
    
            # Mostra contenuto script per debug
            with open(script, 'r', encoding='utf-8') as f:
                print("=== CONTENUTO SCRIPT ===")
                print(f.read())
                print("=== FINE SCRIPT ===\n")
    
            log = run_steamcmd(args.steamcmd, script)
    
            matches = list(DL_RE.finditer(log))
            print(f"\nTrovate {len(matches)} mod scaricate nell'output")
    
            if not matches:
                print('Nessun download rilevato nell\'output SteamCMD')
                print('Output SteamCMD completo:')
                print(log)
            else:
                # Mostra la cartella di download di Steam
                steam_download_dir = None
                for match in matches:
                    mid, src_path = match.groups()
                    src = pathlib.Path(src_path)
                    if steam_download_dir is None:
                        steam_download_dir = src.parent
                    print(f'Mod {mid} scaricata in: {src}')
    
                if steam_download_dir:
                    print(f'\n📁 Cartella download Steam: {steam_download_dir}')
    
            for i, match in enumerate(matches, 1):
                mid, src_path = match.groups()
                src = pathlib.Path(src_path)
                dest = mods_dir / mid
                print(f'[{i}/{len(matches)}] Processando mod {mid}')
                print(f'  Sorgente: {src}')
                print(f'  Destinazione: {dest}')
    
                try:
                    move_or_link(src, dest, args.link)
                    print(f'  ✓ Aggiornata mod {mid}')
                except Exception as e:
                    print(f'  ✗ Errore mod {mid}: {e}')
    
        except Exception as e:
            print(f'Errore durante l\'aggiornamento: {e}', file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)
        finally:
            if 'script' in locals():
                print(f"Eliminando script temporaneo: {script}")
                os.remove(script)
    
        print(f'\n✅ Aggiornamento completato per {len(matches)} mod.')
        print('Processo terminato.')
if __name__ == '__main__':
    main()
