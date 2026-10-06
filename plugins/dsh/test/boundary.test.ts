import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'

import { adapterMetadata, apply, inject, name } from '../src/index.ts'


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


test('exports native Cordis plugin contract', () => {
  assert.equal(name, 'praxis-dsh')
  assert.deepEqual(inject, ['agents', 'commands', 'skills'])
  assert.equal(typeof apply, 'function')
})

test('declares both verified DSH API families and consistent development pins', async () => {
  const pluginPackage = JSON.parse(
    await readFile(new URL('../package.json', import.meta.url), 'utf8'),
  ) as { peerDependencies?: Record<string, string> }
  const rootPackage = JSON.parse(
    await readFile(new URL('../../../package.json', import.meta.url), 'utf8'),
  ) as { devDependencies?: Record<string, string> }

  const expected = {
    '@deepseek-ai/cordis': '4.0.5-alpha.1',
    '@deepseek-ai/dsh-agent': '0.2.1-alpha.1',
    '@deepseek-ai/dsh-commands': '0.2.1-alpha.1',
    '@deepseek-ai/dsh-llm': '0.2.1-alpha.1',
    '@deepseek-ai/dsh-skill': '0.2.1-alpha.1',
  }
  const rootManifest = JSON.parse(
    await readFile(new URL('../../../package.json', import.meta.url), 'utf8'),
  ) as { peerDependencies: Record<string, string> }
  const sdkVersion = rootPackage.devDependencies?.['@deepseek-ai/dsh-agent']
  assert.ok(sdkVersion === '0.2.0-rc.2' || sdkVersion === '0.2.1-alpha.1')
  for (const [pkg, previewVersion] of Object.entries(expected)) {
    const stableVersion = pkg === '@deepseek-ai/cordis' ? '4.0.4' : '0.2.0-rc.2'
    const range = `${stableVersion} || ${previewVersion}`
    assert.equal(pluginPackage.peerDependencies?.[pkg], range)
    assert.equal(rootManifest.peerDependencies[pkg], range)
    assert.equal(rootPackage.devDependencies?.[pkg],
      pkg === '@deepseek-ai/cordis'
        ? sdkVersion === '0.2.0-rc.2' ? '4.0.4' : previewVersion
        : sdkVersion)
  }
})
