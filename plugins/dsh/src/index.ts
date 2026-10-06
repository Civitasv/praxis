import type { Context } from '@deepseek-ai/cordis'
import type {} from '@deepseek-ai/dsh-agent'
import type {} from '@deepseek-ai/dsh-skill'

export const adapterMetadata = {
  name: 'praxis-dsh',
  harness: 'deepseek-harness',
  apiVersion: 1,
} as const

export const name = 'praxis-dsh'
export const inject = ['agents', 'skills'] as const

export function apply(ctx: Context): void {
  void ctx
}
