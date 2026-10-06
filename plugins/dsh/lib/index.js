import { registerPraxisCommand } from "./command.js";
import { registerPraxisLifecycle } from "./lifecycle.js";
import { registerPraxisSkill } from "./skill.js";
export const adapterMetadata = {
    name: 'praxis-dsh',
    harness: 'deepseek-harness',
    apiVersion: 1,
};
export const name = 'praxis-dsh';
export const inject = ['agents', 'commands', 'skills'];
export function apply(ctx) {
    registerPraxisSkill(ctx);
    registerPraxisCommand(ctx);
    registerPraxisLifecycle(ctx);
}
