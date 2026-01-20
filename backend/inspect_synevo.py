import sys
import os
import json
import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.processors.synevo import SynevoParser

def custom_serializer(obj):
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

if __name__ == "__main__":
    file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/raw/synevo/31033112056.pdf"))
    
    print(f"--- Inspecting {file_path} ---")
    if not os.path.exists(file_path):
        print("ERROR: File not found!")
        sys.exit(1)
        
    parser = SynevoParser()
    result = parser.parse(file_path)
    
    print(json.dumps(result, indent=2, default=custom_serializer))
