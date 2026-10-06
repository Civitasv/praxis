import { createHash } from 'node:crypto'
import type { Context } from '@deepseek-ai/cordis'
import type { Agent, PreStepDecision } from '@deepseek-ai/dsh-agent'
import { createUserMessage } from '@deepseek-ai/dsh-llm'
import type { ContextFormed } from '@deepseek-ai/dsh-llm'

import { renderRecoveryContext, renderRecoveryFallback } from './context.ts'
import { runRecoveryStatus } from './praxis-cli.ts'
import type { RecoverySnapshot, RecoveryStatusInput } from './praxis-cli.ts'

declare module '@deepseek-ai/dsh-llm' {
  interface MessageSourceMap {
    'praxis-dsh': { kind: 'praxis-dsh' } & ContextFormed
  }
}

export type RecoveryRunner = (input: RecoveryStatusInput) => Promise<RecoverySnapshot>

const CONTEXT_SOURCE = { kind: 'praxis-dsh', form: 'instructions' } as const

function projectCwd(agent: Agent): string | undefined {
  const cwd = agent.session.header.cwd
  return typeof cwd === 'string' && cwd.trim().length > 0 ? cwd : undefined
}

function contextDigest(text: string): string {
  return createHash('sha256').update(text, 'utf8').digest('hex')
}

function contextMessage(text: string) {
  return createUserMessage({
    content: [{ type: 'text', text }],
    source: CONTEXT_SOURCE,
  })
}

export function registerPraxisLifecycle(
  ctx: Context,
  run: RecoveryRunner = runRecoveryStatus,
): void {
  const lastContextDigest = new WeakMap<Agent, string>()
  const pluginAbort = new AbortController()
  ctx.effect(
    () => () => {
      if (!pluginAbort.signal.aborted) {
        pluginAbort.abort(new Error('praxis-dsh plugin disposed'))
      }
    },
    'praxis-dsh: abort recovery subprocesses',
  )

  const recover = async (
    agent: Agent,
    eventSignal?: AbortSignal,
  ): Promise<string | undefined> => {
    const cwd = projectCwd(agent)
    if (cwd === undefined) return undefined
    const signal = eventSignal === undefined
      ? pluginAbort.signal
      : AbortSignal.any([eventSignal, pluginAbort.signal])
    if (signal.aborted) return undefined
    try {
      const snapshot = await run({
        cwd,
        host: 'dsh',
        conversationId: String(agent.id),
        signal,
      })
      if (signal.aborted) return undefined
      return renderRecoveryContext(snapshot)
    } catch (error: unknown) {
      if (signal.aborted) return undefined
      ctx.logger.warn(`praxis-dsh: automatic recovery failed: ${String(error)}`)
      return renderRecoveryFallback()
    }
  }

  ctx.on('agent/created', async ({ agent, signal }) => {
    const context = await recover(agent, signal)
    if (context === undefined) {
      lastContextDigest.delete(agent)
      return
    }
    try {
      agent.inject(contextMessage(context))
      lastContextDigest.set(agent, contextDigest(context))
    } catch (error: unknown) {
      ctx.logger.warn(`praxis-dsh: failed to inject recovery context: ${String(error)}`)
    }
  })

  ctx.on(
    'agent/pre-step',
    async ({ agent, messages, signal }, next): Promise<PreStepDecision> => {
      if (messages.length === 0) return next()

      const downstream = await next()
      if (downstream.kind === 'reject' || signal.aborted) return downstream

      const context = await recover(agent, signal)
      if (context === undefined) {
        lastContextDigest.delete(agent)
        return downstream
      }

      const digest = contextDigest(context)
      if (lastContextDigest.get(agent) === digest) return downstream

      lastContextDigest.set(agent, digest)
      return {
        ...downstream,
        messages: [...downstream.messages, contextMessage(context)],
      }
    },
  )
}
