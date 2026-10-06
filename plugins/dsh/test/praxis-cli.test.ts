import assert from 'node:assert/strict'
import { mkdtemp, rm } from 'node:fs/promises'
import { delimiter, join } from 'node:path'
import { tmpdir } from 'node:os'
import { test } from 'node:test'

import {
  PraxisCliProtocolError,
  buildRecoveryInvocation,
  praxisRepositoryRoot,
  runRecoveryStatus,
} from '../src/praxis-cli.ts'


test('builds recovery-status as direct argv with repository PYTHONPATH prefix', () => {
  const invocation = buildRecoveryInvocation({
    cwd: '/tmp/project with spaces',
    host: 'dsh',
    conversationId: 'session value',
    pythonExecutable: 'python-test',
  })

  assert.equal(invocation.command, 'python-test')
  assert.deepEqual(invocation.args, [
    '-m',
    'praxis',
    'recovery-status',
    '--cwd',
    '/tmp/project with spaces',
    '--host',
    'dsh',
    '--conversation-id',
    'session value',
  ])
  assert.equal(invocation.options.cwd, '/tmp/project with spaces')
  assert.equal(invocation.options.shell, false)
  assert.ok(invocation.options.env.PYTHONPATH)
  assert.equal(invocation.options.env.PYTHONPATH.split(delimiter)[0], praxisRepositoryRoot)
})


test('passes cwd and session only as argv and parses structured recovery JSON', async () => {
  let captured: unknown[] | undefined
  const snapshot = {
    initialized: true,
    enabled: true,
    revision: 3,
    task_resolution: { kind: 'none', task: null, candidates: [] },
    open_decisions: [],
    blocked_scopes: [],
    project_model: { stale_sections: [], unknown_sections: [] },
  }

  const result = await runRecoveryStatus(
    { cwd: '/tmp/project; echo bad', host: 'dsh', conversationId: 's && bad' },
    async (command, args, options) => {
      captured = [command, args, options]
      return { stdout: JSON.stringify({ ok: true, recovery: snapshot }) + '\n', stderr: '' }
    },
  )

  assert.deepEqual(result, snapshot)
  assert.equal(captured?.[0], 'python3')
  assert.deepEqual(captured?.[1], [
    '-m', 'praxis', 'recovery-status',
    '--cwd', '/tmp/project; echo bad',
    '--host', 'dsh',
    '--conversation-id', 's && bad',
  ])
  assert.equal((captured?.[2] as { shell: boolean }).shell, false)
})


test('rejects malformed or unsuccessful CLI protocol responses', async () => {
  await assert.rejects(
    runRecoveryStatus(
      { cwd: '/tmp/project', host: 'dsh' },
      async () => ({ stdout: 'not-json', stderr: '' }),
    ),
    PraxisCliProtocolError,
  )

  await assert.rejects(
    runRecoveryStatus(
      { cwd: '/tmp/project', host: 'dsh' },
      async () => ({ stdout: JSON.stringify({ ok: false, error: { code: 'bad', message: 'broken' } }), stderr: '' }),
    ),
    PraxisCliProtocolError,
  )
})


test('real TypeScript to Python recovery-status integration is silent-state safe', async () => {
  const root = await mkdtemp(join(tmpdir(), 'praxis-dsh-cli-'))
  try {
    const result = await runRecoveryStatus({ cwd: root, host: 'dsh', conversationId: 'session-1' })
    assert.equal(result.initialized, false)
    assert.equal(result.enabled, false)
    assert.equal(result.revision, null)
    assert.deepEqual(result.task_resolution, { kind: 'none', task: null, candidates: [] })
  } finally {
    await rm(root, { recursive: true, force: true })
  }
})
