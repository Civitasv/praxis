<p align="center">
  <img src=".github/assets/praxis-mark.svg" width="96" height="96" alt="Praxis">
</p>

<h1 align="center">Praxis</h1>

<p align="center"><strong>Build with AI. Keep the judgment.</strong></p>

<p align="center">
  A plugin for people who want to learn from their coding agent while building real software.<br>
  Praxis makes important AI conclusions understandable before implementation moves on.
</p>

<p align="center">
  <sub>Codex · Cursor · CodeBuddy · DeepSeek Harness</sub>
</p>

---

## Philosophy

**Shipping faster should not mean learning less.**

Coding agents can now produce working software while skipping much of the experience that used to build engineering judgment.

That is useful if the only goal is output. But many people also want to get better at the craft while they build.

> Praxis is for people who want the leverage of AI without giving up the learning that comes from understanding important decisions.

It is a plugin for that gap.

It extends the coding agent you already use rather than introducing another agent or a separate workflow. Its core Tutor behavior is implemented as a shared skill, with a small host-neutral core and thin host integrations around it.

During mechanical work, Praxis stays out of the way. When the agent reaches a consequential conclusion — about data ownership, state boundaries, failure behavior, dependencies, API shape, migration strategy — the plugin makes the reasoning legible before implementation continues.

## What using Praxis feels like

Without Praxis:

```text
You     Add persistent chat history.

Agent   I’ll use the database as the source of truth
        and Redis as a cache.

        ✓ Implemented
```

With the Praxis plugin enabled:

```text
You     Add persistent chat history.

Agent   I’ll use the database as the source of truth
        and Redis as a cache.

        Why:
        message history is durable product state. A Redis restart
        should not erase it.

        Tradeoff:
        this adds a durable write path, but keeps Redis disposable.

        Boundary:
        if chat history is intentionally ephemeral, Redis-only
        may be enough.

You     So the database owns history. Redis only makes access faster,
        and losing Redis should not lose messages.

Agent   Exactly.

        ✓ Implemented
        ✓ Verified: history survived a Redis restart.
```

It is still the same coding agent doing the work.

The difference is that useful learning is pulled out of the real task instead of being skipped. Praxis turns consequential conclusions into small teaching moments: why this choice fits the project, what it trades away, and when a different answer would be better.

You do not need to turn the session into a lesson or know the right question to ask. The plugin should notice what is worth understanding and explain only enough to make that part of the work yours too.

## Learn while building

| During real work | Agent with Praxis |
| --- | --- |
| Routine implementation | Keeps moving |
| Important engineering conclusion | Explains the reasoning |
| New concept you may not know yet | Builds the minimum useful mental model |
| Meaningful tradeoff | Shows what you gain and give up |
| Context-dependent answer | Explains when the conclusion changes |
| Implementation finishes | Connects the result back to the reasoning |

The loop is simple:

**build → notice → explain → understand → verify**

Praxis is not trying to replace documentation, courses, or deliberate study. It makes the project you are already building a better place to learn.

## Install

Praxis is installed as a plugin for your coding agent. Its shared Tutor skill defines the core behavior; a small host-neutral core and thin integrations provide durable state and recovery across hosts.

### 1. Install the core

Requires Python 3.10+.

```bash
python3 -m pip install --user 'git+https://github.com/Civitasv/praxis.git'
```

On Windows, replace `python3` with `py`.

### 2. Add your agent integration

<details>
<summary><strong>Codex</strong></summary>

```bash
codex plugin marketplace add Civitasv/praxis
codex plugin add praxis@praxis
```

Enable Praxis in the project:

```text
$praxis:praxis-enable
```

You can also select **Praxis Enable** from the Codex skill picker.

</details>

<details>
<summary><strong>Cursor</strong></summary>

```bash
mkdir -p ~/.cursor/plugins/local
git clone --depth 1 https://github.com/Civitasv/praxis.git ~/.cursor/plugins/local/praxis
```

Restart Cursor, then run:

```text
/praxis enable
```

</details>

<details>
<summary><strong>DeepSeek Harness / Cordis</strong></summary>

Requires `pnpm` on `PATH`. Replace `web` with your profile name.

```bash
dsh plugin --profile web add github:Civitasv/praxis
dsh --profile web
```

Then run:

```text
/praxis enable
```

</details>

<details>
<summary><strong>CodeBuddy</strong></summary>

```bash
codebuddy plugin marketplace add Civitasv/praxis --name praxis && codebuddy plugin install praxis@praxis
```

Then run:

```text
/praxis:enable
```

</details>

Once enabled, just work normally:

```text
Add organization-level API keys.

Move this app from local state to persisted projects.

Add retries to the payment workflow.

Refactor authentication so web and CLI share the same session model.
```

Praxis should stay quiet when there is nothing useful to learn and step in when the work contains a decision, concept, or consequence worth understanding.

## Not a quiz. Not a second agent.

Praxis is a plugin for your existing coding agent. It does not run beside it as another autonomous coder.

The plugin should not interrupt every implementation detail, ask you to defend obvious choices, or slow the project down for the sake of teaching.

If you do not know the answer, **“I don't know” is a valid answer**.

The agent should explain just enough for the next important conclusion to make sense, then continue the work.

## What Praxis tries to preserve

For most of software history, learning and building were tightly coupled. Engineering judgment was built through repetition:

```text
make a decision
→ implement it
→ observe what happened
→ update your mental model
→ make a better decision next time
```

AI compresses the implementation step dramatically — and can accidentally compress away the learning that came with it.

Praxis exists for users who want to keep that learning loop alive while still using AI at full speed.

The durable output is not only the diff. It is also:

- the important choice that was made;
- the constraints that shaped it;
- the tradeoff that was accepted;
- the evidence that later confirmed or challenged it.

Over time, decisions that once needed explanation should become decisions you can make well yourself.

That is the point.

## Commands

| Agent | Enable | Disable | Status |
| --- | --- | --- | --- |
| Cursor | `/praxis enable` | `/praxis disable` | `/praxis status` |
| DeepSeek Harness | `/praxis enable` | `/praxis disable` | `/praxis status` |
| CodeBuddy | `/praxis:enable` | `/praxis:disable` | `/praxis:status` |
| Codex | `$praxis:praxis-enable` | `$praxis:praxis-disable` | `$praxis:praxis-status` |

The shared Praxis skill provides Tutor behavior for enabled projects; project controls live in the dedicated Codex control skills.

## Update Praxis

Update the core first:

```bash
python3 -m pip install --user --upgrade 'git+https://github.com/Civitasv/praxis.git'
```

Then update your agent integration.

<details>
<summary><strong>Codex</strong></summary>

```bash
codex plugin marketplace upgrade praxis
codex plugin add praxis@praxis
```

Open a new chat to load the updated skill.

</details>

<details>
<summary><strong>Cursor</strong></summary>

```bash
git -C ~/.cursor/plugins/local/praxis pull --ff-only
```

Restart Cursor.

</details>

<details>
<summary><strong>DeepSeek Harness / Cordis</strong></summary>

```bash
dsh plugin --profile web update praxis
dsh --profile web
```

</details>

<details>
<summary><strong>CodeBuddy</strong></summary>

```bash
codebuddy plugin marketplace update praxis && codebuddy plugin update praxis@praxis
```

Then reload plugins:

```text
/reload-plugins
```

</details>

## Status

Praxis is currently **alpha**.

This repository packages the plugin across Codex, Cursor, CodeBuddy, and DeepSeek Harness / Cordis. The shared Tutor skill is the core behavior behind those integrations. Distribution is currently source-based; public marketplace publication is not claimed yet.

## Documentation

The README is intentionally product-facing. Implementation details live under `Docs/`.

- [Architecture overview](Docs/Architecture/Overview.md)
- [Tutor model](Docs/Architecture/Tutor%20Model.md)
- [Harness integrations](Docs/Architecture/Harness%20Integration.md)
- [Feature specifications](Docs/Specs/)
- [Development and validation](Docs/Development/Validation.md)

Contributors should start with [Code.md](Code.md) and [State.md](State.md).
