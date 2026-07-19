# kb/facts/

Career facts, one YAML list per topic file (e.g. `identity.yaml`, `experience.yaml`, `open_source.yaml`, `projects.yaml`, `skills.yaml`, `education.yaml`, `work_authorization.yaml`, `availability.yaml`, `research.yaml`, `off_limits.yaml` — see spec §1.2 for the full inventory).

This directory is intentionally empty as scaffolded in Phase 0 — **populating it is on the user, not Claude Code** (spec §5: "this is mostly you writing truth, Claude Code writing tooling"). `kb/build.py` runs correctly against zero facts (emits a valid, empty compiled KB); it will validate real facts against `../schema/fact.schema.json` as they're added.

Each file is a YAML list of fact objects matching the schema:

```yaml
- id: agt-pr-2694
  category: open_source
  claim: >
    Authored and merged PR #2694 in ... [full, truthful, specific claim]
  evidence:
    - url: https://github.com/org/repo/pull/2694
      type: primary        # primary | secondary | self_reported
  verification: verified   # verified | self_reported | in_progress
  date: 2026-05
  tags: [tag1, tag2]
  metrics:
    some_number: 1.5
```

Rules enforced by `kb/build.py`:
- Every fact must satisfy `../schema/fact.schema.json` (structural shape).
- Every `verification: verified` fact must have at least one `evidence` entry with `type: primary`.
- Fact `id`s must be unique across all files.
- (CI only) every evidence URL must return 2xx.
