from backend.processors.regina_maria import ReginaMariaParser
import json
import datetime

def json_serial(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

p = ReginaMariaParser()
path = "data/raw/regina_maria/rezultat_33862887_2025.12.08 12.07.56.pdf"

try:
    res = p.parse(path)
    print(json.dumps(res, default=json_serial, indent=2))
except Exception:
    import traceback
    with open("data/traceback.log", "w", encoding="utf-8") as f:
        traceback.print_exc(file=f)
