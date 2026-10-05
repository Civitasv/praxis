import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'

import { adapterMetadata } from '../src/index.ts'


test('exports stable DSH adapter metadata', () => {
  assert.deepEqual(adapterMetadata, {
    name: 'praxis-dsh',
    harness: 'deepseek-harness',
    apiVersion: 1,
  })
})

test('adapter seam does not reach into neutral or private implementation paths', async () => {
  const source = await readFile(new URL('../src/index.ts', import.meta.url), 'utf8')
  const forbidden = ['../../praxis', '@praxis/internal-', 'praxis/']
  for (const fragment of forbidden) {
    assert.equal(source.includes(fragment), false, `forbidden adapter dependency: ${fragment}`)
  }
})
