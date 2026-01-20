import sys
import os

def run():
    path = sys.argv[1]
    if not os.path.exists(path):
        print("File not found.")
        return
        
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        print("".join(lines[-100:]))

if __name__ == "__main__":
    run()
