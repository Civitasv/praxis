import type {
  RecoveryDecisionSummary,
  RecoverySnapshot,
  RecoveryTaskSummary,
} from './praxis-cli.ts'

export const MAX_CONTEXT_CHARS = 3000

const RECOVERY_FOOTER = 'Recovery is not approval. Use the shared Praxis Tutor Skill for details.'
const FALLBACK_CONTEXT = [
  'Praxis automatic recovery is unavailable.',
  'Use the shared Praxis Tutor Skill manually.',
  'Do not assume durable state was restored.',
  'Recovery is not approval.',
].join(' ')

function inlineText(value: unknown): string {
  return String(value).split(/\s+/u).filter(Boolean).join(' ')
}

function taskLine(task: RecoveryTaskSummary): string {
  return [
    inlineText(task.id),
    '—',
    inlineText(task.title ?? '(untitled)'),
    `[stage=${inlineText(task.stage)}, status=${inlineText(task.status)}]`,
  ].join(' ')
}

function decisionLine(decision: RecoveryDecisionSummary): string {
  return `Open decision: ${inlineText(decision.id)} — ${inlineText(decision.title)} [class=${inlineText(decision.class)}]`
}

function bounded(lines: readonly string[]): string {
  const footerBudget = RECOVERY_FOOTER.length + 1
  const budget = MAX_CONTEXT_CHARS - footerBudget
  const kept: string[] = []
  let used = 0

  for (const rawLine of lines) {
    const line = inlineText(rawLine)
    const separator = kept.length === 0 ? 0 : 1
    const available = budget - used - separator
    if (available <= 0) break

    if (line.length <= available) {
      kept.push(line)
      used += separator + line.length
      continue
    }
    if (available > 1) {
      kept.push(line.slice(0, available - 1) + '…')
    }
    break
  }

  if (kept.length === 0) return RECOVERY_FOOTER.slice(0, MAX_CONTEXT_CHARS)
  return `${kept.join('\n')}\n${RECOVERY_FOOTER}`
}

export function renderRecoveryFallback(): string {
  return FALLBACK_CONTEXT.slice(0, MAX_CONTEXT_CHARS)
}

export function renderRecoveryContext(snapshot: RecoverySnapshot): string | undefined {
  if (!snapshot.initialized) return undefined
  if (!snapshot.enabled) {
    return 'Praxis is paused for this project. Do not activate Tutor behavior until the user explicitly resumes it.'
  }

  const lines: string[] = [
    'Praxis is enabled for this project.',
    'Load and follow the shared Praxis Tutor Skill.',
  ]

  const resolution = snapshot.task_resolution
  if (resolution.kind === 'exact') {
    lines.push(`Recovered task: ${taskLine(resolution.task)}`)
  } else if (resolution.kind === 'exact_ambiguous') {
    lines.push('Multiple matching DSH tasks; ask the user which task to continue:')
    for (const task of resolution.candidates) lines.push(`- ${taskLine(task)}`)
  } else if (resolution.kind === 'candidate') {
    lines.push(`Recoverable task candidate: ${taskLine(resolution.task)}`)
    lines.push("This task is a candidate only; do not adopt or rebind it without the user's choice.")
  } else if (resolution.kind === 'candidate_ambiguous') {
    lines.push('Multiple pending task candidates; ask the user which task to continue:')
    for (const task of resolution.candidates) lines.push(`- ${taskLine(task)}`)
  }

  for (const decision of snapshot.open_decisions) lines.push(decisionLine(decision))
  if (snapshot.blocked_scopes.length > 0) {
    lines.push(`Blocked scopes: ${snapshot.blocked_scopes.map(inlineText).join(', ')}`)
  }
  if (snapshot.project_model.stale_sections.length > 0) {
    lines.push(`Stale project sections: ${snapshot.project_model.stale_sections.map(inlineText).join(', ')}`)
  }
  if (snapshot.project_model.unknown_sections.length > 0) {
    lines.push(`Unknown project sections: ${snapshot.project_model.unknown_sections.map(inlineText).join(', ')}`)
  }

  return bounded(lines)
}
