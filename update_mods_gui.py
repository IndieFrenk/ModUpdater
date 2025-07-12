#!/usr/bin/env python3
"""
update_mods_gui.py – interfaccia grafica per aggiornare le mod Workshop
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import pathlib
import sys
import os
import tempfile
import subprocess
import re

# Regex per rilevare i download
DL_RE = re.compile(r'Downloaded item (\d+) to "(.+?)"')

def build_runscript(mod_ids, appid) -> str:
    """Crea script temporaneo per SteamCMD"""
    fd, path = tempfile.mkstemp(suffix='.txt', text=True)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write('@ShutdownOnFailedCommand 1\n@NoPromptForPassword 1\n')
        f.write('login anonymous\n')
        for mid in mod_ids:
            f.write(f'workshop_download_item {appid} {mid}\n')
        f.write('quit\n')
    return path

def move_or_link(src, dest, as_link: bool):
    """Sposta o collega una cartella"""
    import shutil
    if dest.exists():
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        else:
            shutil.rmtree(dest)
    if as_link:
        dest.symlink_to(src, target_is_directory=True)
    else:
        shutil.move(src, dest)

class ModUpdaterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mod Updater v1.0")
        self.root.geometry("700x600")
        self.root.resizable(True, True)

        # Variabili
        self.steamcmd_path = tk.StringVar()
        self.mods_dir_path = tk.StringVar()
        self.appid_var = tk.StringVar(value="294100")  # Default RimWorld
        self.link_var = tk.BooleanVar()

        # Queue per comunicare tra thread
        self.log_queue = queue.Queue()

        self.setup_ui()
        self.check_log_queue()

    def setup_ui(self):
        # Frame principale
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configurazione griglia
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Titolo
        title_label = ttk.Label(main_frame, text="RimWorld Mod Updater", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # SteamCMD Path
        ttk.Label(main_frame, text="SteamCMD:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.steamcmd_path, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Sfoglia", command=self.browse_steamcmd).grid(row=1, column=2, padx=5)

        # Mods Directory
        ttk.Label(main_frame, text="Cartella Mod:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.mods_dir_path, width=50).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(main_frame, text="Sfoglia", command=self.browse_mods_dir).grid(row=2, column=2, padx=5)

        # AppID
        ttk.Label(main_frame, text="AppID Steam:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.appid_var, width=15).grid(row=3, column=1, sticky=tk.W, padx=5)

        # Link checkbox
        ttk.Checkbutton(main_frame, text="Crea collegamenti simbolici", 
                       variable=self.link_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=10)

        # Pulsante aggiorna
        self.update_button = ttk.Button(main_frame, text="🔄 Aggiorna Mod", 
                                       command=self.start_update, style='Accent.TButton')
        self.update_button.grid(row=5, column=0, columnspan=3, pady=15)

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        # Log area
        ttk.Label(main_frame, text="Log:").grid(row=7, column=0, sticky=tk.W, pady=(10, 0))
        self.log_text = scrolledtext.ScrolledText(main_frame, height=18, width=80, 
                                                 font=('Consolas', 9))
        self.log_text.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Pulsante cancella log
        ttk.Button(main_frame, text="Cancella Log", 
                  command=self.clear_log).grid(row=9, column=0, sticky=tk.W, pady=5)

        # Configura ridimensionamento
        main_frame.rowconfigure(8, weight=1)

    def clear_log(self):
        """Cancella il contenuto del log"""
        self.log_text.delete(1.0, tk.END)

    def browse_steamcmd(self):
        filename = filedialog.askopenfilename(
            title="Seleziona SteamCMD",
            filetypes=[("Eseguibili", "*.exe"), ("Tutti i file", "*.*")]
        )
        if filename:
            self.steamcmd_path.set(filename)

    def browse_mods_dir(self):
        dirname = filedialog.askdirectory(
            title="Seleziona cartella Mod"
        )
        if dirname:
            self.mods_dir_path.set(dirname)

    def log_message(self, message):
        """Aggiunge messaggio al log"""
        self.log_queue.put(message)

    def check_log_queue(self):
        """Controlla la queue per nuovi messaggi di log"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message + '\n')
                self.log_text.see(tk.END)
                self.root.update_idletasks()
        except queue.Empty:
            pass

        # Riprogramma il controllo
        self.root.after(100, self.check_log_queue)

    def validate_inputs(self):
        """Valida gli input dell'utente"""
        if not self.steamcmd_path.get():
            messagebox.showerror("Errore", "Seleziona il percorso di SteamCMD")
            return False

        if not self.mods_dir_path.get():
            messagebox.showerror("Errore", "Seleziona la cartella delle mod")
            return False

        if not pathlib.Path(self.steamcmd_path.get()).exists():
            messagebox.showerror("Errore", "SteamCMD non trovato nel percorso specificato")
            return False

        if not pathlib.Path(self.mods_dir_path.get()).exists():
            messagebox.showerror("Errore", "Cartella mod non trovata")
            return False

        try:
            int(self.appid_var.get())
        except ValueError:
            messagebox.showerror("Errore", "AppID deve essere un numero")
            return False

        return True

    def start_update(self):
        """Avvia l'aggiornamento in un thread separato"""
        if not self.validate_inputs():
            return

        # Disabilita il pulsante e avvia progress bar
        self.update_button.config(state='disabled')
        self.progress.start()

        # Avvia thread per l'aggiornamento
        thread = threading.Thread(target=self.update_mods_thread)
        thread.daemon = True
        thread.start()

    def update_mods_thread(self):
        """Esegue l'aggiornamento delle mod in un thread separato"""
        try:
            mods_dir = pathlib.Path(self.mods_dir_path.get()).resolve()
            appid = int(self.appid_var.get())

            # Trova mod con ID numerici
            ids = [d.name for d in mods_dir.iterdir()
                   if d.is_dir() and d.name.isdigit()]

            if not ids:
                self.log_message('❌ Nessuna mod con ID valido trovata in ' + str(mods_dir))
                return

            self.log_message(f'📦 Trovate {len(ids)} mod da aggiornare')
            self.log_message(f'📁 Cartella mod: {mods_dir}')
            self.log_message(f'⚙️  SteamCMD: {self.steamcmd_path.get()}')
            self.log_message(f'🎮 AppID: {appid}')
            self.log_message('🚀 Iniziando aggiornamento...\n')

            # Crea script e esegui SteamCMD
            script = build_runscript(ids, appid)
            self.log_message(f"📄 Script temporaneo creato: {script}")

            # Esegui SteamCMD
            log = self.run_steamcmd_with_logging(self.steamcmd_path.get(), script)

            # Processa risultati
            matches = list(DL_RE.finditer(log))
            self.log_message(f"\n📊 Trovate {len(matches)} mod scaricate")

            if not matches:
                self.log_message('⚠️  Nessun download rilevato')
            else:
                # Mostra cartella download Steam
                steam_download_dir = None
                for match in matches:
                    mid, src_path = match.groups()
                    src = pathlib.Path(src_path)
                    if steam_download_dir is None:
                        steam_download_dir = src.parent
                    self.log_message(f'✅ Mod {mid} scaricata')

                if steam_download_dir:
                    self.log_message(f'\n📁 Cartella download Steam: {steam_download_dir}')

            # Sposta/collega mod
            success_count = 0
            for i, match in enumerate(matches, 1):
                mid, src_path = match.groups()
                src = pathlib.Path(src_path)
                dest = mods_dir / mid
                self.log_message(f'[{i}/{len(matches)}] Processando mod {mid}')

                try:
                    move_or_link(src, dest, self.link_var.get())
                    self.log_message(f'  ✅ Aggiornata mod {mid}')
                    success_count += 1
                except Exception as e:
                    self.log_message(f'  ❌ Errore mod {mid}: {e}')

            # Pulizia
            if os.path.exists(script):
                os.remove(script)

            self.log_message(f'\n🎉 Aggiornamento completato!')
            self.log_message(f'✅ Mod aggiornate: {success_count}/{len(matches)}')
            self.log_message('✨ Processo terminato.')

        except Exception as e:
            self.log_message(f'❌ Errore durante l\'aggiornamento: {e}')
            import traceback
            self.log_message(traceback.format_exc())

        finally:
            # Riabilita UI
            self.root.after(0, self.finish_update)

    def run_steamcmd_with_logging(self, cmd_path, script_path):
        """Esegue SteamCMD con logging personalizzato"""
        self.log_message(f"⚙️  Eseguendo SteamCMD...")

        res = subprocess.run([cmd_path, '+runscript', script_path],
                           text=True, capture_output=True)

        if res.stdout:
            self.log_message("=== OUTPUT STEAMCMD ===")
            self.log_message(res.stdout)
            self.log_message("=== FINE OUTPUT ===")

        if res.stderr:
            self.log_message("=== ERRORI STEAMCMD ===")
            self.log_message(res.stderr)
            self.log_message("=== FINE ERRORI ===")

        if res.returncode != 0:
            self.log_message(f"❌ SteamCMD terminato con codice: {res.returncode}")
            raise Exception(f"SteamCMD failed with code {res.returncode}")

        return res.stdout

    def finish_update(self):
        """Chiamata quando l'aggiornamento è terminato"""
        self.progress.stop()
        self.update_button.config(state='normal')

def main():
    root = tk.Tk()
    try:
        # Prova a impostare uno stile moderno
        root.tk.call('source', 'azure.tcl')
        root.tk.call('set_theme', 'light')
    except:
        pass  # Fallback al tema predefinito
    
    app = ModUpdaterGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()