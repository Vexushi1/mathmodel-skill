"""Export one frozen user turn. Example: python tests/v11_web_app_packet.py --case intake --turn 1 --output intake.zip"""
from __future__ import annotations

import argparse
import base64
import hashlib
from io import BytesIO
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, ZipInfo

import yaml

FIXTURES = Path(__file__).resolve().parent / "fixtures"
CATALOG = FIXTURES / "v11_web_app_cases.yaml"


def relative_path(value: str) -> str:
    path = PurePosixPath(value)
    if (not path.parts or path.is_absolute() or str(path) != value
            or ".." in path.parts or "\\" in value or ":" in value):
        raise ValueError(f"Expected a relative POSIX file path: {value!r}")
    return value


def check_digest(data: bytes, expected: str) -> bytes:
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError("Frozen material does not match its registered SHA-256")
    return data


def material_files(material: dict) -> dict[str, bytes]:
    if "archive" in material:
        path = FIXTURES / relative_path(material["archive"])
        raw = check_digest(path.read_bytes(), material["sha256"])
        with ZipFile(BytesIO(raw)) as archive:
            names = archive.namelist()
            omitted = set(material.get("omit", []))
            if len(set(names)) != len(names) or not omitted.issubset(names):
                raise ValueError("Duplicate or missing fixture archive member")
            return {relative_path(name): archive.read(name) for name in names if name not in omitted}

    name = relative_path(material["path"])
    if "file" in material:
        source = FIXTURES / relative_path(material["file"])
        return {name: check_digest(source.read_bytes(), material["sha256"])}
    if "text" in material:
        return {name: material["text"].encode("utf-8")}
    encoded = "".join(material["base64"].split())
    return {name: check_digest(base64.b64decode(encoded, validate=True), material["sha256"])}


def packet_files(case_id: str, turn: int) -> dict[str, bytes]:
    catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    case = next((c for c in catalog["cases"] if c["id"] == case_id), None)
    if case is None or not 1 <= turn <= len(case["turns"]):
        raise ValueError(f"Unknown case/turn: {case_id!r}/{turn}")
    current = case["turns"][turn - 1]
    files = {"用户请求.txt": (current["prompt"] + "\n").encode("utf-8")}
    for source in current["materials"]:
        additions = material_files(catalog["materials"][source])
        if files.keys() & additions.keys():
            raise ValueError(f"Conflicting packet file from {source}")
        files.update(additions)
    return files


def export_packet(case_id: str, turn: int, output: Path) -> str:
    files = packet_files(case_id, turn)
    buffer = BytesIO()
    with ZipFile(buffer, "w") as archive:
        for name, data in sorted(files.items()):
            # Identical fixture bytes on Windows and POSIX, independent of wall clock and zlib.
            info = ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.create_system = 0
            info.external_attr = 0x20
            archive.writestr(info, data)
    raw = buffer.getvalue()
    with output.open("xb") as target:
        target.write(raw)
    return hashlib.sha256(raw).hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True)
    parser.add_argument("--turn", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(export_packet(args.case, args.turn, args.output))
    except (OSError, ValueError) as error:
        parser.exit(2, f"{error}\n")
