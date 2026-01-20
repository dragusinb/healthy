import os
import glob

def clean_pdfs():
    # Synevo
    files = glob.glob("data/raw/synevo/*.pdf")
    for f in files:
        try:
            os.remove(f)
            print(f"Removed {f}")
        except Exception as e:
            print(f"Error removing {f}: {e}")

    # Regina Maria (optional, but good for cleanup)
    files_rm = glob.glob("data/raw/regina_maria/*.pdf")
    for f in files_rm:
        try:
            os.remove(f)
            print(f"Removed {f}")
        except Exception as e:
            print(f"Error removing {f}: {e}")

if __name__ == "__main__":
    clean_pdfs()
