import type { Tool, ToolContext } from './types'
import { runLoop } from '../agent'
import type { Registry } from './registry'

type SubRole = 'planner' | 'implementer' | 'tester' | 'failure_analyst' | 'self_test_writer'
type RouterRole = 'primary_coder' | 'planner' | 'tester' | 'failure_analyst' | 'self_test_writer'

type Input = { role: SubRole; task: string; max_iterations?: number }

let subagentCounter = 0
let spawnDeps: {
  router: Parameters<typeof runLoop>[0]['router']
  registryFor(role: SubRole): Registry
  systemPromptFor(role: SubRole, taskHint: string): string
} | null = null

export function setSpawnContext(deps: NonNullable<typeof spawnDeps>): void {
  spawnDeps = deps
}

export const spawnSubagentTool: Tool<Input, { summary: string; iterations: number }> = {
  name: 'spawn_subagent',
  description:
    'Spawns a subagent with a fresh context. Allowed roles: planner, implementer, tester, failure_analyst, self_test_writer. Returns a text summary.',
  parameters: {
    type: 'object',
    properties: {
      role: { type: 'string', enum: ['planner', 'implementer', 'tester', 'failure_analyst', 'self_test_writer'] },
      task: { type: 'string' },
      max_iterations: { type: 'integer', minimum: 1, maximum: 60 },
    },
    required: ['role', 'task'],
  },
  concurrencySafe: false,
  parse(args) {
    const role = args.role
    if (role !== 'planner' && role !== 'implementer' && role !== 'tester' && role !== 'failure_analyst' && role !== 'self_test_writer') {
      return { __error: 'invalid role' }
    }
    if (typeof args.task !== 'string') return { __error: 'task required' }
    const mi = typeof args.max_iterations === 'number' ? args.max_iterations : 40
    return { role, task: args.task, max_iterations: mi }
  },
  async call(input, ctx: ToolContext) {
    if (!spawnDeps) return { ok: false, error: 'spawn_subagent not wired (setSpawnContext missing)' }
    if (ctx.agentId !== 'root') return { ok: false, error: 'subagents may not spawn other subagents' }
    const id = `sub-${++subagentCounter}-${input.role}`
    const registry = spawnDeps.registryFor(input.role)
    const result = await runLoop({
      agentId: id,
      router: spawnDeps.router,
      role: routerRoleFor(input.role),
      tools: registry,
      systemPrompt: spawnDeps.systemPromptFor(input.role, input.task),
      initialUserMessage: input.task,
      maxIterations: input.max_iterations ?? 40,
      cwd: ctx.cwd,
      logger: ctx.logger,
      readFileCache: ctx.readFileCache,
      autoCommit: () => {},
      onIterationStart: () => {},
    })
    return { ok: true, data: { summary: result.lastSummary ?? '(no summary)', iterations: result.iterations } }
  },
  renderResult(r) {
    if (!r.ok) return `Error: ${r.error}`
    return `subagent done in ${r.data.iterations} iterations:\n${r.data.summary}`
  },
}

function routerRoleFor(role: SubRole): RouterRole {
  if (role === 'implementer') return 'primary_coder'
  return role
}
