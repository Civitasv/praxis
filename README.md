<p align="center">
  <img src=".github/assets/praxis-mark.svg" width="96" height="96" alt="Praxis">
</p>

<h1 align="center">Praxis</h1>

<p align="center"><strong>Build with AI. Learn from it.</strong></p>

<p align="center">
  A plugin for people who want to learn from their coding agent while building real software.
</p>

<p align="center">
  <sub>Codex · Cursor · CodeBuddy · DeepSeek Harness</sub>
</p>

---

## Philosophy

Coding agents can produce software faster than the experience behind that software can turn into judgment.

Praxis extends the coding agent you already use. When the agent reaches an important engineering conclusion, Praxis helps make the reasoning understandable: why it fits the project, what it trades away, and when the answer would change.

Routine work keeps moving. Useful learning stays visible.

**Build with AI. Keep the judgment.**

## What using Praxis feels like

Without Praxis:

```text
You     Add persistent chat history.

Agent   I’ll use the database as the source of truth
        and Redis as a cache.

        ✓ Implemented
```

With Praxis:

```text
You     Add persistent chat history.

Agent   I’ll use the database as the source of truth
        and Redis as a cache.

You     I don't know why.

Agent   Message history is durable product state.
        If Redis restarts, users should not lose it.

        The tradeoff is an extra durable write path,
        but Redis stays disposable.

        If history were intentionally ephemeral,
        Redis-only could be enough.

You     So the database owns history; Redis only makes it faster.

Agent   Exactly.

        ✓ Implemented
        ✓ Verified: history survived a Redis restart.
```

Same agent, same task. Praxis changes what gets explained before the work moves on.

## What Praxis tries to preserve

Engineering judgment is built by connecting decisions to consequences:

```text
decide
→ implement
→ observe
→ update your mental model
→ decide better next time
```

AI can compress implementation dramatically. Praxis keeps the important parts of that loop visible enough to learn from while you build.

## Install

Requires Python 3.10+.

Install the shared Praxis core:

```bash
python3 -m pip install --user 'git+https://github.com/Civitasv/praxis.git'
```

On Windows, replace `python3` with `py`.

Then add Praxis to the coding agent you use.

<details>
<summary><strong>Codex</strong></summary>

```bash
codex plugin marketplace add Civitasv/praxis
codex plugin add praxis@praxis
```

Enable it in the project:

```text
$praxis:praxis-enable
```

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

Replace `web` with your profile name.

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

Once enabled, work normally. Praxis stays quiet during routine implementation and surfaces explanations when the work contains something worth learning.

## Commands

| Agent | Enable | Disable | Status |
| --- | --- | --- | --- |
| Cursor | `/praxis enable` | `/praxis disable` | `/praxis status` |
| DeepSeek Harness | `/praxis enable` | `/praxis disable` | `/praxis status` |
| CodeBuddy | `/praxis:enable` | `/praxis:disable` | `/praxis:status` |
| Codex | `$praxis:praxis-enable` | `$praxis:praxis-disable` | `$praxis:praxis-status` |

## Update Praxis

Update the shared core first:

```bash
python3 -m pip install --user --upgrade 'git+https://github.com/Civitasv/praxis.git'
```

Then update the integration you use.

<details>
<summary><strong>Codex</strong></summary>

```bash
codex plugin marketplace upgrade praxis
codex plugin add praxis@praxis
```

Open a new chat.

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

The repository ships integrations for Codex, Cursor, CodeBuddy, and DeepSeek Harness / Cordis. Distribution is currently source-based; public marketplace publication is not claimed yet.

## Documentation

Implementation details live under `Docs/`:

- [Architecture overview](Docs/Architecture/Overview.md)
- [Tutor model](Docs/Architecture/Tutor%20Model.md)
- [Harness integrations](Docs/Architecture/Harness%20Integration.md)
- [Feature specifications](Docs/Specs/)
- [Development and validation](Docs/Development/Validation.md)

Contributors should start with [Code.md](Code.md) and [State.md](State.md).
