# kb/facts/

Career facts, one YAML list per topic file (e.g. `identity.yaml`, `experience.yaml`, `open_source.yaml`, `projects.yaml`, `education.yaml`, `work_authorization.yaml`, `availability.yaml`, `research.yaml`, `off_limits.yaml` — see spec §1.2 for the full inventory). `skills.yaml` (the skills matrix) is a separate format handled in a later phase — see spec §1.4 — and is not yet wired into `kb/build.py`.

## Provenance convention

Every fact in this directory is either:

1. **Sourced** — copied from `pranav-agent-platform-spec.md` §1.2, where it appears as real,
   specific content (a named PR, a named employer, real-looking evidence URLs). Marked with the
   verification level the spec itself assigned.
2. **Placeholder** — `verification: in_progress`, `claim` starting `PLACEHOLDER —`, no evidence.
   These exist so the file/category structure matches the spec's fact-file inventory, but no
   factual content has been written for them. Claude did not invent descriptions for named
   projects/employers/credentials it has no source for — that would violate this project's own
   hard invariant (never assert an uncited claim).

**Before Phase 1 ships anything publicly:** replace every placeholder with real claim text (or
delete the entry), and double-check the two sourced facts (`open_source.yaml`'s `agt-pr-2694`,
`experience.yaml`'s `atai-tensorrt`) for accuracy — Claude carried these over from the spec
document but has not independently verified the linked URLs or numbers.

`work_authorization.yaml` is a placeholder and needs particular care — it's legally/personally
sensitive and must be phrased exactly as you want it stated publicly, not left as a stand-in.

Each file is a YAML list of fact objects matching `../schema/fact.schema.json`. Rules enforced by
`kb/build.py`:
- Every fact must satisfy the schema (structural shape).
- Every `verification: verified` fact must have at least one `evidence` entry with `type: primary`.
- Fact `id`s must be unique across all files.
- (CI only) every evidence URL must return 2xx.
