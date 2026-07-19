# CLAUDE.md — Pranav Agent Platform

## What this repo is

A monorepo shipping two public surfaces over one shared, evidence-cited knowledge base of Pranav's career facts:

- `kb/` — YAML fact files (source of truth) compiled by `kb/build.py` into `kb/dist/` artifacts.
- `interview-agent/` — FastAPI + Anthropic API backend; SSE chat grounded only in the KB.
- `mcp-server/` — FastMCP (Streamable HTTP) server exposing the KB as tools for recruiters' own AI assistants.
- `web-widget/` — Preact chat + contracts-status widget embedded in the Astro portfolio.
- `contracts/` — pytest behavioral contract suite that hits the real deployed prompt + KB + model.
- `shared/` — KB loader, LLM client, injection guard, rate limiter used by both services.

Full architecture: `pranav-agent-platform-spec.md`. SDLC process (branching, per-phase loop, audit levels, CI sequencing): `docs/sdlc-plan.md`.

## Hard invariant

**KB is the single source of truth. Never hardcode facts, metrics, or claims in prompts, tool code, or the widget.** Any change that lets the agent assert an uncited metric is a bug, not a feature.

## Per-package commands

| Package | Test | Lint | Type check |
|---|---|---|---|
| `kb` | `uv run --package kb pytest kb/tests` | `uv run ruff check kb` | `uv run pyright kb` |
| `shared` | `uv run --package shared pytest shared/tests` | `uv run ruff check shared` | `uv run pyright shared` |
| `interview-agent` | `uv run --package interview-agent pytest interview-agent/tests` | `uv run ruff check interview-agent` | `uv run pyright interview-agent` |
| `mcp-server` | `uv run --package mcp-server pytest mcp-server/tests` | `uv run ruff check mcp-server` | `uv run pyright mcp-server` |

Build KB artifacts: `uv run python kb/build.py`

## Contracts

Contracts hit the **live Anthropic API** — real cost, real latency. Run the cheap subset locally, never the full suite on a whim:

```
uv run pytest contracts -m cheap
```

The full suite (including nightly cross-surface consistency checks) runs in CI only.

## Style

- `ruff check` / `ruff format` for lint + formatting.
- `pyright --strict` for type checking — no untyped defs in new code.
- Conventional Commits, scoped by package: `feat(kb): ...`, `fix(mcp-server): ...`, `chore(ci): ...`.

## Process

This project follows a fixed per-phase loop (plan → branch → build [TDD for deterministic code, contract-first for LLM-behavioral code] → self code-review → debug loop if needed → verify → PR/CI gate → deploy → close phase) and six audit levels (KB integrity, code correctness, security, behavioral/contract, deploy readiness, post-deploy monitoring). See `docs/sdlc-plan.md` for the full definition — follow it rather than improvising a new process each session.
