import assert from 'node:assert/strict'
import { test } from 'node:test'

import { Context } from '@deepseek-ai/cordis'
import AgentRegistry, { agentEvents } from '@deepseek-ai/dsh-agent'
import type { Agent, PreStepDecision } from '@deepseek-ai/dsh-agent'
import { createUserMessage } from '@deepseek-ai/dsh-llm'
import type { UserMessage } from '@deepseek-ai/dsh-llm'

import { registerPraxisLifecycle } from '../src/lifecycle.ts'
import type { RecoverySnapshot, RecoveryStatusInput } from '../src/praxis-cli.ts'


function enabledSnapshot(revision = 1): RecoverySnapshot {
  return {
    initialized: true,
    enabled: true,
    revision,
    task_resolution: { kind: 'none', task: null, candidates: [] },
    open_decisions: [],
    blocked_scopes: [],
    project_model: { stale_sections: [], unknown_sections: [] },
  }
}


function uninitializedSnapshot(): RecoverySnapshot {
  return {
    initialized: false,
    enabled: false,
    revision: null,
    task_resolution: { kind: 'none', task: null, candidates: [] },
    open_decisions: [],
    blocked_scopes: [],
    project_model: { stale_sections: [], unknown_sections: [] },
  }
}


function stubAgent(ctx: Context, cwd = '/tmp/project', rawId = 'session-1') {
  const id = rawId as Agent['id']
  const injected: UserMessage[] = []
  const agent = {
    id,
    session: { id, header: { cwd } },
    ctx,
    inject(message: UserMessage) {
      injected.push(message)
    },
  } as unknown as Agent
  return { agent, injected }
}


async function lifecycleHarness(
  run: (input: RecoveryStatusInput) => Promise<RecoverySnapshot>,
): Promise<{ ctx: Context; fiber: Awaited<ReturnType<Context['plugin']>> }> {
  const ctx = new Context()
  await ctx.plugin(AgentRegistry)
  const fiber = await ctx.plugin({
    name: 'praxis-lifecycle-test',
    apply(pluginCtx: Context) {
      registerPraxisLifecycle(pluginCtx, run)
    },
  })
  return { ctx, fiber }
}


test('agent/created injects bounded DSH recovery using cwd and session identity', async () => {
  const calls: RecoveryStatusInput[] = []
  const { ctx } = await lifecycleHarness(async input => {
    calls.push(input)
    return enabledSnapshot()
  })
  try {
    const { agent, injected } = stubAgent(ctx, '/workspace/repo', 'session-a')
    const detach = ctx.agents.enter(agent, undefined)
    try {
      await ctx.agents.announce(agent, 'resume')
      assert.equal(calls.length, 1)
      assert.equal(calls[0]?.cwd, '/workspace/repo')
      assert.equal(calls[0]?.host, 'dsh')
      assert.equal(calls[0]?.conversationId, 'session-a')
      assert.ok(calls[0]?.signal)
      assert.equal(calls[0]?.signal?.aborted, false)
      assert.equal(injected.length, 1)
      const source = injected[0]?.source
      assert.equal(source?.kind, 'praxis-dsh')
      if (source?.kind !== 'praxis-dsh') throw new Error('expected praxis-dsh source')
      assert.equal(source.form, 'instructions')
      assert.match(JSON.stringify(injected[0]?.content), /Praxis is enabled/)
      assert.match(JSON.stringify(injected[0]?.content), /Recovery is not approval/)
    } finally {
      detach()
    }
  } finally {
    await ctx.fiber.dispose()
  }
})


test('agent/created is silent when Praxis is uninitialized and contains recovery failures', async () => {
  {
    const { ctx } = await lifecycleHarness(async () => uninitializedSnapshot())
    try {
      const { agent, injected } = stubAgent(ctx)
      ctx.agents.enter(agent, undefined)
      await assert.doesNotReject(ctx.agents.announce(agent, 'startup'))
      assert.deepEqual(injected, [])
    } finally {
      await ctx.fiber.dispose()
    }
  }

  {
    const { ctx } = await lifecycleHarness(async () => {
      throw new Error('python unavailable')
    })
    try {
      const { agent, injected } = stubAgent(ctx)
      ctx.agents.enter(agent, undefined)
      await assert.doesNotReject(ctx.agents.announce(agent, 'startup'))
      assert.equal(injected.length, 1)
      assert.match(JSON.stringify(injected[0]?.content), /automatic recovery is unavailable/)
      assert.match(JSON.stringify(injected[0]?.content), /Do not assume durable state was restored/)
    } finally {
      await ctx.fiber.dispose()
    }
  }
})


test('agent lifecycle forwards cancellation and suppresses fallback after abort', async () => {
  let resolveEntered!: (signal: AbortSignal) => void
  const entered = new Promise<AbortSignal>(resolve => { resolveEntered = resolve })
  const { ctx } = await lifecycleHarness(async input => {
    assert.ok(input.signal)
    resolveEntered(input.signal)
    return await new Promise<RecoverySnapshot>((_resolve, reject) => {
      input.signal?.addEventListener('abort', () => reject(new Error('aborted')), { once: true })
    })
  })
  try {
    const controller = new AbortController()
    const { agent, injected } = stubAgent(ctx)
    ctx.agents.enter(agent, undefined)
    const announcing = ctx.agents.announce(agent, 'resume', controller.signal)
    const observed = await entered.promise
    assert.equal(observed.aborted, false)
    controller.abort(new Error('cancel lifecycle'))
    await assert.doesNotReject(announcing)
    assert.equal(observed.aborted, true)
    assert.deepEqual(injected, [])
  } finally {
    await ctx.fiber.dispose()
  }
})


test('disposing the lifecycle plugin aborts running recovery without fallback injection', { timeout: 3000 }, async () => {
  let resolveEntered!: (signal: AbortSignal) => void
  const entered = new Promise<AbortSignal>(resolve => { resolveEntered = resolve })
  const { ctx, fiber } = await lifecycleHarness(async input => {
    assert.ok(input.signal)
    resolveEntered(input.signal)
    return await new Promise<RecoverySnapshot>((_resolve, reject) => {
      if (input.signal?.aborted) {
        reject(new Error('already aborted'))
        return
      }
      input.signal?.addEventListener('abort', () => reject(new Error('plugin disposed')), { once: true })
    })
  })
  try {
    const { agent, injected } = stubAgent(ctx)
    ctx.agents.enter(agent, undefined)
    const announcing = ctx.agents.announce(agent, 'resume')
    const signal = await entered
    assert.equal(signal.aborted, false)
    const disposing = fiber.dispose()
    await assert.doesNotReject(announcing)
    await disposing
    assert.equal(signal.aborted, true)
    assert.deepEqual(injected, [])
  } finally {
    await ctx.fiber.dispose()
  }
})


test('pre-step skips empty continuations and always delegates', async () => {
  let runs = 0
  const { ctx } = await lifecycleHarness(async () => {
    runs += 1
    return enabledSnapshot()
  })
  try {
    const { agent } = stubAgent(ctx)
    const seed: PreStepDecision = { kind: 'enter', messages: [] }
    let delegated = 0
    const decision = await agentEvents(ctx, agent).waterfall(
      'agent/pre-step',
      { messages: [], turn: 1, step: 2, signal: new AbortController().signal },
      () => {
        delegated += 1
        return Promise.resolve(seed)
      },
    )
    assert.equal(decision, seed)
    assert.equal(delegated, 1)
    assert.equal(runs, 0)
  } finally {
    await ctx.fiber.dispose()
  }
})


test('pre-step appends changed recovery context once without rewriting user messages', async () => {
  let revision = 1
  let runs = 0
  const { ctx } = await lifecycleHarness(async () => {
    runs += 1
    if (revision === 1) return enabledSnapshot(1)
    return {
      ...enabledSnapshot(revision),
      project_model: { stale_sections: ['auth'], unknown_sections: [] },
    }
  })
  try {
    const { agent } = stubAgent(ctx)
    const user = createUserMessage({
      content: [{ type: 'text', text: 'continue auth' }],
      source: { kind: 'user' },
    })

    const enter = async (): Promise<PreStepDecision> => ({ kind: 'enter', messages: [user] })
    const first = await agentEvents(ctx, agent).waterfall(
      'agent/pre-step',
      { messages: [user], turn: 1, step: 1, signal: new AbortController().signal },
      enter,
    )
    assert.equal(first.kind, 'enter')
    if (first.kind !== 'enter') throw new Error('expected enter')
    assert.equal(first.messages[0], user)
    assert.equal(first.messages.length, 2)
    assert.equal(first.messages[1]?.source.kind, 'praxis-dsh')

    const second = await agentEvents(ctx, agent).waterfall(
      'agent/pre-step',
      { messages: [user], turn: 2, step: 1, signal: new AbortController().signal },
      enter,
    )
    assert.equal(second.kind, 'enter')
    if (second.kind !== 'enter') throw new Error('expected enter')
    assert.deepEqual(second.messages, [user])

    revision = 2
    const third = await agentEvents(ctx, agent).waterfall(
      'agent/pre-step',
      { messages: [user], turn: 3, step: 1, signal: new AbortController().signal },
      enter,
    )
    assert.equal(third.kind, 'enter')
    if (third.kind !== 'enter') throw new Error('expected enter')
    assert.equal(third.messages.length, 2)
    assert.equal(runs, 3)
  } finally {
    await ctx.fiber.dispose()
  }
})


test('pre-step preserves downstream reject and does not run recovery after rejection', async () => {
  let runs = 0
  const { ctx } = await lifecycleHarness(async () => {
    runs += 1
    return enabledSnapshot()
  })
  try {
    const { agent } = stubAgent(ctx)
    const user = createUserMessage({
      content: [{ type: 'text', text: 'blocked elsewhere' }],
      source: { kind: 'user' },
    })
    const decision = await agentEvents(ctx, agent).waterfall(
      'agent/pre-step',
      { messages: [user], turn: 1, step: 1, signal: new AbortController().signal },
      () => Promise.resolve({ kind: 'reject' as const }),
    )
    assert.deepEqual(decision, { kind: 'reject' })
    assert.equal(runs, 0)
  } finally {
    await ctx.fiber.dispose()
  }
})


test('disposing the lifecycle plugin removes DSH listeners', async () => {
  let runs = 0
  const { ctx, fiber } = await lifecycleHarness(async () => {
    runs += 1
    return enabledSnapshot()
  })
  try {
    await fiber.dispose()
    const { agent } = stubAgent(ctx)
    const user = createUserMessage({
      content: [{ type: 'text', text: 'after unload' }],
      source: { kind: 'user' },
    })
    const seed: PreStepDecision = { kind: 'enter', messages: [user] }
    const decision = await agentEvents(ctx, agent).waterfall(
      'agent/pre-step',
      { messages: [user], turn: 1, step: 1, signal: new AbortController().signal },
      () => Promise.resolve(seed),
    )
    assert.equal(decision, seed)
    assert.equal(runs, 0)
  } finally {
    await ctx.fiber.dispose()
  }
})
