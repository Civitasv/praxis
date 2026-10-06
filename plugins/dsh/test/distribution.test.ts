import assert from 'node:assert/strict'
import { access, readFile } from 'node:fs/promises'
import { test } from 'node:test'


async function missing(url: URL): Promise<boolean> {
  try {
    await access(url)
    return false
  } catch {
    return true
  }
}


test('DSH package keeps shared Skill and neutral core single-source', async () => {
  assert.equal(await missing(new URL('../skills/', import.meta.url)), true)
  assert.equal(await missing(new URL('../praxis/', import.meta.url)), true)

  const skill = await readFile(new URL('../src/skill.ts', import.meta.url), 'utf8')
  assert.match(skill, /skills\/praxis\/SKILL\.md/)
  assert.equal(skill.includes('plugins/dsh/skills'), false)
})


test('DSH subprocess bridge uses direct execFile and never enables shell execution', async () => {
  const source = await readFile(new URL('../src/praxis-cli.ts', import.meta.url), 'utf8')
  assert.match(source, /execFile\(/)
  assert.match(source, /shell:\s*false/)
  assert.equal(/\bexec\s*\(/.test(source), false)
  assert.equal(source.includes('shell: true'), false)
})


test('neutral Python core contains no DeepSeek Harness or Cordis dependencies', async () => {
  const names = [
    '__init__.py',
    '__main__.py',
    'cli.py',
    'decisions.py',
    'fingerprints.py',
    'locking.py',
    'project.py',
    'project_map.py',
    'recovery.py',
    'state.py',
    'tasks.py',
  ]
  for (const name of names) {
    const source = (
      await readFile(new URL(`../../../praxis/${name}`, import.meta.url), 'utf8')
    ).toLowerCase()
    assert.equal(source.includes('deepseek'), false, name)
    assert.equal(source.includes('cordis'), false, name)
    assert.equal(source.includes('plugins.dsh'), false, name)
  }
})


test('root development pins include the DSH preview type dependency closure', async () => {
  const root = JSON.parse(
    await readFile(new URL('../../../package.json', import.meta.url), 'utf8'),
  ) as { devDependencies?: Record<string, string> }

  const expected = {
    '@deepseek-ai/cordis': '4.0.5-alpha.1',
    '@deepseek-ai/dsh-agent': '0.2.1-alpha.1',
    '@deepseek-ai/dsh-attachment': '0.2.1-alpha.1',
    '@deepseek-ai/dsh-brand': '0.2.1-alpha.1',
    '@deepseek-ai/dsh-llm': '0.2.1-alpha.1',
    '@deepseek-ai/dsh-skill': '0.2.1-alpha.1',
  }
  for (const [pkg, version] of Object.entries(expected)) {
    assert.equal(root.devDependencies?.[pkg], version, pkg)
  }
})


test('DSH CI explicitly provisions Python 3.10 for the real TypeScript to Python bridge', async () => {
  const workflow = await readFile(
    new URL('../../../.github/workflows/ci.yml', import.meta.url),
    'utf8',
  )
  const typescriptJob = workflow.split('\n  typescript:\n')[1] ?? ''
  assert.match(typescriptJob, /name: TypeScript \/ DSH/)
  assert.match(typescriptJob, /name: Set up Python 3\.10/)
  assert.match(typescriptJob, /python-version:\s*['"]3\.10['"]/)
  assert.match(typescriptJob, /run: pnpm typecheck/)
  assert.match(typescriptJob, /run: pnpm test:dsh/)
})
