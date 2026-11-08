"""RCS (Autodesk ReCap indexed scan) inspection.

Header field layout (offsets 0x08-0xE0) is NOT independently reverse
engineered by this project. It is re-implemented from the byte-offset
breakdown published by the MIT-licensed `recap-mcp` project (Xuan Tinh,
https://github.com/xuantinhnbs-rgb/recap-mcp, `recap_mcp/rcp.py`), whose
README states it was cross-checked field-by-field against the XML manifest
of Autodesk's own shipped sample project (point count, GUID, registration
matrix all matched) on a real Autodesk ReCap 26.1.1.221 install — see
docs/format-findings.md #11 for the full citation and confidence note.
This project has still never run this against a real .rcs file itself.

The point-record body past the header remains closed and undecoded — both
our own research and recap-mcp's independent, ReCap-verified investigation
agree on this. This module does not and will not guess at it.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path
from typing import Any

MAGIC = b"ADOCT"
HEADER_PEEK_BYTES = 512
MIN_HEADER_BYTES = 0x140  # below this, the fixed-offset fields below don't exist
_GUID_RE = re.compile(rb"\{[0-9A-Fa-f_]{36}\}")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_header_fields(head: bytes) -> dict[str, Any]:
    ver_major, ver_minor = struct.unpack_from("<II", head, 0x08)
    d = struct.unpack_from("<24d", head, 0x10)
    reserved_a, reserved_b, num_points, _pad = struct.unpack_from("<4I", head, 0xD0)
    m = _GUID_RE.search(head, 0xE0)
    return {
        "format_version": f"{ver_major}.{ver_minor}",
        "guid": m.group(0).decode("latin1") if m else None,
        "num_points_claimed": num_points,
        "translation": list(d[0:3]),
        "rotation_euler_deg": list(d[3:6]),
        "scale": list(d[6:9]),
        "unknown_reserved_doubles": list(d[9:12]),
        "octree_bounds": {"min": list(d[12:15]), "max": list(d[15:18])},
        "data_bounds": {"min": list(d[18:21]), "max": list(d[21:24])},
        "reserved_ints": [reserved_a, reserved_b],
        "confidence": "medium — reused from a third-party (recap-mcp) "
        "report of cross-checking these fields against a real ReCap "
        "manifest; not independently verified by this project against "
        "any file, synthetic or real",
        "coordinate_frame_note": "local to this scan; apply "
        "registration.matrix4x4 (from the owning .rcp, not available "
        "here) to express in project coordinates",
    }


def inspect_scan(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(path)

    with p.open("rb") as f:
        header = f.read(HEADER_PEEK_BYTES)

    signature_valid = header.startswith(MAGIC)

    result: dict[str, Any] = {
        "path": str(p),
        "file_size_bytes": p.stat().st_size,
        "sha256": _sha256(p),
        "signature": {
            "expected": MAGIC.decode("ascii"),
            "observed_header_hex": header[: len(MAGIC)].hex(),
            "valid": signature_valid,
            "confidence": "medium-high; cross-corroborated publicly, "
            "including an independent ReCap-verified report (see "
            "docs/format-findings.md #1 and #11)",
        },
        "header_fields": None,
        "body_structure": "unknown — no public specification for the "
        "point-record layout, octree index, or compression scheme exists, "
        "and none has been reverse engineered for this project (see "
        "docs/format-findings.md and docs/limitations.md)",
        "point_data_decoded": False,
        "unknowns": [
            "point record layout",
            "octree/spatial index layout",
            "compression scheme",
            "meaning of unknown_reserved_doubles",
        ],
    }

    if signature_valid and len(header) >= MIN_HEADER_BYTES:
        result["header_fields"] = _parse_header_fields(header)

    return result
