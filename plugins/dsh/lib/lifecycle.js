import { createHash } from 'node:crypto';
import { createUserMessage } from '@deepseek-ai/dsh-llm';
import { renderRecoveryContext, renderRecoveryFallback } from "./context.js";
import { runRecoveryStatus } from "./praxis-cli.js";
const CONTEXT_SOURCE = { kind: 'praxis-dsh', form: 'instructions' };
function projectCwd(agent) {
    const cwd = agent.session.header.cwd;
    return typeof cwd === 'string' && cwd.trim().length > 0 ? cwd : undefined;
}
function contextDigest(text) {
    return createHash('sha256').update(text, 'utf8').digest('hex');
}
function contextMessage(text) {
    return createUserMessage({
        content: [{ type: 'text', text }],
        source: CONTEXT_SOURCE,
    });
}
export function registerPraxisLifecycle(ctx, run = runRecoveryStatus) {
    const lastContextDigest = new WeakMap();
    const pluginAbort = new AbortController();
    ctx.effect(() => () => {
        if (!pluginAbort.signal.aborted) {
            pluginAbort.abort(new Error('praxis-dsh plugin disposed'));
        }
    }, 'praxis-dsh: abort recovery subprocesses');
    const recover = async (agent, eventSignal) => {
        const cwd = projectCwd(agent);
        if (cwd === undefined)
            return undefined;
        const signal = eventSignal === undefined
            ? pluginAbort.signal
            : AbortSignal.any([eventSignal, pluginAbort.signal]);
        if (signal.aborted)
            return undefined;
        try {
            const snapshot = await run({
                cwd,
                host: 'dsh',
                conversationId: String(agent.id),
                signal,
            });
            if (signal.aborted)
                return undefined;
            return renderRecoveryContext(snapshot);
        }
        catch (error) {
            if (signal.aborted)
                return undefined;
            ctx.logger.warn(`praxis-dsh: automatic recovery failed: ${String(error)}`);
            return renderRecoveryFallback();
        }
    };
    ctx.on('agent/created', async ({ agent, signal }) => {
        const context = await recover(agent, signal);
        if (context === undefined) {
            lastContextDigest.delete(agent);
            return;
        }
        try {
            agent.inject(contextMessage(context));
            lastContextDigest.set(agent, contextDigest(context));
        }
        catch (error) {
            ctx.logger.warn(`praxis-dsh: failed to inject recovery context: ${String(error)}`);
        }
    });
    ctx.on('agent/pre-step', async ({ agent, messages, signal }, next) => {
        if (messages.length === 0)
            return next();
        const downstream = await next();
        if (downstream.kind === 'reject' || signal.aborted)
            return downstream;
        const context = await recover(agent, signal);
        if (context === undefined) {
            lastContextDigest.delete(agent);
            return downstream;
        }
        const digest = contextDigest(context);
        if (lastContextDigest.get(agent) === digest)
            return downstream;
        lastContextDigest.set(agent, digest);
        return {
            ...downstream,
            messages: [...downstream.messages, contextMessage(context)],
        };
    });
}
