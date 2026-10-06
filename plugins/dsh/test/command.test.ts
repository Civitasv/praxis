import assert from 'node:assert/strict'
import { test } from 'node:test'

import type { Context } from '@deepseek-ai/cordis'
import type { Agent } from '@deepseek-ai/dsh-agent'
import type { CommandDefinition } from '@deepseek-ai/dsh-commands'

import {
  parsePraxisCommand,
  registerPraxisCommand,
} from '../src/command.ts'
import type { PraxisControlInput, PraxisControlResult } from '../src/praxis-cli.ts'


test('parses the Praxis control grammar', () => {
  assert.equal(parsePraxisCommand(''), 'status')
  assert.equal(parsePraxisCommand(' status '), 'status')
  assert.equal(parsePraxisCommand(' enable '), 'enable')
  assert.equal(parsePraxisCommand(' DISABLE '), 'disable')
  assert.equal(parsePraxisCommand('pause'), undefined)
  assert.equal(parsePraxisCommand('enable now'), undefined)
})


test('registers /praxis and executes control against the receiving project', async () => {
  let definition: CommandDefinition | undefined
  let seen: PraxisControlInput | undefined

  const ctx = {
    commands: {
      register(value: CommandDefinition) {
        definition = value
        return () => {}
      },
    },
  } as unknown as Context

  registerPraxisCommand(ctx, async input => {
    seen = input
    return {
      initialized: true,
      active: input.action === 'enable',
      revision: 3,
    }
  })

  assert.ok(definition)
  assert.equal(definition.name, 'praxis')
  assert.equal(definition.input?.hint, '[enable|disable|status]')

  const controller = new AbortController()
  const agent = {
    session: {
      header: { cwd: '/workspace/repo' },
    },
  } as unknown as Agent

  const result = await definition.handler({
    commandId: 'cmd-test' as never,
    agent,
    rawInput: ' enable',
    attachments: [],
    signal: controller.signal,
  })

  assert.deepEqual(seen, {
    cwd: '/workspace/repo',
    action: 'enable',
    signal: controller.signal,
  })
  assert.equal(result.kind, 'success')
  assert.match(result.text ?? '', /enabled/)
})


test('invalid Praxis control input is rejected without running CLI', async () => {
  let definition: CommandDefinition | undefined
  let runs = 0
  const ctx = {
    commands: {
      register(value: CommandDefinition) {
        definition = value
        return () => {}
      },
    },
  } as unknown as Context

  registerPraxisCommand(ctx, async (): Promise<PraxisControlResult> => {
    runs += 1
    return { initialized: true, active: true, revision: 1 }
  })

  const agent = {
    session: {
      header: { cwd: '/workspace/repo' },
    },
  } as unknown as Agent

  const result = await definition!.handler({
    commandId: 'cmd-test' as never,
    agent,
    rawInput: ' maybe',
    attachments: [],
    signal: new AbortController().signal,
  })

  assert.equal(result.kind, 'error')
  assert.match(result.text ?? '', /\/praxis enable/)
  assert.equal(runs, 0)
})
