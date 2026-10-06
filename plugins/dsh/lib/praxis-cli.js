import { execFile } from 'node:child_process';
import { delimiter } from 'node:path';
import { fileURLToPath } from 'node:url';
export const praxisRepositoryRoot = fileURLToPath(new URL('../../../', import.meta.url));
export class PraxisCliError extends Error {
}
export class PraxisCliProcessError extends PraxisCliError {
    stdout;
    stderr;
    constructor(message, stdout, stderr) {
        super(message);
        this.name = 'PraxisCliProcessError';
        this.stdout = stdout;
        this.stderr = stderr;
    }
}
export class PraxisCliProtocolError extends PraxisCliError {
    constructor(message) {
        super(message);
        this.name = 'PraxisCliProtocolError';
    }
}
function pythonRuntime(cwd, pythonExecutable, signal, runtime) {
    const configuredPython = pythonExecutable
        ?? (runtime.env.PRAXIS_PYTHON?.trim() ? runtime.env.PRAXIS_PYTHON : undefined);
    const command = configuredPython ?? (runtime.platform === 'win32' ? 'py' : 'python3');
    const prefix = [
        ...configuredPython === undefined && runtime.platform === 'win32' ? ['-3'] : [],
        '-m',
        'praxis',
    ];
    const inheritedPythonPath = runtime.env.PYTHONPATH;
    const pythonPath = inheritedPythonPath
        ? `${praxisRepositoryRoot}${delimiter}${inheritedPythonPath}`
        : praxisRepositoryRoot;
    return {
        command,
        prefix,
        options: {
            cwd,
            env: { ...runtime.env, PYTHONPATH: pythonPath },
            shell: false,
            ...signal === undefined ? {} : { signal },
        },
    };
}
export function buildRecoveryInvocation(input, runtime = { platform: process.platform, env: process.env }) {
    if (!input.cwd.trim())
        throw new PraxisCliProtocolError('cwd must be non-empty');
    if (!input.host.trim())
        throw new PraxisCliProtocolError('host must be non-empty');
    if (input.conversationId !== undefined && !input.conversationId.trim()) {
        throw new PraxisCliProtocolError('conversationId must be non-empty when provided');
    }
    const python = pythonRuntime(input.cwd, input.pythonExecutable, input.signal, runtime);
    const args = [
        ...python.prefix,
        'recovery-status',
        '--cwd',
        input.cwd,
        '--host',
        input.host,
    ];
    if (input.conversationId !== undefined) {
        args.push('--conversation-id', input.conversationId);
    }
    return {
        command: python.command,
        args,
        options: python.options,
    };
}
export function buildControlInvocation(input, runtime = { platform: process.platform, env: process.env }) {
    if (!input.cwd.trim())
        throw new PraxisCliProtocolError('cwd must be non-empty');
    const python = pythonRuntime(input.cwd, input.pythonExecutable, input.signal, runtime);
    return {
        command: python.command,
        args: [...python.prefix, input.action, '--cwd', input.cwd],
        options: python.options,
    };
}
const executeCommand = async (command, args, options) => {
    return await new Promise((resolve, reject) => {
        execFile(command, [...args], {
            cwd: options.cwd,
            env: options.env,
            shell: false,
            ...options.signal === undefined ? {} : { signal: options.signal },
            encoding: 'utf8',
            maxBuffer: 1024 * 1024,
        }, (error, stdout, stderr) => {
            if (error !== null) {
                reject(new PraxisCliProcessError(`Praxis CLI failed: ${error.message}`, String(stdout), String(stderr)));
                return;
            }
            resolve({ stdout: String(stdout), stderr: String(stderr) });
        });
    });
};
function isRecord(value) {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function isStringArray(value) {
    return Array.isArray(value) && value.every(item => typeof item === 'string');
}
function isTask(value) {
    if (!isRecord(value))
        return false;
    if (typeof value.id !== 'string' || typeof value.host !== 'string')
        return false;
    if (typeof value.stage !== 'string' || typeof value.status !== 'string')
        return false;
    if (value.conversation_id !== undefined && typeof value.conversation_id !== 'string')
        return false;
    if (value.title !== undefined && typeof value.title !== 'string')
        return false;
    return true;
}
function isDecision(value) {
    if (!isRecord(value))
        return false;
    return (typeof value.id === 'string'
        && typeof value.task_id === 'string'
        && typeof value.class === 'string'
        && value.status === 'open'
        && typeof value.title === 'string'
        && Number.isSafeInteger(value.revision));
}
function parseSnapshot(value) {
    if (!isRecord(value))
        throw new PraxisCliProtocolError('recovery must be an object');
    if (typeof value.initialized !== 'boolean' || typeof value.enabled !== 'boolean') {
        throw new PraxisCliProtocolError('recovery activation fields are invalid');
    }
    if (value.revision !== null && !Number.isSafeInteger(value.revision)) {
        throw new PraxisCliProtocolError('recovery revision is invalid');
    }
    const resolution = value.task_resolution;
    if (!isRecord(resolution))
        throw new PraxisCliProtocolError('task_resolution is invalid');
    const kind = resolution.kind;
    if (kind !== 'none'
        && kind !== 'exact'
        && kind !== 'exact_ambiguous'
        && kind !== 'candidate'
        && kind !== 'candidate_ambiguous') {
        throw new PraxisCliProtocolError('task_resolution kind is invalid');
    }
    if (!Array.isArray(resolution.candidates) || !resolution.candidates.every(isTask)) {
        throw new PraxisCliProtocolError('task_resolution candidates are invalid');
    }
    if (resolution.task !== null && !isTask(resolution.task)) {
        throw new PraxisCliProtocolError('task_resolution task is invalid');
    }
    if ((kind === 'exact' || kind === 'candidate') && resolution.task === null) {
        throw new PraxisCliProtocolError('resolved task is missing');
    }
    if ((kind === 'none' || kind === 'exact_ambiguous' || kind === 'candidate_ambiguous') && resolution.task !== null) {
        throw new PraxisCliProtocolError('ambiguous/empty recovery cannot carry a selected task');
    }
    if (!Array.isArray(value.open_decisions) || !value.open_decisions.every(isDecision)) {
        throw new PraxisCliProtocolError('open_decisions are invalid');
    }
    if (!isStringArray(value.blocked_scopes)) {
        throw new PraxisCliProtocolError('blocked_scopes are invalid');
    }
    const model = value.project_model;
    if (!isRecord(model)
        || !isStringArray(model.stale_sections)
        || !isStringArray(model.unknown_sections)) {
        throw new PraxisCliProtocolError('project_model recovery summary is invalid');
    }
    return {
        initialized: value.initialized,
        enabled: value.enabled,
        revision: value.revision,
        task_resolution: resolution,
        open_decisions: value.open_decisions,
        blocked_scopes: value.blocked_scopes,
        project_model: {
            stale_sections: model.stale_sections,
            unknown_sections: model.unknown_sections,
        },
    };
}
export async function runRecoveryStatus(input, execute = executeCommand) {
    const invocation = buildRecoveryInvocation(input);
    const result = await execute(invocation.command, invocation.args, invocation.options);
    let payload;
    try {
        payload = JSON.parse(result.stdout);
    }
    catch {
        throw new PraxisCliProtocolError('Praxis CLI returned malformed JSON');
    }
    if (!isRecord(payload) || payload.ok !== true) {
        throw new PraxisCliProtocolError('Praxis CLI did not return a successful recovery response');
    }
    return parseSnapshot(payload.recovery);
}
export async function runPraxisControl(input, execute = executeCommand) {
    const invocation = buildControlInvocation(input);
    const result = await execute(invocation.command, invocation.args, invocation.options);
    let payload;
    try {
        payload = JSON.parse(result.stdout);
    }
    catch {
        throw new PraxisCliProtocolError('Praxis CLI returned malformed JSON');
    }
    if (!isRecord(payload) || payload.ok !== true || typeof payload.active !== 'boolean') {
        throw new PraxisCliProtocolError('Praxis CLI did not return a successful control response');
    }
    const state = payload.state;
    if (state !== null && !isRecord(state)) {
        throw new PraxisCliProtocolError('Praxis control state is invalid');
    }
    const revision = state === null ? null : state.revision;
    if (revision !== null && !Number.isSafeInteger(revision)) {
        throw new PraxisCliProtocolError('Praxis control revision is invalid');
    }
    return {
        initialized: state !== null,
        active: payload.active,
        revision: revision,
    };
}
