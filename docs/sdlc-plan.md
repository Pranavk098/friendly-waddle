# SDLC Process — Pranav Agent Platform

This defines how every phase of `pranav-agent-platform-spec.md` §5 gets built. It wraps the spec's architecture in a repeatable plan→build→review→verify→deploy loop with defined audit gates. Follow it for every phase rather than improvising.

## Repo & branching

- `main` is always deployable. One short-lived branch per phase-slice (`phase0-scaffold-kb`, `phase1-mcp-mvp`, …), split further per sub-task if a phase spans multiple sessions.
- Branch protection on `main`: PR required, required status checks (starts with `kb-validate`/`lint-test`, grows as later CI workflows come online). No multi-approver requirement (solo project) — `/code-review` substitutes for a second reviewer.
- Conventional Commits, scoped by package (`feat(kb): ...`, `fix(mcp-server): ...`, `chore(ci): ...`).
- PRs require: Summary, DoD reference (spec §5 phase item), test evidence (actual command output, not just "tests pass"), audit-levels-touched checklist, rollback note. Keep PRs small (~<400 line diff).
- Secrets: `.env.example` committed, real `.env` gitignored, Anthropic key only in GitHub Actions / Railway secrets — never in a commit.

## Per-phase execution loop

1. **Plan** — `superpowers:writing-plans` (preceded by `superpowers:brainstorming` if the phase has open design choices) scoped to that phase's DoD from spec §5.
2. **Branch** for the phase.
3. **Build**, split by code type:
   - *Deterministic code* (KB loader/schema, `build.py`, skills matcher, rate limiter, MCP tool renderers, SSE plumbing, guard regex): strict TDD via `superpowers:test-driven-development` — failing test first.
   - *LLM-dependent/behavioral code* (system prompts, `check_fit` synthesis, chat generation): draft prompt → hand-run adversarial/gap questions manually → formalize into `contracts/` once behavior stabilizes (contract-first, sequenced into the phase that introduces the surface, not deferred to Phase 5).
4. **Self code-review** — `/code-review` on the diff; add `security-review` for anything touching LLM boundaries, `check_fit`, or injection surfaces.
5. **Debug loop** — `superpowers:systematic-debugging` for any unexpected failure, not ad-hoc patching.
6. **Verify** — `superpowers:verification-before-completion`: actually run the phase's DoD command/curl/inspector check and capture real output before claiming done.
7. **PR + CI gate** — open PR, CI runs the audit levels applicable so far, fix red, merge only when green.
8. **Deploy** (Phases 1, 3, 4+) — `engineering:deploy-checklist` before any Railway deploy.
9. **Close phase** — `superpowers:finishing-a-development-branch`; check off DoD; start next phase's plan.

## Audit layers

| Level | Checks | Enforced by | Runs when |
|---|---|---|---|
| 1 — KB/data integrity | Fact schema, evidence required on `verified` facts, evidence URLs 2xx, token budget, no dup IDs | `kb/build.py` validation + `kb-validate.yml` | Local pre-commit (fast checks) → PR CI (full, incl. URL fetch) |
| 2 — code correctness | ruff, `pyright --strict`, pytest unit/integration | TDD locally; `lint-test` CI job | Every commit locally; blocks PR merge |
| 3 — security | Injection-guard tests, secret scan, CORS check, rate-limiter behavior, no key leakage in logs | `security-review` skill + `/code-review`; CI secret-scan | Self-review pre-PR; every PR in CI |
| 4 — behavioral/contract | No-fabrication, gap honesty, injection resistance, scope deflection, cross-surface consistency | `contracts/` pytest suite via `contracts.yml` | PR CI (cheap subset) on `prompts/`/`kb/`/`contracts/` changes; nightly cron (full); gates deploy |
| 5 — deploy readiness | Checklist, `/healthz`, env-var/migration check, rollback path documented | `engineering:deploy-checklist` + `deploy.yml` gated on Levels 1 & 4 | Immediately before every Railway deploy |
| 6 — post-deploy/ongoing | Uptime, nightly full contract run, weekly digest (unanswered questions, KB staleness, check_fit gap clusters) | BetterStack; `contracts.yml` nightly cron; `weekly-digest.yml` | Scheduled, alerting |

## CI sequencing

Introduce each GitHub Actions workflow **when its subject matter first exists**, not all on day one:

- `kb-validate.yml` — Phase 0 (KB exists immediately).
- `contracts.yml` — when Phase 2 (`check_fit`) or Phase 3 (interview agent) introduces the first LLM-behavioral surface.
- `deploy.yml` — Phase 1, when the MCP server becomes the first real deploy target.
- `weekly-digest.yml` — Phase 6, when analytics tables exist.

A CI job with nothing to check yet is false-green noise.

## Phase map (see spec §5 for full detail)

| Phase | New audit levels exercised | DoD |
|---|---|---|
| 0 — Scaffold + KB | L1 | `python kb/build.py` emits all dist artifacts; CI green |
| 1 — MCP server MVP | L2, L5 (+ `deploy.yml`) | Connect from Claude.ai, get correct cited answers |
| 2 — check_fit | L3 (+ `contracts.yml`) | 3 real JDs → honest, cited, gap-inclusive; injection JDs don't move verdict table |
| 3 — Interview agent backend | L2–L4 on second surface | Streamed cited answer via curl; 429s enforce |
| 4 — Widget | L5 extended, a11y in review | Live on pranavkoduru.dev |
| 5 — Contract suite + public panel | L4 fully realized, nightly cron live | Contracts panel live and green; a grounding-breaking prompt edit fails CI |
| 6 — Polish + launch | L6 live (+ `weekly-digest.yml`) | Monitoring live, launch materials ready |

Open product decisions to make at the relevant phase: subdomain names (Phase 0/1), salary-range stance for `off_limits.yaml` (Phase 0, decline recommended), ResumeOS KB overlap (flag as v2, revisit after Phase 6).
