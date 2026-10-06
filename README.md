# Praxis

**Build with AI. Keep the judgment.**

Praxis is an AI tutor for building software with coding agents.

AI has made it dramatically easier to produce software. But producing a working artifact is not the same thing as experiencing the decisions required to build it, and it is not the same thing as gaining the judgment to make those decisions again.

Praxis is built around that gap.

## Philosophy

For most of software history, engineering judgment was accumulated through repetition:

```text
make a decision
→ implement it
→ observe what happened
→ update your mental model
→ make a better decision next time
```

Coding agents can now skip much of that experience. They can choose the data model, architecture, state ownership, failure strategy, dependency, and API shape — then hand you a finished implementation.

That is useful, but it creates a new failure mode:

> You can become much better at producing software without becoming much better at engineering it.

Praxis keeps the productive part of AI automation while preserving the part that builds judgment.

The agent should handle mechanical execution. Praxis keeps consequential choices visible.

When a decision matters, Praxis should help you understand:

- what is actually being decided;
- what constraints the real project imposes;
- what the meaningful alternatives are;
- what each alternative gives up;
- what happened after the choice was implemented.

Then the agent can keep moving.

Praxis is not a quiz system and it does not try to slow work down for the sake of teaching. The learning happens inside the real project, through real decisions and their consequences.

If you do not know the answer, **“I don't know” is a valid answer**. Praxis should explain enough for the next meaningful choice instead of turning the interaction into an exam.

## What using Praxis feels like

Without Praxis:

```text
You: Add persistent chat history.

Agent: Done.
```

With Praxis:

```text
You: Add persistent chat history.

Praxis: There is one consequential choice before implementation:
        what owns durable message history?

        Redis-only is simpler, but losing Redis loses history.
        A database source of truth adds another dependency but gives
        durable ownership and makes Redis disposable.

You: I don't know which one I want.

Praxis: If message history must survive cache loss or restarts,
        use the database as the source of truth and Redis only for
        transient delivery/cache behavior.

You: Do that.

Agent: Implements it and verifies restart behavior.

Praxis: The implementation matched the decision:
        history survived the Redis restart, so the ownership boundary
        behaved as intended.
```

The point is not that you typed more. The point is that the important decision stayed visible long enough to become part of your own mental model.

## Install

Praxis has two parts: the small project-state CLI and the integration for your coding agent. Install the CLI once:

```bash
python3 -m pip install --user 'git+https://github.com/Civitasv/praxis.git'
```

Python 3.10+ is required. On Windows, use `py -m pip install --user 'git+https://github.com/Civitasv/praxis.git'`.

Then install the integration for the agent you use.

### Codex

```bash
codex plugin marketplace add Civitasv/praxis
codex
```

Then install **Praxis** from the Plugins Directory. You can do the final install either from Codex with `/plugins` or from the **ChatGPT desktop app** after restarting it and opening Plugins.

Codex's current CLI can add and manage marketplace sources, but it **does not currently expose a non-interactive plugin install command**, so the final install action is UI-based. Repository/local marketplace testing is supported in ChatGPT Desktop; installing a local plugin on the web does not deploy its local hook scripts.

### Cursor

macOS / Linux / WSL:

```bash
mkdir -p ~/.cursor/plugins/local && git clone --depth 1 https://github.com/Civitasv/praxis.git ~/.cursor/plugins/local/praxis
```

Restart Cursor or run **Developer: Reload Window**.

Cursor's `agent` CLI **does not currently expose a plugin-install subcommand**. The command above uses Cursor's official local-plugin directory. Do not replace the checkout with a symlink to a repository outside that directory; Cursor skips those external symlinks.

### DeepSeek Harness / Cordis

Install Praxis into the profile you use:

```bash
dsh plugin --profile web add github:Civitasv/praxis
```

Then restart that profile:

```bash
dsh --profile web
```

Replace `web` with your own DSH profile name when needed. DSH plugin management requires `pnpm` on `PATH`.

### CodeBuddy

```bash
codebuddy plugin marketplace add Civitasv/praxis --name praxis && codebuddy plugin install praxis@praxis
```

The command adds the Praxis marketplace and installs Praxis at user scope. Use `--scope project` on the install command if you want the project to declare the plugin for collaborators.

## Enable Praxis in a project

Installing an integration does **not** enable Praxis in every repository. Open the project in your coding agent and use its Praxis control command:

| Agent | Enable | Disable | Status |
| --- | --- | --- | --- |
| Cursor | `/praxis enable` | `/praxis disable` | `/praxis status` |
| DeepSeek Harness | `/praxis enable` | `/praxis disable` | `/praxis status` |
| CodeBuddy | `/praxis:enable` | `/praxis:disable` | `/praxis:status` |
| Codex | `$praxis enable` | `$praxis disable` | `$praxis status` |

In ChatGPT Desktop, an installed Praxis plugin can also be addressed with `@Praxis` on a Work/Codex surface that has access to the local project; ask it to enable, disable, or show Praxis status for the current project.

You do **not** need to run the underlying Python command yourself. The CLI remains the host-adapter implementation boundary.

Then work normally. There is no special “Praxis task language” to learn.

Ask the coding agent to build something:

```text
Add organization-level API keys.

Move this app from local state to persisted projects.

Add retries to the payment workflow.

Refactor authentication so web and CLI share the same session model.
```

Praxis should stay out of mechanical work and intervene when a choice is consequential enough to improve future engineering judgment.

When it surfaces a decision, you can:

- give your current proposal;
- ask for the tradeoffs;
- say you are unsure;
- accept a recommendation;
- choose a different direction and explain why.

Once the decision is explicit, the agent continues implementation and verification.

## What Praxis tries to preserve

Praxis is designed around a simple separation:

**AI should remove unnecessary effort. It should not remove the experiences from which judgment is formed.**

That means a healthy Praxis session should leave you with more than a finished diff. You should also know why important choices were made, what tradeoffs were accepted, and whether reality supported the original reasoning.

Over time, the goal is not to make you dependent on Praxis.

The goal is for decisions that once required explanation to become decisions you can make well yourself.

## Documentation

README is intentionally product-facing. Implementation details and repository internals live under `Docs/`:

- [Architecture overview](Docs/Architecture/Overview.md)
- [Tutor model](Docs/Architecture/Tutor%20Model.md)
- [Codex, Cursor, CodeBuddy, and DSH integration](Docs/Architecture/Harness%20Integration.md)
- [Feature specifications](Docs/Specs/)
- [Development and validation](Docs/Development/Validation.md)

For contributors working on the repository itself, start with [Code.md](Code.md) and [State.md](State.md).
