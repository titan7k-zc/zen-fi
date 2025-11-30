# Zen-fi 

Compact, terminal-styled GUI for automated Wi‑Fi password testing (brute-force core).

> **WARNING:** Only use this tool on networks you own or have explicit permission to test. Unauthorized access is illegal.

---

## Features

* Minimal, all-dark (no white padding) GUI built with `tkinter` and `ttk`.
* Uses `nmcli` (NetworkManager) for fast connection attempts.
* Load passwords from `*.npy` files (`password.npy`, `password1.npy`, ...).
* Start from any file in the folder, see progress, abort safely.

---

## Repository layout (expected)

```
zen-fi/
├─ zen_fi.py        # main script (your GUI program)
├─ key/             # user-selected password folder (example)
│  ├─ password.npy
│  ├─ password1.npy
│  └─ ...
└─ README.md        # this file
```

---

## Prerequisites

Install system packages and Python libraries before running.

### Debian / Ubuntu

```bash
sudo apt update
sudo apt install -y network-manager python3 python3-pip python3-tk tk
sudo pip3 install numpy
sudo systemctl enable --now NetworkManager
```

### Arch / Manjaro

```bash
sudo pacman -Syu --needed networkmanager python python-pip tk xorg-xhost
sudo pip install numpy
sudo systemctl enable --now NetworkManager
# If running GUI as root and DISPLAY permission issues occur:
xhost +SI:localuser:root
```

**Note:** `nmcli` must be available in `PATH` and NetworkManager must be running.

---

## Preparing password files

Zen-fi expects `.npy` files named like `password.npy`, `password1.npy`, `password2.npy`, ...
Each `.npy` should contain a 1‑D array of password strings (or any array that flattens to strings).

Quick converter (split `password.txt` into batches of 20):

```python
import numpy as np
from pathlib import Path

pw = Path("password.txt").read_text().splitlines()
batch_size = 20
out = Path("key"); out.mkdir(exist_ok=True)
for i in range(0, len(pw), batch_size):
    arr = np.array(pw[i:i+batch_size], dtype=object)
    name = "password.npy" if i == 0 else f"password{(i//batch_size)}.npy"
    np.save(out/name, arr)
```

Adjust `batch_size` as needed.

---

## Run the app

Run as root (the GUI checks for root to use `nmcli`):

```bash
# if script is named zen_fi.py
sudo python3 zen_fi.py
# or make it executable
chmod +x zen_fi.py
sudo ./zen_fi.py
```

---

## Using the GUI

1. Click **BROWSE** and select the folder containing your `password*.npy` files.
2. Click **SCAN** to detect nearby SSIDs and pick your target from the dropdown.
3. (Optional) Select a starting file under **START FROM**.
4. Click **INITIATE ATTACK** to begin. Click **ABORT** to stop.

Console output shows attempted passwords and final results.

---

## Troubleshooting

* **`nmcli` not found**: install `network-manager` and enable the service.
* **No networks shown**: ensure your Wi‑Fi device is enabled (`rfkill list`) and NetworkManager controls it.
* **GUI display/permission issues (running as root)**: on local X sessions, run `xhost +SI:localuser:root` before launching on Arch or similar.

---

## Security & Legal

This project is provided for education and authorized security testing only. You are solely responsible for how you use it. Misuse may lead to criminal charges.

---

## License & Credits

* Author: titan7k
## Using the GUI

1. Click **BROWSE** and select the folder containing your `password*.npy` files.