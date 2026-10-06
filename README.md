<p align="center">
  <img src=".github/assets/praxis-mark.svg" width="96" height="96" alt="Praxis">
</p>

<h1 align="center">Praxis</h1>

<p align="center"><strong>Build with AI. Keep the judgment.</strong></p>

<p align="center">
  A tutor layer for coding agents that keeps consequential engineering decisions visible<br>
  while the agent handles the mechanical work.
</p>

<p align="center">
  <sub>Codex · Cursor · CodeBuddy · DeepSeek Harness</sub>
</p>

---

## Philosophy

**The new bottleneck is judgment.**

Coding agents can now produce working software without exposing much of the reasoning that shaped it.

That is useful. It also creates a strange failure mode:

> You can get much better at producing software without getting much better at engineering it.

Praxis is built for that gap.

It stays quiet during mechanical work. When a choice is consequential enough to shape the system — data ownership, state boundaries, failure behavior, dependencies, API shape, migration strategy — Praxis makes the decision legible before the agent commits to it.

Then the agent keeps moving.

## What using Praxis feels like

```text
You     Add persistent chat history.

Agent   I’ll use the database as the source of truth
        and Redis as a cache.

Praxis  Before implementation, make that conclusion legible.

        Why it follows:
        message history is durable product state. A Redis restart
        should not erase it.

        What it costs:
        the database adds a durable write path and some complexity,
        but Redis stays disposable.

        Where it stops being true:
        if chat history is intentionally ephemeral, Redis-only
        may be enough.

You     So the database owns the history. Redis only makes access
        faster, and losing Redis should not lose messages.

Praxis  Exactly. That is the model the implementation should preserve.

Agent   ✓ Implemented

Praxis  ✓ Verified: history survived a Redis restart.
```

Praxis is not trying to make you choose every implementation detail.

The AI can still reach the conclusion. Praxis keeps the reasoning, tradeoff, and boundary visible until the conclusion is something you actually understand — not just something the agent decided for you.

## How Praxis behaves

| Situation | Praxis |
| --- | --- |
| Mechanical implementation | Stays out of the way |
| AI reaches a consequential conclusion | Makes the reasoning and boundary legible |
| You already understand it | Keeps moving |
| You are unsure | Builds the missing mental model, without turning it into a quiz |
| Implementation finishes | Checks whether reality supported the conclusion |
| A new session starts | Restores the durable decision context |

The loop is simple:

**surface → understand → implement → verify → retain**

Praxis should make the agent more productive **without making you less capable**.

## Install

Praxis has a small host-neutral Python core plus an integration for the coding agent you use.

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

Praxis should intervene only when there is something worth learning from.

## Not a quiz. Not a second agent.

Praxis is not trying to become another autonomous coder.

It does not interrupt every implementation detail, ask you to defend obvious choices, or slow the project down for the sake of “teaching.”

If you do not know the answer, **“I don't know” is a valid answer**.

Praxis should give you just enough structure to understand the next meaningful choice, then hand execution back to the coding agent.

## What Praxis tries to preserve

For most of software history, engineering judgment was built through repetition:

```text
make a decision
→ implement it
→ observe what happened
→ update your mental model
→ make a better decision next time
```

AI compresses the implementation step dramatically.

Praxis exists so it does not accidentally compress away the learning loop too.

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

The repository ships working integrations for Codex, Cursor, CodeBuddy, and DeepSeek Harness / Cordis. Distribution is currently source-based; public marketplace publication is not claimed yet.

## Documentation

The README is intentionally product-facing. Implementation details live under `Docs/`.

- [Architecture overview](Docs/Architecture/Overview.md)
- [Tutor model](Docs/Architecture/Tutor%20Model.md)
- [Harness integrations](Docs/Architecture/Harness%20Integration.md)
- [Feature specifications](Docs/Specs/)
- [Development and validation](Docs/Development/Validation.md)

Contributors should start with [Code.md](Code.md) and [State.md](State.md).
