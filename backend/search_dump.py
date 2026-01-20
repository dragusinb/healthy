def run():
    path = "regina_dump.txt"
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            
        print(f"Total Lines in Dump: {len(lines)}")
        print("--- HEAD (First 20 lines) ---")
        for line in lines[:20]:
            print(line.strip())
        print("--- END HEAD ---")
        
        keywords = ["rezultat", "valoare", "um", "referinta", "homocisteina", "test", "analiza", "interval"]
        print(f"\nScanning for keywords: {keywords}")
        
        count = 0
        for line in lines:
            lower = line.lower()
            if any(k in lower for k in keywords):
                if count < 50: # Limit output
                    print(line.strip())
                    count += 1
        
        if count == 0:
            print("NO KEYWORDS FOUND.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
