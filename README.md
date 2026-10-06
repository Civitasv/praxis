<p align="center">
  <img src=".github/assets/praxis-mark.svg" width="96" height="96" alt="Praxis">
</p>

<h1 align="center">Praxis</h1>

<p align="center"><strong>Build with AI. Develop taste.</strong></p>

<p align="center">
  A plugin for developing engineering taste while building real software with your coding agent.
</p>

<p align="center">
  <sub>Codex · Cursor · CodeBuddy · DeepSeek Harness</sub>
</p>

---

## Philosophy

**AI makes implementation cheap. Taste is still earned.**

Fast output is not the same as good engineering. If AI makes every meaningful choice before you understand it, you may ship faster today without getting better at choosing tomorrow.

Praxis extends the coding agent you already use. Routine work stays fast. When a decision can shape the system, Praxis slows down just enough to expose the reasoning, alternatives, tradeoffs, and consequences.

That attention compounds. The more good decisions you understand, the faster you can recognize them yourself.

**Sometimes slower is faster.**

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

        This choice matters:
        history is durable product state, so a Redis restart
        should not erase it.

        The tradeoff is an extra durable write path,
        but Redis stays disposable.

You     I don't know what "source of truth" means.

Agent   It means the database owns the canonical history.
        Redis can make access faster, but losing Redis
        should not lose messages.

You     Got it.

Agent   ✓ Implemented
        ✓ Verified: history survived a Redis restart.
```

Praxis keeps the learning inside the same workflow, so the decision becomes part of your own taste instead of disappearing into the implementation.

## What Praxis tries to preserve

Engineering taste is the ability to recognize better choices earlier.

It grows by connecting decisions to consequences:

```text
compare
→ choose
→ implement
→ observe
→ internalize
→ choose better next time
```

Praxis does not try to slow down the whole task. It spends attention where understanding compounds, so future decisions become faster, better, and more independent.

## Install

Requires Python 3.10+.

Install Praxis:

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

Once enabled, work normally. Praxis only slows down decisions worth learning from.

## Commands

| Agent | Enable | Disable | Status |
| --- | --- | --- | --- |
| Cursor | `/praxis enable` | `/praxis disable` | `/praxis status` |
| DeepSeek Harness | `/praxis enable` | `/praxis disable` | `/praxis status` |
| CodeBuddy | `/praxis:enable` | `/praxis:disable` | `/praxis:status` |
| Codex | `$praxis:praxis-enable` | `$praxis:praxis-disable` | `$praxis:praxis-status` |

## Update Praxis

Update Praxis:

```bash
python3 -m pip install --user --upgrade 'git+https://github.com/Civitasv/praxis.git'
```

Then refresh the integration you use.

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

Current integrations: Codex, Cursor, CodeBuddy, and DeepSeek Harness / Cordis. Distribution is currently source-based.

## Documentation

Implementation details live under `Docs/`:

- [Architecture overview](Docs/Architecture/Overview.md)
- [Tutor model](Docs/Architecture/Tutor%20Model.md)
- [Harness integrations](Docs/Architecture/Harness%20Integration.md)
- [Feature specifications](Docs/Specs/)
- [Development and validation](Docs/Development/Validation.md)

Contributors should start with [Code.md](Code.md) and [State.md](State.md).
