import type { ChatMessage, ToolCall } from './models/types'
import type { Registry } from './tools/registry'
import type { ReadFileCache } from './state/readFileCache'
import type { Logger } from './logger'
import { TOOL_BATCH_PARALLEL_LIMIT } from './config'

export type Role = 'primary_coder' | 'planner' | 'tester' | 'failure_analyst' | 'self_test_writer'

type Router = {
  complete(req: {
    role: Role
    messages: ChatMessage[]
    tools?: { name: string; description: string; parameters: Record<string, unknown> }[]
  }): Promise<{ content: string | null; toolCalls: ToolCall[] }>
}

export type LoopInputs = {
  agentId: string
  router: Router
  role: Role
  tools: Registry
  systemPrompt: string
  initialUserMessage: string
  maxIterations: number
  cwd: string
  logger: Logger
  readFileCache: ReadFileCache
  autoCommit(opts: { cwd: string; message: string }): void
  onIterationStart(iter: number): void
}

export type LoopResult = {
  iterations: number
  halted: boolean
  lastSummary: string | null
}

export async function runLoop(inp: LoopInputs): Promise<LoopResult> {
  const messages: ChatMessage[] = [
    { role: 'system', content: inp.systemPrompt },
    { role: 'user', content: inp.initialUserMessage },
  ]
  inp.logger.prompt({ role: 'system', content: inp.systemPrompt.slice(0, 1000), target: inp.agentId })
  inp.logger.prompt({ role: 'user', content: inp.initialUserMessage, target: inp.agentId })

  let halted = false
  let lastSummary: string | null = null
  let lastToolCallHashes: string[] = []
  let iteration = 0

  for (iteration = 0; iteration < inp.maxIterations; iteration++) {
    inp.onIterationStart(iteration)

    const response = await inp.router.complete({
      role: inp.role,
      messages,
      tools: inp.tools.schemas(),
    })

    const summary = summarize(response.content, response.toolCalls)
    lastSummary = summary
    inp.logger.decision({ iteration, agentId: inp.agentId, summary })

    messages.push({ role: 'assistant', content: response.content, toolCalls: response.toolCalls })

    if (!response.toolCalls || response.toolCalls.length === 0) {
      inp.autoCommit({ cwd: inp.cwd, message: `iter ${iteration} (${inp.agentId}): ${summary}` })
      break
    }

    // cycle detection
    const sig = response.toolCalls.map(tc => `${tc.name}:${JSON.stringify(tc.args).slice(0, 200)}`).join('|')
    lastToolCallHashes.push(sig)
    if (lastToolCallHashes.length > 3) lastToolCallHashes.shift()
    const stuck =
      lastToolCallHashes.length === 3 &&
      lastToolCallHashes[0] === lastToolCallHashes[1] &&
      lastToolCallHashes[1] === lastToolCallHashes[2]

    if (stuck) {
      inp.logger.intervention({
        type: 'cycle-detected',
        what: 'pruned last 4 messages and forced retry',
        why: 'identical tool calls for 3 iterations',
        filesAffected: [],
        touchedFinalCode: false,
      })
      messages.splice(-4)
      lastToolCallHashes = []
    }

    const ctx = {
      cwd: inp.cwd,
      logger: inp.logger,
      readFileCache: inp.readFileCache,
      agentId: inp.agentId,
      iteration,
    }

    const safe: ToolCall[] = []
    const unsafe: ToolCall[] = []
    for (const tc of response.toolCalls) {
      const t = inp.tools.byName(tc.name)
      if (t && t.concurrencySafe) safe.push(tc)
      else unsafe.push(tc)
    }

    const safeBatch = safe.slice(0, TOOL_BATCH_PARALLEL_LIMIT)
    const safeResults = await Promise.all(
      safeBatch.map(tc => inp.tools.invoke(tc.name, tc.args, ctx).then(r => ({ tc, r }))),
    )
    const unsafeResults: { tc: ToolCall; r: { rendered: string; raw: { ok: boolean } } }[] = []
    for (const tc of unsafe) {
      const r = await inp.tools.invoke(tc.name, tc.args, ctx)
      unsafeResults.push({ tc, r })
    }
    for (const { tc, r } of [...safeResults, ...unsafeResults]) {
      messages.push({ role: 'tool', toolCallId: tc.id, content: r.rendered })
      if (tc.name === 'submit_done') halted = true
    }

    inp.autoCommit({ cwd: inp.cwd, message: `iter ${iteration} (${inp.agentId}): ${summary}` })

    if (halted) break
  }

  return { iterations: iteration + 1, halted, lastSummary }
}

function summarize(content: string | null, toolCalls: ToolCall[]): string {
  const trimmed = content?.trim() ?? ''
  const toolPart = toolCalls && toolCalls.length > 0
    ? ` tools=[${toolCalls.map(t => `${t.name}(${JSON.stringify(t.args).slice(0, 120)})`).join(' | ')}]`
    : ''
  const textPart = trimmed.length > 0 ? trimmed.slice(0, 200).replace(/\s+/g, ' ') : ''
  return (textPart + toolPart).trim() || '(no action)'
}
