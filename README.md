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

You lead the meaningful choices; Praxis guides your reasoning, and your coding agent implements the scope you delegate. That includes both **product design**—what people experience—and **technical design**—how responsibilities, state, and data flow support that experience.

Suppose you want persistent chat history in a local, single-user app:

> **You:** Keep my chat history after restarting the app.
>
> **(o.o) Understanding**
>
> Persistence: Should messages survive only an app restart, or also move between devices?
>
> **You:** Just this device for now.
>
> **(o-o) Designing**
>
> Product design / Sending: What should the user see while a message is being saved, and if saving fails?
>
> **You:** Show it immediately as pending. If saving fails, keep the text and let me retry.
>
> **(o-o) Designing**
>
> Technical design / Storage: How would you store the messages and decide when a pending message becomes saved?
>
> **You:** Use SQLite. Mark the message saved immediately, then write it in the background.
>
> **(o_^) Reviewing**
>
> Acknowledgment: SQLite fits local storage, and keeping failed input supports retry. But marking a message saved before the write succeeds creates a gap: the app could close while a “saved” message exists only in memory. How would you change that order?
>
> **You:** Keep it pending until the database write succeeds. On failure, leave it available for retry.
>
> **(^_~) Revising**
>
> Write order: That keeps the immediate feedback you wanted while making “saved” reflect a completed write. Check that saved messages survive a restart; separately simulate a failed write to check that the message stays unsaved and available for retry.
>
> **You:** Implement that design and run the restart and failed-write checks.
>
> **(^_^) Implementing**
>
> Result: Implemented the pending, saved, and retry behavior. Saved messages survived the restart check, and a simulated failed write left the message unsaved and available for retry. Sudden power loss was not tested. The useful distinction: immediate feedback can precede persistence; a “saved” acknowledgment must follow it.

This is an illustrative conversation, not a recorded acceptance test.

The five nodes describe the current activity, not a fixed sequence. A technical constraint can send you back to understanding the requirement; a revision can lead to another review. Titles follow your conversation's language.

When you need help, Praxis explains the missing concept or compares credible options and their tradeoffs. Once you select a design and delegate implementation, routine work moves ahead. The learning comes from connecting **your reasoning → the selected design → the observed result**.

## What Praxis helps you build

Engineering taste is the ability to recognize better choices earlier.

It grows through product choices such as interaction and recovery behavior, and technical choices such as ownership, module boundaries, and failure handling. Each connects a decision to its consequences:

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

This loop can return to earlier discussions as requirements or evidence change.

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

In Codex settings, open Hooks and review and trust the Praxis hooks to allow automatic tutoring context.

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
