---
name: praxis-enable
description: Enable Praxis tutoring in the current project when the user invokes Praxis Enable.
---

# Praxis Enable

Before running the command, tell the user that activation also adds a removable Praxis block to the project's `AGENTS.md`. It checks live activation before software work and stays inactive while paused.
Run `praxis enable --cwd . --agents-fallback` in the current project and report the actual activation and fallback results concisely. If the user declines the block, run `praxis enable --cwd .`; existing authorization does not need another confirmation.
The block preserves surrounding instructions and can be removed with `praxis agents-fallback --cwd . --remove`. On delivery problems, use `praxis doctor --cwd .`; when using a separately installed CLI, pass `--plugin-root` with the installed plugin directory to inspect its adapter.
Enabling Praxis is not approval of any engineering decision.
If local command execution is unavailable, report that this action requires a local project execution surface; do not claim success or ask the user to run the CLI.
