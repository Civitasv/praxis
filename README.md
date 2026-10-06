<p align="center">
  <img src=".github/assets/praxis-mark.svg" width="96" height="96" alt="Praxis">
</p>

<h1 align="center">Praxis</h1>

<p align="center"><strong>Build with AI. Develop taste.</strong></p>

<p align="center">
  A plugin for developing engineering taste while coding with AI.
</p>

<p align="center">
  <sub>Codex · Cursor · CodeBuddy · DeepSeek Harness</sub>
</p>

<p align="center">
  <strong>English</strong> · <a href="README.zh-CN.md">简体中文</a>
</p>

---

## Philosophy

**AI makes implementation cheap. Taste is still earned.**

Fast output is not the same as good engineering. If AI makes every meaningful choice before you understand it, you may ship faster today without getting better at choosing tomorrow.

Praxis extends the coding agent you already use. Routine work stays fast. When a decision can shape the system, Praxis slows down just enough to expose the reasoning, alternatives, tradeoffs, and consequences.

That attention compounds. The more good decisions you understand, the faster you can recognize them yourself.

**Slower at the right moment is faster over time.**

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

Agent   What should persistence guarantee, and how would you store the history?

You     Keep it after restarts. I'd put messages in Redis because it is fast.

Agent   Redis durability depends on configuration. With snapshots, a failure
        can lose messages since the last snapshot. Is that acceptable here?

You     No. What other options do I have?

Agent   A durable database can own the messages; Redis could be an optional
        cache. This adds a write path, but losing the cache needn't lose history.
        For this scope, using only the database would also avoid cache complexity.

You     Use only the database first. Save a message before acknowledging it,
        and test that acknowledged messages survive a restart.

Agent   That addresses the durability gap. This step will add storage and
        restart checks; caching remains outside the scope.

You     Implement that design.

Agent   ✓ Implemented the agreed storage behavior.
        ✓ Verified: acknowledged history survived a restart.
```

This example illustrates the intended interaction; it is not a recorded acceptance test.

Praxis keeps the learning inside the same workflow, so the decision becomes part of your own taste instead of disappearing into the implementation.

## What Praxis helps you build

Engineering taste is the ability to recognize better choices earlier.

It grows by connecting decisions to consequences:

```text
understand
→ propose
→ examine
→ revise
→ choose and delegate
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

## License

Praxis is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0-only)**.

You may use, modify, and redistribute Praxis under the terms of the AGPL. Its copyleft requirements include source-availability obligations for covered modifications, including when a modified version is offered for use over a network. See [LICENSE](LICENSE) for the full terms.

## Documentation

Implementation details live under `Docs/`:

- [Architecture overview](Docs/Architecture/Overview.md)
- [Tutor model](Docs/Architecture/Tutor%20Model.md)
- [Harness integrations](Docs/Architecture/Harness%20Integration.md)
- [Feature specifications](Docs/Specs/)
- [Development and validation](Docs/Development/Validation.md)

Contributors should start with [Code.md](Code.md) and [State.md](State.md).
