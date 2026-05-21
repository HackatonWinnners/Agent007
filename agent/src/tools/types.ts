import type { ReadFileCache } from '../state/readFileCache'
import type { Logger } from '../logger'

export type ToolContext = {
  cwd: string
  logger: Logger
  readFileCache: ReadFileCache
  agentId: string
  iteration: number
}

export type ToolResult<T = unknown> = { ok: true; data: T } | { ok: false; error: string }

export type Tool<I extends Record<string, unknown> = Record<string, unknown>, O = unknown> = {
  name: string
  description: string
  parameters: Record<string, unknown>
  concurrencySafe: boolean
  parse(args: Record<string, unknown>): I | { __error: string }
  call(input: I, ctx: ToolContext): Promise<ToolResult<O>>
  renderResult(result: ToolResult<O>): string
}
