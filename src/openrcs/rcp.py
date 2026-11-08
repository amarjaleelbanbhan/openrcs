"""RCP (Autodesk ReCap project) inspection.

RCP is reported to be a ZIP archive containing XML (a direct, first-hand
Autodesk-forum user report, cross-checked against a second source — see
docs/format-findings.md #6). This module only reports structure it can
observe directly: ZIP members, XML tag names/nesting, and file paths that
look like scan references. It does not claim to know what any XML
tag/attribute *means* — no field-name mapping for that is verified.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import xml.parsers.expat as expat
import zipfile
from pathlib import Path
from typing import Any


class _RejectedDoctype(Exception):
    pass

SCAN_REFERENCE_RE = re.compile(r"[^\"'<>\s]+\.(?:rcs|rcc)", re.IGNORECASE)

# RCP is documented as a "lightweight" project file; an XML member larger
# than this is treated as a zip-bomb risk rather than decompressed.
MAX_XML_MEMBER_BYTES = 50 * 1024 * 1024


def _reject_doctype(*_args: Any) -> None:
    raise _RejectedDoctype("DOCTYPE declarations are rejected (XXE / entity-expansion protection)")


def _safe_fromstring(data: bytes) -> ET.Element:
    # RCP files may come from third parties; refuse any DOCTYPE outright so
    # neither external entities (XXE) nor internal entity bombs ("billion
    # laughs") can be defined in the first place. ElementTree.XMLParser no
    # longer exposes the underlying expat handle (stdlib changed this), so
    # this drives expat directly with an ElementTree TreeBuilder as target —
    # the same approach ElementTree itself used to use internally.
    builder = ET.TreeBuilder()
    parser = expat.ParserCreate()
    parser.StartDoctypeDeclHandler = _reject_doctype
    parser.StartElementHandler = builder.start
    parser.EndElementHandler = builder.end
    parser.CharacterDataHandler = builder.data
    parser.Parse(data, True)
    return builder.close()


def _summarize_xml(name: str, data: bytes) -> dict[str, Any]:
    try:
        root = _safe_fromstring(data)
    except (expat.ExpatError, _RejectedDoctype) as exc:
        return {"member": name, "parse_error": str(exc)}
    return {
        "member": name,
        "root_tag": root.tag,
        "child_tags": sorted({child.tag for child in root}),
    }


def inspect_project(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(path)

    if not zipfile.is_zipfile(p):
        return {
            "path": str(p),
            "file_size_bytes": p.stat().st_size,
            "is_zip_container": False,
            "error": "Expected a ZIP/XML container (docs/format-findings.md "
            "#6); this file is not a readable ZIP archive. It may be a "
            "different RCP version, corrupted, or the public report this "
            "tool relies on may not hold for this file.",
        }

    xml_summaries: list[dict[str, Any]] = []
    referenced_scans: set[str] = set()

    with zipfile.ZipFile(p) as zf:
        members = zf.namelist()
        for name in members:
            referenced_scans.update(SCAN_REFERENCE_RE.findall(name))
            if name.lower().endswith(".xml"):
                info = zf.getinfo(name)
                if info.file_size > MAX_XML_MEMBER_BYTES:
                    xml_summaries.append(
                        {"member": name, "skipped": "exceeds size cap "
                         f"({info.file_size} > {MAX_XML_MEMBER_BYTES} bytes); "
                         "not decompressed (zip-bomb precaution)"}
                    )
                    continue
                data = zf.read(name)
                xml_summaries.append(_summarize_xml(name, data))
                referenced_scans.update(
                    SCAN_REFERENCE_RE.findall(data.decode("utf-8", "replace"))
                )

    return {
        "path": str(p),
        "file_size_bytes": p.stat().st_size,
        "is_zip_container": True,
        "members": members,
        "xml_members_parsed": xml_summaries,
        "referenced_scan_like_paths": sorted(referenced_scans),
        "field_semantics_known": False,
        "unknowns": [
            "which XML element/attribute holds registration/transformation "
            "matrices",
            "which XML element/attribute holds clipping regions",
            "which XML element/attribute holds coordinate reference "
            "system info",
            "schema version compatibility rules",
        ],
    }
