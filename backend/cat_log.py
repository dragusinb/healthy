import sys
import os

files = ["debug_synevo_log.txt", "debug_table_log.txt"]

for fname in files:
    if os.path.exists(fname):
        print(f"--- {fname} ---")
        try:
            with open(fname, "r", encoding="utf-16") as f:
                print(f.read())
        except UnicodeError:
            try:
                with open(fname, "r", encoding="utf-8") as f:
                    print(f.read())
            except Exception as e:
                print(f"Error reading {fname}: {e}")
