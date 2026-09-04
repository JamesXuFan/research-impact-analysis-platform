# P36 Subagents

A set of Claude Code subagent definitions for COMP3888_W11_02_P36.

## Install

Put the contents of `agents/` into `.claude/agents/` at the repository root:

```
COMP3888_W11_02_P36/
└── .claude/
    └── agents/
        ├── pandas-safety.md
        ├── finding-checker.md
        ├── repo-scout.md
        ├── metrics-consistency.md
        ├── data-dictionary-sync.md
        └── minutes-drafter.md
```

Commit it and the whole team gets them. For personal use only, put them in `~/.claude/agents/`
instead.

Once installed, Claude decides when to delegate based on each `description`. You can also call one
by name: *"use pandas-safety on cleaning/dedupe.py"*.

## The six agents

| Name | When it runs | Model |
|---|---|---|
| `pandas-safety` | After editing any data-processing code | sonnet |
| `finding-checker` | After drafting any key finding | opus / high |
| `repo-scout` | When you need to know where something is implemented | haiku |
| `metrics-consistency` | Before merging an analysis branch | sonnet |
| `data-dictionary-sync` | Before opening a pull request | haiku |
| `minutes-drafter` | After every meeting | sonnet |

The first three are generic — a few edits and they work on any project. The last three are bound to
this project's definitions and file paths.

## Two places to wire them into the process

**PR checklist.** Add two lines: if you touched `src/p36/`, run `pandas-safety`; if you added or
renamed a derived column, run `data-dictionary-sync`. Both catch things a human reviewer reliably
misses, and both have consequences that only surface weeks later.

**Before Week 10 integration.** Run `metrics-consistency` once. Eight people working six directions
in parallel makes definitional drift the most expensive source of rework on this project, and it
gets cheaper the earlier it is found.

## If you edit these

- `description` is read by the router and decides whether the agent gets dispatched at all. The body
  is read by the subagent itself and decides what it does once dispatched. Two different readers —
  do not blur them together.
- A subagent cannot see the main conversation, and the main agent cannot see its working steps.
  **Only its final message comes back.** That is why every body ends with an output format section.
  Remove it and the caller receives prose it has to re-parse.
- Keep `tools` narrowed to read-only on the review agents. Give one write access and it will start
  fixing things instead of reporting them.

Full field reference: https://code.claude.com/docs/en/sub-agents
