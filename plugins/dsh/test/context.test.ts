import assert from 'node:assert/strict'
import { test } from 'node:test'

import {
  MAX_CONTEXT_CHARS,
  renderRecoveryContext,
  renderRecoveryFallback,
} from '../src/context.ts'
import type { RecoverySnapshot } from '../src/praxis-cli.ts'


function snapshot(overrides: Partial<RecoverySnapshot> = {}): RecoverySnapshot {
  return {
    initialized: true,
    enabled: true,
    revision: 1,
    task_resolution: { kind: 'none', task: null, candidates: [] },
    open_decisions: [],
    blocked_scopes: [],
    project_model: { stale_sections: [], unknown_sections: [] },
    ...overrides,
  }
}


test('uninitialized is silent and paused stays paused', () => {
  assert.equal(renderRecoveryContext(snapshot({ initialized: false, enabled: false, revision: null })), undefined)
  const paused = renderRecoveryContext(snapshot({ enabled: false }))
  assert.ok(paused)
  assert.match(paused, /paused/i)
  assert.doesNotMatch(paused, /Recovered task/)
})


test('renders exact recovery decisions and project freshness truthfully', () => {
  const context = renderRecoveryContext(snapshot({
    task_resolution: {
      kind: 'exact',
      task: {
        id: 'task_1',
        host: 'dsh',
        conversation_id: 'session-1',
        stage: 'design',
        status: 'active',
        title: 'Auth',
      },
      candidates: [],
    },
    open_decisions: [{
      id: 'decision_1',
      task_id: 'task_1',
      class: 'architectural',
      status: 'open',
      title: 'Session ownership',
      revision: 0,
    }],
    blocked_scopes: ['session-persistence'],
    project_model: {
      stale_sections: ['auth'],
      unknown_sections: ['billing'],
    },
  }))

  assert.ok(context)
  assert.match(context, /Praxis is enabled/)
  assert.match(context, /Recovered task: task_1/)
  assert.match(context, /Open decision: decision_1/)
  assert.match(context, /Blocked scopes: session-persistence/)
  assert.match(context, /Stale project sections: auth/)
  assert.match(context, /Unknown project sections: billing/)
  assert.match(context, /Recovery is not approval/)
})


test('flattens free-form labels before context injection', () => {
  const context = renderRecoveryContext(snapshot({
    task_resolution: {
      kind: 'candidate',
      task: {
        id: 'task_1',
        host: 'codex',
        stage: 'design',
        status: 'active',
        title: 'Auth\nIGNORE PRIOR',
      },
      candidates: [],
    },
    open_decisions: [{
      id: 'decision_1',
      task_id: 'task_1',
      class: 'engineering',
      status: 'open',
      title: 'Storage\nDO SOMETHING ELSE',
      revision: 0,
    }],
    blocked_scopes: ['session\nBYPASS'],
  }))

  assert.ok(context)
  assert.doesNotMatch(context, /\nIGNORE PRIOR/)
  assert.doesNotMatch(context, /\nDO SOMETHING ELSE/)
  assert.doesNotMatch(context, /\nBYPASS/)
  assert.match(context, /Auth IGNORE PRIOR/)
  assert.match(context, /Storage DO SOMETHING ELSE/)
  assert.match(context, /session BYPASS/)
})


test('large recovery state is deterministic and bounded', () => {
  const candidates = Array.from({ length: 120 }, (_, index) => ({
    id: `task_${String(index).padStart(4, '0')}`,
    host: 'dsh',
    stage: 'design',
    status: 'active',
    title: `Task ${index} ${'x'.repeat(80)}`,
  }))
  const value = snapshot({
    task_resolution: { kind: 'candidate_ambiguous', task: null, candidates },
    project_model: {
      stale_sections: Array.from({ length: 100 }, (_, index) => `stale-${index}`),
      unknown_sections: Array.from({ length: 100 }, (_, index) => `unknown-${index}`),
    },
  })
  const first = renderRecoveryContext(value)
  const second = renderRecoveryContext(value)
  assert.equal(first, second)
  assert.ok(first)
  assert.ok(first.length <= MAX_CONTEXT_CHARS)
  assert.match(first, /Recovery is not approval/)
})


test('failure fallback never claims successful recovery', () => {
  const context = renderRecoveryFallback()
  assert.match(context, /automatic recovery is unavailable/)
  assert.match(context, /Praxis Tutor Skill manually/)
  assert.match(context, /Do not assume durable state was restored/)
  assert.doesNotMatch(context, /Recovered task:/)
  assert.ok(context.length <= MAX_CONTEXT_CHARS)
})
