import sys

def run():
    path = sys.argv[1]
    keyword = sys.argv[2]
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if keyword in line:
                print(line.strip())

if __name__ == "__main__":
    run()
