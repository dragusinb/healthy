import sys
import os
sys.path.append(os.getcwd())
from backend.processors.synevo import SynevoParser
import json

parser = SynevoParser()
file_path = "data/raw/synevo/12002582294.pdf"

try:
    data = parser.parse(file_path)
    with open("debug_synevo_output.json", "w") as f:
        json.dump(data, f, default=str, indent=2)
    print("Output written to debug_synevo_output.json")
except Exception as e:
    print(e)
