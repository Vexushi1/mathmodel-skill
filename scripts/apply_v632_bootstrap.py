#!/usr/bin/env python3
from pathlib import Path
import base64, re, zlib
root = Path(__file__).resolve().parent
payload = "".join((root / ".v632" / f"part{i:02d}.txt").read_text(encoding="ascii").strip() for i in range(8))
source = zlib.decompress(base64.b64decode(payload)).decode("utf-8")
source = re.sub(
    r'\n    refresh = ROOT / "\.github/workflows/refresh-generated\.yml".*?refresh\.write_text\(text, encoding="utf-8", newline="\\n"\)\n',
    "\n",
    source,
    flags=re.S,
)
exec(compile(source, "apply_v632_delivery_closure.py", "exec"))
