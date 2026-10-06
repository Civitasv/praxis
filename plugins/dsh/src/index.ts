import type { Context } from '@deepseek-ai/cordis'
import type {} from '@deepseek-ai/dsh-agent'
import type {} from '@deepseek-ai/dsh-commands'
import type {} from '@deepseek-ai/dsh-skill'

import { registerPraxisCommand } from './command.ts'
import { registerPraxisLifecycle } from './lifecycle.ts'
import { registerPraxisSkill } from './skill.ts'

export const adapterMetadata = {
  name: 'praxis-dsh',
  harness: 'deepseek-harness',
  apiVersion: 1,
} as const

export const name = 'praxis-dsh'
export const inject = ['agents', 'commands', 'skills'] as const

export function apply(ctx: Context): void {
  registerPraxisSkill(ctx)
  registerPraxisCommand(ctx)
  registerPraxisLifecycle(ctx)
}
