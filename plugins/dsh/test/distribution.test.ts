import assert from 'node:assert/strict'
import { access, cp, mkdir, mkdtemp, readFile, rm, symlink } from 'node:fs/promises'
import { execFile } from 'node:child_process'
import { createRequire } from 'node:module'
import { tmpdir } from 'node:os'
import { dirname, join } from 'node:path'
import { promisify } from 'node:util'
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


test('root development pins include the selected DSH type dependency closure', async () => {
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
  const sdkVersion = root.devDependencies?.['@deepseek-ai/dsh-agent']
  assert.ok(sdkVersion === '0.2.0-rc.2' || sdkVersion === '0.2.1-alpha.1')
  for (const [pkg, version] of Object.entries(expected)) {
    const selected: string = sdkVersion === '0.2.0-rc.2'
      ? pkg === '@deepseek-ai/cordis' ? '4.0.4' : sdkVersion
      : version
    assert.equal(root.devDependencies?.[pkg], selected, pkg)
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


test('installed package imports JavaScript from node_modules and resolves the shared skill', async () => {
  const fixture = await mkdtemp(join(tmpdir(), 'praxis-installed-'))
  try {
    const installed = join(fixture, 'node_modules', 'praxis')
    await mkdir(installed, { recursive: true })
    await cp(new URL('../../../package.json', import.meta.url), join(installed, 'package.json'))
    await cp(new URL('../', import.meta.url), join(installed, 'plugins', 'dsh'), { recursive: true })
    await cp(new URL('../../../skills/', import.meta.url), join(installed, 'skills'), { recursive: true })
    const require = createRequire(import.meta.url)
    const llm = dirname(require.resolve('@deepseek-ai/dsh-llm/package.json'))
    await mkdir(join(fixture, 'node_modules', '@deepseek-ai'), { recursive: true })
    await symlink(llm, join(fixture, 'node_modules', '@deepseek-ai', 'dsh-llm'), 'dir')
    await promisify(execFile)(process.execPath, ['--input-type=module', '-e', `
      import assert from 'node:assert/strict';
      const plugin = await import('praxis');
      assert.equal(plugin.name, 'praxis-dsh');
      assert.equal(typeof plugin.apply, 'function');
      const { registerPraxisSkill } = await import('./node_modules/praxis/plugins/dsh/lib/skill.js');
      let content;
      registerPraxisSkill({ skills: { register(skill) { content = skill.content; return () => {}; } } });
      assert.match(content, /Praxis Tutor Skill/);
    `], { cwd: fixture })
  } finally {
    await rm(fixture, { recursive: true, force: true })
  }
})
