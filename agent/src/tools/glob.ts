import fg from 'fast-glob'
import { resolve } from 'path'
import type { Tool } from './types'

type Input = { pattern: string; cwd?: string }

export const globTool: Tool<Input, { paths: string[] }> = {
  name: 'glob',
  description: 'Returns absolute file paths matching a glob pattern under cwd (or override). Sorted, max 1000.',
  parameters: {
    type: 'object',
    properties: { pattern: { type: 'string' }, cwd: { type: 'string' } },
    required: ['pattern'],
  },
  concurrencySafe: true,
  parse(args) {
    if (typeof args.pattern !== 'string') return { __error: 'pattern required' }
    return { pattern: args.pattern, cwd: typeof args.cwd === 'string' ? args.cwd : undefined }
  },
  async call(input, ctx) {
    const base = input.cwd ?? ctx.cwd
    const matches = await fg(input.pattern, { cwd: base, onlyFiles: true, dot: false })
    const absolute = matches.map(p => resolve(base, p)).slice(0, 1000)
    absolute.sort()
    return { ok: true, data: { paths: absolute } }
  },
  renderResult(r) {
    if (!r.ok) return `Error: ${r.error}`
    return r.data.paths.length === 0 ? '(no matches)' : r.data.paths.join('\n')
  },
}
