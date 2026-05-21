import type { Tool, ToolContext, ToolResult } from './types'
import type { ToolSchema } from '../models/types'

export type Registry = {
  list(): Tool[]
  byName(name: string): Tool | undefined
  schemas(): ToolSchema[]
  invoke(name: string, args: Record<string, unknown>, ctx: ToolContext): Promise<{ rendered: string; raw: ToolResult }>
}

export function createRegistry(tools: Tool[]): Registry {
  const map = new Map(tools.map(t => [t.name, t] as const))
  return {
    list: () => tools,
    byName: n => map.get(n),
    schemas: () =>
      tools.map(t => ({ name: t.name, description: t.description, parameters: t.parameters })),
    async invoke(name, args, ctx) {
      const tool = map.get(name)
      if (!tool) {
        return { rendered: `Error: unknown tool ${name}`, raw: { ok: false, error: 'unknown tool' } }
      }
      const parsed = tool.parse(args)
      if ('__error' in parsed) {
        const errMsg = typeof parsed.__error === 'string' ? parsed.__error : 'invalid input'
        const r: ToolResult = { ok: false, error: errMsg }
        return { rendered: tool.renderResult(r), raw: r }
      }
      const out = await tool.call(parsed as never, ctx)
      return { rendered: tool.renderResult(out), raw: out }
    },
  }
}
