#!/usr/bin/env python3
"""
need to install numpy - "sudo pacman -S python-numpy"
run-"❯ python3 python/WifiBruteie/passwords/txt-to-npy.py password.txt"
view -> use np-view.py 
"""


from pathlib import Path
import sys
import argparse

def parse_args():
    p = argparse.ArgumentParser(description="Split TXT -> multiple .npy files (chunked).")
    p.add_argument("input", help="Input text file (one password per line).")
    p.add_argument("--outdir", "-o", default="key", help="Output directory to store .npy files (default: key).")
    p.add_argument("--chunksize", "-n", type=int, default=3, help="Number of items per .npy file (default: 20).")
    p.add_argument("--basename", "-b", default="password", help="Base name for output files (default: password).")
    return p.parse_args()

def read_lines(path: Path):
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        # strip newline and ignore blank lines
        return [line.strip() for line in f if line.strip()]

def chunk_list(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i+size]

def main():
    args = parse_args()
    txt_path = Path(args.input)
    if not txt_path.exists():
        print(f"[ERROR] Input file not found: {txt_path}")
        sys.exit(1)

    try:
        import numpy as np
    except ModuleNotFoundError:
        print("[ERROR] numpy is not installed for this Python interpreter.")
        print("Install it in your venv or system (Arch):")
        print("  /path/to/venv/bin/pip install numpy")
        print("or (Arch system-wide) run:")
        print("  sudo pacman -S python-numpy")
        sys.exit(1)

    items = read_lines(txt_path)
    if not items:
        print("[WARN] No non-empty lines found in input file.")
        sys.exit(1)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    basename = args.basename
    chunk_size = max(1, int(args.chunksize))

    count = 0
    for idx, chunk in enumerate(chunk_list(items, chunk_size)):
        # filename: basename.npy for idx==0, basename{idx}.npy for idx>0
        fname = f"{basename}.npy" if idx == 0 else f"{basename}{idx}.npy"
        out_path = outdir / fname

        arr = np.array(chunk, dtype=object)
        np.save(out_path, arr)
        count += 1
        print(f"Saved chunk {idx} -> {out_path} ({len(chunk)} items)")

    print(f"Done. Created {count} .npy file(s) in: {outdir.resolve()}")

if __name__ == "__main__":
    main()
