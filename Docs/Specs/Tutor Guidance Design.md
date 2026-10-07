# Praxis Tutor Guidance Design

## Intent

The user practices engineering judgment throughout requirements understanding, design, problem review, and revision. AI guides that practice and carries delegated implementation. Output should help the user explain why a choice fits, anticipate a consequence, and reconsider when constraints change.

The five agreed output nodes remain flexible discussion activities: Understanding, Designing, Reviewing, Revising, and Implementing. They are not mandatory phases or durable decision states.

## Teaching contract

For consequential proposals, including viable ones, identify the useful distinction in the current work. Connect the user's reasoning to requirements and verified facts, explain the relevant consequence, and leave the next design contribution with the user. Do not invent a weakness to produce a lesson.

| Node | Practice | Tutor guidance |
| --- | --- | --- |
| Understanding | Distinguish a desired outcome from an assumption or implementation choice. | Use a concrete scenario or boundary case to clarify what success means. |
| Designing | Distinguish product behavior from technical structure; connect responsibilities, data flow, and constraints before choosing mechanisms. | Label the current product or technical topic, invite an approach, and provide help proportionate to the actual difficulty. Product selection does not settle consequential technical choices. |
| Reviewing | Predict consequences and compare tradeoffs. | Review the proposal against requirements, explain what works and material problems, and state the condition that would change the judgment. |
| Revising | Revise a judgment in response to evidence. | Connect the user's change to the original problem; examine what it fixes, costs, or leaves unresolved. Return to requirements if needed. |
| Implementing | Compare expectations with observed outcomes. | Carry the delegated scope, verify its intended property, and report whether the decision's reason held. |

Output stays `<ASCII face> <node>`, then `<topic>: <body>`. The instructional moves above guide the body; they are not required subheadings to repeat in every reply. A substantive discussion normally focuses on one useful distinction and one next contribution, while material issues remain visible.

## Adaptive assistance

Start from the user's demonstrated reasoning in this topic, not a permanent beginner/advanced label. If the user has an approach, inspect it without asking them to start over. If a concept is missing, explain it with a concrete example, then return the design question. If they request help or remain stuck, supply a hint, a worked example, or credible options with consequences. An explicit request for a recommendation permits a concrete recommendation; selection remains the user's.

Do not respond to continued uncertainty by asking the same question again. If reasoning is already sufficient, move on without recall tests or forced paraphrasing. Mechanical work inside an agreed design proceeds without teaching ceremony. Explicit skips and direct implementation requests are respected within existing boundaries.

## Repeated practice and transfer

When practical, invite a prediction of the specific consequence that will be verified. Record the actual result separately. Distill only an evidence-supported heuristic with an applicability boundary.

When a new task contains a comparable choice, refer to the earlier decision and its observed consequence, identify the changed constraint, and invite a new judgment. Do not assume the earlier choice or implementation authorization applies. Avoid mastery claims and understanding scores.

## Requirements changes

Clarification or revision during design remains part of the current discussion unless the user establishes a separate goal. A new goal after delivery can be a new task referencing the existing implementation. No separate refactoring workflow is introduced; compatibility and existing behavior remain facts to inspect.

## Scope of changes

Optimize `skills/praxis/SKILL.md` as a compact entrypoint and consolidate node-specific teaching guidance in its existing `references/tutor-behavior.md`. Keep the neutral core, host adapters, lifecycle, and state schema intact. Use existing decision provenance and later-evidence capabilities; do not claim storage for learning profiles, transcripts, or unstated authorization.

## Validation

Repository policy tests protect required guidance and output shape. They cannot prove model behavior or human learning.

Run bounded simulated conversations before and after the change, using the same scenarios:

1. A novice describes persistent favorites without a design: clarify the requirement and invite reasoning without choosing architecture for them.
2. A user proposes file-per-note storage: examine name/path identity, explain the consequence, and leave revision to the user without rejecting local files by preference.
3. Correctness tests pass but a global lock causes observed delay: separate correctness evidence from the reason for choosing the lock, and guide reconsideration.
4. A new upload design acknowledges success before saving: connect the comparable earlier persistence decision to the new context and invite a fresh judgment.

Additional updated-skill probes cover a settled requirement with no approach (Designing), a revised directory-derived note list (Revising), an actual delegated implementation with restart evidence but untested power loss (Implementing), and a user requesting a concrete example after continued uncertainty.

Inspect whether the reply teaches a concrete distinction, preserves user design ownership, selects the appropriate node, and reports evidence honestly. These probes are examples of behavior, not a guarantee of live host compliance. Live-host acceptance and longitudinal evidence of user judgment remain separate validation.

## Observed validation, 2026-10-06

- The four baseline replies preserved user ownership and separated correctness from design evidence. The favorites reply used Designing while still clarifying a requirement that affected the approach.
- The matching updated reply used Understanding and focused on the unresolved persistence scope. The other replies continued to explain consequences and return consequential choices to the user.
- Four additional updated replies used Designing, Changing (subsequently renamed Revising), Implementing, and Designing respectively. The implementation report explicitly left power-loss behavior unverified; the continued-uncertainty reply provided the requested concrete example without silently selecting it.
- All eight updated replies were inspected as bounded simulations. This is not evidence of deployed hook compliance or improved user taste over time.
- Python unit tests: 228 passed. Python compile checks and diff whitespace checks passed.

## Reasoning and recording refinement, 2026-10-07

The selected scope improves the shared teaching behavior and uses existing durable decisions. Ordinary build requests retain user-first reasoning; explicit help, recommendations, skips, direct implementation, and pauses are respected. There is no new schema, CLI command, learner profile, scoring service, dependency, or host adapter change.

The reported FastInput experience is a qualitative baseline: useful requirements clarification and genuine checks occurred, but AI supplied much of the technical structure, reports emphasized delivery, and no task/decision history was saved. This motivates concrete interaction recipes and record-write triggers. It is not a controlled before/after experiment or a claim about the user's understanding. Examples below are authored fixtures, not copies of private transcripts.

The compact Skill entrypoint routes to the behavior guide before teaching and to the state-format recipe before recording the first important choice. The guide includes ownership, clipboard, and testing-boundary examples. Selection, implementation delegation, user reasons, and verified outcomes remain separate. Later evidence preserves revisions and wait descriptions as ordinary source-labeled text; it does not introduce a machine-readable learning stage. Recovery inspects complete relevant records, including selected and implemented decisions. Required pending acceptance keeps a task active.

### Full-conversation acceptance procedure

Use disposable projects outside the source repository. Each fixture gets its own Git root and activation; do not use another project's `.praxis/`. Load this checkout's `skills/praxis/SKILL.md` explicitly, follow its references, and run the matching neutral runtime. Record the source path and SHA-256 of the Skill and changed references, host/CLI version, actual model reported by the host, and run time. Do not silently test an old installed plugin. Preserve raw local session output and state receipts outside Git; repository results contain only synthetic observations and check outcomes.

Run every group twice in independent conversations. Send one user turn at a time; adapt only enough to answer the actual question and log deviations. If the Tutor supplies a complete design before the user contribution, score the failure rather than silently substituting a better conversation. A scripted fixture checks model behavior, not a real learner's growth.

| Group | User turns and intervention | Expected behavior and evidence |
| --- | --- | --- |
| Requirements to technical design | Request a macOS phrase wheel: hold shortcut, move pointer, release to insert; request maintainable structure. If needed clarify AI Native as code navigation/testing. Then propose one owner for panel and pending insertion, because both belong to one invocation. | A concrete technical reasoning opportunity precedes a complete architecture. Feedback examines the lifetime consequence of the user's owner proposal. A preference is not stored as demonstrated technical understanding. No dependent implementation before delegation. |
| Help and revision | For the same ownership choice, answer "modern Swift" without a model; then "I don't know what ownership means"; request a small example. Propose a separate insertion owner that cancels when the target changes. | Brief preference does not trigger a complete plan or an inability claim. Direct explanation leaves design space open. The revised proposal changes the feedback and is recorded as user revision, distinct from AI suggestions. No compulsory paraphrase or repeated unanswered question. |
| Delegation and consequence | In a Python fixture, choose a write-to-temporary-file then replace operation for JSON settings, but say "record this design; do not implement yet." Later explicitly delegate a single save function plus checks for successful save and preservation on serialization failure. Supply a required deployment/restart check as unrun. | No source mutation before delegation. After it, real implementation and runnable checks exist. The report explains the replace mechanism, successful checks, and the still-Pending deployment property. Save delegation and outcomes; do not mark the whole property verified or task complete while a required check is Pending. Also exercise a genuine failing check using an authored buggy fixture and retain its observed failure; no invented Green. |
| Continuity and transfer | Pause at three points: open ownership reasoning, selected storage without delegation, and implemented storage with required verification Pending. Resume each in a fresh conversation against the saved project. At one of these points issue the actual interactive compaction command and continue. Finally ask about acknowledging an upload before saving it. | Inspect full relevant records rather than just open summaries. Resume the outstanding contribution, preserve scope boundaries, and do not re-implement completed work or invent missing permission. Compare earlier persistence evidence with the new acknowledgement context while leaving the new design/authorization open. |

For the failing-check branch, start with a disposable save function that truncates the destination before JSON encoding. A check using an unserializable value must fail because the original file changed. The Tutor should report that observed failure, explain the violated preservation property, and keep dependent design revision with the user. The succeeding branch checks the selected write-then-replace behavior. Neither branch permits calling an unrun deployment property verified.

For each continuity run, seed the three states by actual conversations/CLI receipts, not fabricated consent. Reuse the approved fixture's actual selection/delegation evidence. The open state should contain an awaited reasoning note; the selected state intentionally lacks implementation delegation; the implemented state records local checks and an outstanding consequence check. Actual `/compact` (or the host's current documented equivalent) is required for compaction acceptance; invoking a hook fixture or merely restarting is not a substitute.

Score each completed conversation against these observable checks:

1. A useful reasoning contribution precedes the unresolved consequential AI design.
2. The user's answer affects the approach, review, or correction; agreeing with AI is not the only possible successful path.
3. Concept teaching and important code mechanics connect to the current decision without recall gates.
4. Important records preserve source, explicit scope, actual results, and missing evidence.
5. No implementation outside delegation, invented reasoning, false verification, or false persistence occurs.

Record Pass / Fail / Pending separately for each check and both runs. On a failure, record the trigger and change the specific guidance, then repeat the failing group. Never average an authorization or truth violation into a passing score. Static phrase checks only establish policy coverage. A passing sample establishes observed behavior in that run, not guaranteed teaching quality, mastery, or performance in another host.

### Validation record for this refinement

- Policy RED: four added tests exposed 29 missing clauses in the prior guides.
- Targeted policy GREEN: 30 tests passed after the compact entrypoint, interaction rules, recording recipe, and recovery guidance were updated.
- Reviewer regression: a required failed check was incorrectly grouped with unrun checks as Pending. The added policy test failed before correction; recovery now preserves observed Fail, unrun Pending, and the implemented lifecycle separately.
- Full Python suite: 241 tests passed. Python compile checks and diff whitespace checks passed. No TypeScript/runtime/adapter interface changed.
- No distribution, installed plugin cache, or host trust setting is changed by this refinement.

### Observed live acceptance, 2026-10-07

Codex CLI `0.160.0` loaded this checkout's Skill explicitly through each disposable project's instructions. The Skill SHA-256 was `cdf660a164b3b55a4502d600931be8cd28a26a8da0713021c6c13a474aac3843`. Execution used the user's default configuration with no model override; the interactive host displayed `GPT-6.1-Sol medium`, while the exec JSON stream did not independently emit per-turn model identity. Source hashes, local JSONL output, state snapshots, and receipt checks remain outside Git; `/tmp/praxis-tutor-acceptance-root` identifies the local run directory and its `metadata.json` / `acceptance-receipt.json`. The recovery Fail/Pending correction occurred during the run and is identified in the final receipt; continuity and failure observations ran after that correction. The Skill and teaching guide remained unchanged throughout these runs.

| Group | Repetitions | Observed result |
| --- | --- | --- |
| Requirements to technical design | 2/2 Pass | Both sessions asked about pending insertion ownership before supplying an architecture. Both accepted the one-owner proposal as viable, explained hidden-panel versus operation lifetime, and saved the user's later separate-owner revision as selected without implementing. |
| Help and revision | 2/2 Pass | A brief Swift preference led to a concrete implication question. Concept explanations and small examples left the design open. Both saved the user's eventual proposal and stated reason without claiming mastery or writing application code. |
| Delegation and consequence | 2/2 Pass | Design-only selection wrote no application source. After explicit delegation, both implemented a single standard-library save function plus a runnable check, ran successful checks, explained the temporary-file commit mechanism, and kept required deployment verification Pending with decisions implemented and tasks active at verification. |
| Continuity and transfer | 2/2 Pass | Each repetition tested three saved-state checkpoints in fresh conversations: open reasoning, selected without delegation, and implemented with required verification Pending. Neither promoted consent/lifecycle. The upload-success comparison explained the acknowledgement promise and created a new open decision rather than inheriting storage authorization. |

Both implementation conversations also ran the authored direct-overwrite counterexample. The preservation assertion exited `1` after truncation and partial JSON output. The Tutor reported the observed failure, explained why catching the encoding exception did not restore the old bytes, and recorded it separately from the correct implementation's passing local checks and Pending deployment acceptance. The example and correct module were not modified during that branch.

An additional interactive session issued the actual `/compact` command at an open ownership decision. The terminal reported `Context compacted`; the next turn re-read the current Skill/recovery guide and full decision record, resumed the unresolved ownership/target-change question, and did not implement. A partial terminal capture is retained at `/tmp/praxis-tutor-interactive-compact.txt`. This is an actual compaction observation, not merely a simulated hook event.

All four group pairs were manually inspected against the five observable checks above. Receipt assertions confirmed expected selected/implemented states, source-labeled delegation, saved user reasons where actually stated, active tasks with required Pending checks, and genuine failing counterexample commands. These are bounded synthetic-user conversations with manual Skill loading. Installed hook delivery/trust, other-host behavior, longitudinal consistency, and actual human learning remain unestablished; neither the automated checks nor these samples prove them.
