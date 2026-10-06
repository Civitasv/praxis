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

## Quick start

Praxis currently runs from source and supports **Codex** and **DeepSeek Harness / Cordis**.

### 1. Get Praxis

```bash
git clone https://github.com/Civitasv/praxis.git
cd praxis
```

Python 3.10+ is required.

### 2. Enable Praxis for a project

From the Praxis checkout:

```bash
python -m praxis enable --cwd /path/to/your-project
```

Enabling is project-local. Installing or loading the host integration does **not** automatically enable Praxis in every repository.

You can inspect the current project state with:

```bash
python -m praxis status --cwd /path/to/your-project
```

### 3. Make Praxis available to your coding agent

**Codex**

Use this repository as a local Codex plugin. The repository root contains the Praxis plugin manifest and shared Tutor Skill.

**DeepSeek Harness / Cordis**

Use the plugin under `plugins/dsh/` in your DSH/Cordis composition. The DSH package is currently repository-local rather than published to npm.

Host setup and compatibility details live in [Docs/Architecture/Harness Integration.md](Docs/Architecture/Harness%20Integration.md).

### 4. Work normally

There is no special “Praxis task language” you need to learn.

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
- [Codex and DSH integration](Docs/Architecture/Harness%20Integration.md)
- [Feature specifications](Docs/Specs/)
- [Development and validation](Docs/Development/Validation.md)

For contributors working on the repository itself, start with [Code.md](Code.md) and [State.md](State.md).
