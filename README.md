# OpenRCS

An independent, open-source command-line tool for inspecting Autodesk
ReCap `.rcs` (scan) and `.rcp` (project) files.

**This is not endorsed by, affiliated with, or associated with Autodesk.**
"Autodesk" and "ReCap" are trademarks of their respective owner; this
project's name only refers to the file formats it inspects.

## What this actually does today

- `openrcs inspect-scan FILE.rcs` — checks the 5-byte file signature
  (`ADOCT`), and if present, decodes the fixed-offset header fields (format
  version, point count, GUID, translation/rotation/scale, octree and data
  bounds). The header layout is reused from a third party's (recap-mcp)
  report of cross-checking it against a real ReCap install — see
  `docs/format-findings.md` #11 for the citation and confidence level. The
  point-record body past the header is not decoded by anyone, anywhere, as
  far as either project has found.
- `openrcs inspect-project FILE.rcp` — opens the file as a ZIP archive,
  lists its members, and structurally parses any XML member (tag names and
  nesting only — not their meaning), and lists any `.rcs`/`.rcc`-looking
  path strings it finds.
- `openrcs validate FILE.rcs|.rcp` — reports structural validity (signature
  or ZIP-container check) only. It is explicitly **not** a full validator.
- `openrcs convert ...` — **refuses to run**, on purpose. See below.

## What this does NOT do (read this before filing an issue)

- **It cannot decode point-cloud data.** No public specification exists
  for RCS's internal point-record layout, spatial index, or compression.
  Fabricating a reader against guessed offsets would silently produce
  wrong coordinates, which is worse than refusing. `openrcs convert`
  prints exactly this and exits non-zero instead.
- **It has not reverse engineered the ReCap binary.** Autodesk's License
  and Services Agreement prohibits decompiling/disassembling Autodesk
  software (and, in current terms, studying its data structures) without
  an applicable legal exception. No such clearance exists for this
  project. See `docs/format-findings.md`.
- **It has not been tested against a real Autodesk-produced file.** No
  ReCap installation or sample `.rcs`/`.rcp` file was available while
  building this. Every behavior above has only been exercised against
  synthetic fixtures in `fixtures/` (clearly marked as such, not real scan
  data). If you have authorized sample files, running `openrcs` against
  them and reporting mismatches is the single most useful contribution
  right now.

## Why this exists, and why it's deliberately small

RCS/RCP are closed, undocumented Autodesk formats with no open-source
reader (confirmed by checking CloudCompare, PDAL, and PCL support — none
of them read RCS/RCP; see `docs/format-findings.md` for sources). The
practical workaround everyone currently uses is exporting E57/LAS directly
from ReCap.

A fuller MIT-licensed project, [recap-mcp](https://github.com/xuantinhnbs-rgb/recap-mcp),
already solves most of this problem — `.rcp` manifest parsing, `.rcs`
header reading, registration extraction, and real LAS/LAZ-vs-BIM
comparison tooling — verified against an actual Autodesk ReCap install.
OpenRCS does not duplicate that work. It exists for the narrower case
recap-mcp doesn't target: a plain, cross-platform, pip-installable
library/CLI with no Windows or ReCap-install requirement, for scripts,
CI, or data-catalog pipelines that just need to know what's inside an
`.rcp`/`.rcs` file. If you have ReCap running on Windows and want the full
Scan-to-BIM toolchain (registration quality, BIM-mesh deviation, etc.),
use recap-mcp instead — OpenRCS's header-field decoding reuses its
published, cross-checked findings rather than re-deriving them.

## Install

```bash
pip install -e .
```

## Usage

```bash
openrcs inspect-scan path/to/scan.rcs
openrcs inspect-project path/to/project.rcp
openrcs validate path/to/scan.rcs
```

## Tests

```bash
python -m pytest tests/
```

Fixtures under `fixtures/` are synthetic (hand-built to exercise the
parsers) — not real ReCap output. See `docs/format-findings.md` for what
is and isn't verified.

## Documentation

- `docs/format-findings.md` — evidence ledger: every format claim, its
  source, and its confidence level.
- `docs/limitations.md` — explicit list of what doesn't work and why.

## License

Apache License 2.0 — see `LICENSE`. No Autodesk code or proprietary assets
are included or copied.
