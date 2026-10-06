import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { test } from 'node:test'

import { Context } from '@deepseek-ai/cordis'
import SkillRegistry from '@deepseek-ai/dsh-skill'

import { registerPraxisSkill, sharedSkillDirectory, sharedSkillPath } from '../src/skill.ts'


test('registers the shared Praxis Skill without copying it into the DSH package', async () => {
  const ctx = new Context()
  await ctx.plugin(SkillRegistry)

  const dispose = registerPraxisSkill(ctx)
  const skill = await ctx.skills.get('praxis')

  assert.ok(skill)
  assert.equal(skill.name, 'praxis')
  assert.equal(skill.description, 'Build software with AI while keeping consequential engineering judgment visible.')
  assert.deepEqual(skill.invocation, { modelInvocable: true, userInvocable: true })
  assert.equal(skill.provider, 'praxis-dsh')
  assert.equal(skill.source, 'bundled')
  assert.equal(skill.path, sharedSkillPath)
  assert.deepEqual(skill.resourceBase, { kind: 'directory', path: sharedSkillDirectory })
  assert.equal(skill.content, await readFile(sharedSkillPath, 'utf8'))

  dispose()
  assert.equal(await ctx.skills.get('praxis'), undefined)
  await ctx.dispose()
})


test('shared Skill path resolves outside plugins/dsh and no copy is required', () => {
  assert.match(sharedSkillPath, /[\\/]skills[\\/]praxis[\\/]SKILL\.md$/)
  assert.equal(sharedSkillPath.includes('plugins/dsh/skills'), false)
})
