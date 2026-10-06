import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
export const sharedSkillDirectory = fileURLToPath(new URL('../../../skills/praxis/', import.meta.url));
export const sharedSkillPath = fileURLToPath(new URL('../../../skills/praxis/SKILL.md', import.meta.url));
export function registerPraxisSkill(ctx) {
    const content = readFileSync(sharedSkillPath, 'utf8');
    return ctx.skills.register({
        name: 'praxis',
        description: 'Build software with AI while keeping consequential engineering judgment visible.',
        source: 'bundled',
        provider: 'praxis-dsh',
        path: sharedSkillPath,
        resourceBase: { kind: 'directory', path: sharedSkillDirectory },
        invocation: { modelInvocable: true, userInvocable: true },
        content,
    });
}
