# Known Limitations

- **No point-cloud decoding.** OpenRCS cannot read actual point data out of
  an `.rcs` file. The internal point-record layout, octree index, and
  compression scheme are not publicly documented and have not been reverse
  engineered here (see `format-findings.md` for why). `openrcs convert`
  refuses to run rather than produce fabricated or placeholder points.
- **No verified RCP schema.** OpenRCS reports the raw XML structure inside
  an `.rcp` project (tags, nesting, referenced file paths it can find by
  pattern-matching for `.rcs`/`.rcc` strings), but does not claim to know
  which XML element is a transform matrix, a clip region, etc. — that
  mapping is not verified.
- **Magic-byte detection is unverified against a real file.** The `ADOCT`
  signature check is cross-corroborated by three independent public sources
  (see ledger), but no authentic Autodesk-produced `.rcs` file has been
  run through it. It could be wrong.
- **No differential testing performed.** Section 7 of the task (compare
  OpenRCS output against authorized ReCap exports) was not possible — no
  authorized ReCap installation or export was available.
- **No binary/executable reverse engineering was performed or attempted.**
  Autodesk's license terms prohibit it without specific legal clearance,
  and REA's decompiler backends are not configured in this environment
  regardless.
