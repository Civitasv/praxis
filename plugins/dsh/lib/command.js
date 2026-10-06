import { runPraxisControl } from "./praxis-cli.js";
export function parsePraxisCommand(rawInput) {
    const value = rawInput.trim().toLowerCase();
    if (value === '')
        return 'status';
    if (value === 'enable' || value === 'disable' || value === 'status')
        return value;
    return undefined;
}
function renderResult(action, result) {
    if (action === 'status') {
        if (!result.initialized)
            return { kind: 'success', text: 'Praxis is not initialized for this project.' };
        return { kind: 'success', text: `Praxis is ${result.active ? 'enabled' : 'disabled'}.` };
    }
    return {
        kind: 'success',
        text: `Praxis ${result.active ? 'enabled' : 'disabled'} for this project.`,
    };
}
export function registerPraxisCommand(ctx, run = runPraxisControl) {
    ctx.commands.register({
        name: 'praxis',
        description: 'Enable, disable, or inspect Praxis for this project',
        input: { hint: '[enable|disable|status]' },
        handler: async ({ agent, rawInput, signal }) => {
            const action = parsePraxisCommand(rawInput);
            if (action === undefined) {
                return {
                    kind: 'error',
                    text: 'Usage: /praxis enable | /praxis disable | /praxis status',
                };
            }
            const cwd = agent.session.header.cwd;
            if (typeof cwd !== 'string' || !cwd.trim()) {
                return { kind: 'error', text: 'Praxis cannot resolve the current project directory.' };
            }
            try {
                return renderResult(action, await run({ cwd, action, signal }));
            }
            catch (error) {
                return {
                    kind: 'error',
                    text: `Praxis control failed: ${error instanceof Error ? error.message : String(error)}`,
                };
            }
        },
    });
}
