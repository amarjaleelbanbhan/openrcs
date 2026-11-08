# OpenRCS — Format Findings & Evidence Ledger

## Methodology and a critical caveat

**No authorized Autodesk ReCap installation and no `.rcs`/`.rcp` sample files
were available on the machine this investigation ran on.** This means:

- REA (the reverse-engineering MCP tool used for this project) was verified
  to be connected and functional (see below), but it was never pointed at a
  ReCap binary or data file, because none existed to point it at. **No REA
  evidence exists for RCS/RCP in this repo. Every claim below is sourced
  from public third-party documentation, not from REA analysis or
  decompilation.**
- Autodesk's License and Services Agreement prohibits decompiling,
  disassembling, or otherwise reverse engineering Autodesk software, and
  (in its current Acceptable Use Policy language) extends that prohibition
  to studying "data structures or other externals" — without a specific
  applicable-law carve-out. No such legal clearance has been obtained for
  this project. **The Autodesk ReCap executable has not been decompiled or
  disassembled, and will not be, absent that clearance.**
- REA's own decompiler backends (Ghidra, IDA, Hopper, Kuna) are also not
  configured in this environment (`GHIDRA_INSTALL_DIR` unset, no IDA/Hopper/
  Kuna registration) — a second, independent reason no binary decompilation
  happened here, on top of the legal one.

Everything below is therefore **desk research**, cross-checked across
multiple independent public sources, not original reverse engineering of
Autodesk's code. Confidence levels reflect that.

## REA connectivity check (for the record)

REA MCP was verified live in this session:
- `open_binary` on a local, unrelated, non-Autodesk executable
  (`node.exe`, SHA-256 `1c63f1417e2e26d83ca9a9ec1d548524ab1305bc7209d90ebca56257ff0d84ed`)
  succeeded — format `pe`, architecture `x86_64`.
- `binary_overview` (which needs a decompiler provider) failed with
  `provider_unavailable`: Ghidra not configured, Hopper unsupported on
  win32, IDA/Kuna not configured.
- Container-level tools that don't need a decompiler (e.g.
  `inspect_pe_imports`) work fine.
- Session was closed cleanly with `close_binary`.

This confirms the MCP pipe and file-structure tooling work; it does not
constitute, and is not presented as, analysis of any Autodesk artifact.

## Evidence ledger

| # | Finding | Value | Confidence | Sources | Verified against a real file? |
|---|---------|-------|------------|---------|-------------------------------|
| 1 | RCS file signature | First 5 bytes are ASCII `ADOCT` (hex `41 44 4F 43 54`), regardless of extension | Medium-high — 3 independent sources agree, including a shipped open-source detector | filext.com RCS page; [openlidarviewer PR #1317](https://github.com/Aurtechmx/openlidarviewer/pull/1317) (`src/io/recognisedUnsupported.ts`, `RCS_MAGIC = 'ADOCT'`); cadinterop.com | **No.** Not checked against an authentic Autodesk-produced file — none available. |
| 2 | RCS typical size | 64 MB – 3 GB | Low-medium (anecdotal) | filext.com | No |
| 3 | RCS is a closed, undocumented binary container | No public specification exists | High (consistent across every source checked, including Autodesk's own ecosystem partners) | cadinterop.com; archiveteam/justsolve wiki (via search summary); general consensus | N/A — this is a statement of absence, not a structural claim |
| 4 | RCS claimed logical contents | XYZ (double precision), RGB (8-bit/channel), intensity, computed normals | Low — single source, no primary confirmation, no byte offsets given | cadinterop.com | No |
| 5 | RCS internal layout (octree index, point-record layout, compression) | **Unknown** | N/A | — | Not available anywhere publicly; not attempted here (see legal/technical blockers above) |
| 6 | RCP container format | ZIP archive containing at least one XML file plus other members | Medium-high — direct, first-hand user report ("basically just a zip file containing an xml file") cross-checked against a second file-reference site describing the same thing | Autodesk Community forum thread "Read RCP file"; filext/fileinfo-style RCP description | No |
| 7 | RCP claimed logical contents | Relative paths to `.rcs` files, registration/transformation matrices, clipping regions, display preferences | Low — single source (cadinterop.com), no element/attribute names or schema given | cadinterop.com | No |
| 8 | Related project-folder files | `.rcc` = compressed structured scan data (terrestrial/tripod scans), lives in project's `Support` folder | Medium — independently described by a file-info reference site | fileinfo.com `.rcc` page | No |
| 9 | Related project-folder files | `.rch` (range-image header), `.llt` (range-image preview), `.diff` (unmapped raw points) | **Low / unconfirmed** — this came from a search-engine summary of an Autodesk forum thread that returned HTTP 403 when fetched directly; the primary source was never actually read | (unverified — forum thread blocked, treat as rumor until re-checked) | No |
| 10 | Backward compatibility | Projects indexed in a newer ReCap Pro version may fail to open in an older one | Medium (vendor-adjacent reseller site, consistent with normal Autodesk versioning behavior) | cadinterop.com | No |
| 11 | RCS fixed-offset header fields: format version (`0x08`, 2×u32), translation/rotation/scale/octree-bounds/data-bounds (`0x10`, 24×f64), reserved ints + point count (`0xD0`, 4×u32), a GUID (regex search from `0xE0`) | Medium — a third party (not us) reports cross-checking these fields against the XML manifest on a real Autodesk ReCap 26.1.1.221 install: point count, GUID, and registration matrix all matched. We did not run this ourselves against any file. | [recap-mcp](https://github.com/xuantinhnbs-rgb/recap-mcp) (MIT, Xuân Tình), `recap_mcp/rcp.py::read_rcs_header`, audited 2026-11-09 | No — reused from a third party's reported verification, not verified by us |
| 12 | RCS point-record body is a closed octree; no project (ours or recap-mcp's) has decoded it | High — two independent investigations (ours, desk research only; recap-mcp's, with an actual ReCap install) reach the same conclusion | recap-mcp README §"Three dead ends, already explored"; this project's own findings 3 & 5 | N/A — agreement on an absence, not a structural claim |

## recap-mcp audit (2026-11-09)

[recap-mcp](https://github.com/xuantinhnbs-rgb/recap-mcp) is an existing MIT-licensed,
actively-developed MCP server (Python, Windows, ~4450 lines incl. tests, CI green,
3 commits since 2026-09-19, 1 star/0 forks — young, single-author, no community
issues yet beyond dependabot PRs) that already does most of what a general RCS/RCP
inspector would offer, verified against a real Autodesk ReCap install and its
bundled sample project (`C:\ProgramData\Autodesk\Autodesk ReCap\Sample\...`):

- Full `.rcp` manifest parsing (scans, registration matrices + quality, measurements,
  regions, bounds, coordinate system) — pure Python (`zipfile` + `ElementTree`), no
  ReCap runtime dependency despite the README implying Windows/ReCap are required.
- `.rcs` **header** parsing (not the point body) — the source of finding 11 above.
- Headless processing via `decap.exe` (import/decimate/reproject) — legitimate use
  of Autodesk's own shipped CLI tool via its documented `--help` flags, not
  decompilation.
- Rich LAS/LAZ analysis (cross-sections, plane fitting, BIM-mesh deviation with a
  stated correctness certificate, epoch comparison, elevation grids) — the
  Scan-to-BIM workflow this whole category of tooling is actually for.
- Independently confirms: no COM/automation API exists for ReCap, the SDK DLL
  exports are unwrapped C++ mangled symbols, and the `.rcs` point body is a closed
  `ADOCT` octree that cannot be decoded — i.e. it hit the exact same dead end we
  did, but from inside a real installation instead of desk research.

**Conclusion:** the "read an `.rcp`/`.rcs`, extract registration/metadata, compare
against BIM" product is already solved, well, by an MIT-licensed project we can
legally reuse findings from. See `README.md` for what this means for OpenRCS's
direction.

## What this means for OpenRCS today

- **Signature detection (finding 1)** and now **header-field decoding
  (finding 11)** are implemented in `openrcs inspect-scan`.
- **RCP-as-ZIP (finding 6) is implemented** in `openrcs inspect-project`:
  OpenRCS opens the file as a ZIP, lists members, and parses any XML member
  structurally (tag names and nesting only — it does **not** claim to know
  what any tag or attribute *means*, since finding 7 is unverified).
- **Findings 4, 5, 7, 9 are not implemented** — there is no verified point
  layout, no verified XML schema, and no verified auxiliary-file semantics.
  Any code claiming to decode these would be fabricating a format spec.
  `openrcs convert` says so explicitly instead of guessing.
- Point-body decoding (finding 12) will not be attempted: two independent
  investigations agree it isn't currently feasible without Autodesk's SDK.
- If real `.rcs`/`.rcp` samples become available, the next step is to verify
  findings 1 and 11 ourselves instead of relying on a third party's report.
