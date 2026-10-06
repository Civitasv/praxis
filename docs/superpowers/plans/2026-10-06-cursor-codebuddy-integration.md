# Cursor and CodeBuddy Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add native Cursor and CodeBuddy plugin/hook support using the existing Praxis CLI and shared Tutor Skill.

**Architecture:** A shared Python hook layer owns direct-argv `recovery-status` execution and bounded rendering. Cursor and CodeBuddy wrappers own only event parsing and host response envelopes. No MCP or new durable state is added.

**Tech Stack:** Python 3.10+ stdlib; JSON plugin/hook manifests; unittest; GitHub Actions.

**Spec:** `Docs/Specs/Feature-07 Cursor and CodeBuddy Integration.md`

## Global Constraints

- Reuse `skills/praxis/`; never copy it.
- Reuse `praxis recovery-status`; no new host-owned state.
- No MCP files or servers.
- Context hard cap: 3000 characters.
- Host wrappers fail open.
- Prompt/transcript text is not approval.
- Cursor `beforeSubmitPrompt` does not claim unsupported context injection.

## Review Focus

- Plugin manifest path correctness for shared root skills.
- Cursor session cwd/session identity when only environment variables are present.
- Cursor prompt hook must refresh without emitting unsupported recovery context.
- CodeBuddy event envelope must use exact `SessionStart` / `UserPromptSubmit` names.
- Recovery subprocess arguments must remain direct argv with `shell=False`.

### Task 1: Shared recovery hook bridge

**Files:**
- Create: `plugins/shared/recovery_hook.py`
- Create: `tests/test_shared_recovery_hook.py`

- [ ] Write failing tests for direct argv CLI execution, protocol parsing, bounded/sanitized rendering, silence/paused/fallback behavior.
- [ ] Verify RED.
- [ ] Implement the shared bridge and renderer.
- [ ] Verify GREEN.

### Task 2: Cursor plugin

**Files:**
- Create: `.cursor-plugin/plugin.json`
- Create: `plugins/cursor/hooks/hooks.json`
- Create: `plugins/cursor/hooks/praxis_context.py`
- Create: `tests/test_cursor_integration.py`

- [ ] Write failing manifest and subprocess hook tests.
- [ ] Verify RED.
- [ ] Implement Cursor manifest, lifecycle config, and thin wrapper.
- [ ] Verify sessionStart injection, beforeSubmitPrompt refresh-only behavior, prompt/transcript independence, and uninitialized silence.

### Task 3: CodeBuddy plugin

**Files:**
- Create: `.codebuddy-plugin/plugin.json`
- Create: `plugins/codebuddy/hooks/hooks.json`
- Create: `plugins/codebuddy/hooks/praxis_context.py`
- Create: `tests/test_codebuddy_integration.py`

- [ ] Write failing manifest and subprocess hook tests.
- [ ] Verify RED.
- [ ] Implement CodeBuddy manifest, hooks, and thin wrapper.
- [ ] Verify SessionStart/UserPromptSubmit nested additionalContext behavior and uninitialized silence.

### Task 4: Distribution, docs, and CI

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `Docs/Architecture/Harness Integration.md`
- Modify: `Docs/Development/Validation.md`
- Modify: `Code.md`
- Modify: `State.md`
- Modify: `README.md`
- Modify: `tests/test_repository_contract.py`
- Create: `tests/test_agent_plugin_distribution.py`

- [ ] Write closure/distribution tests first.
- [ ] Verify RED.
- [ ] Add Python 3.10 Cursor/CodeBuddy package CI job and durable docs.
- [ ] Keep README product-facing: add Cursor/CodeBuddy to supported-host usage only, no lifecycle internals.
- [ ] Run whole suite and self-review.
