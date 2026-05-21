import { readFileSync } from 'fs'
import fg from 'fast-glob'
import { resolve } from 'path'
import type { Tool } from './types'

type Input = { pattern: string; glob?: string; cwd?: string }
type Match = { path: string; line: number; text: string }

export const grepTool: Tool<Input, { matches: Match[] }> = {
  name: 'grep',
  description: 'Searches file contents for a regex (JS regex). Returns up to 200 file:line:text matches.',
  parameters: {
    type: 'object',
    properties: {
      pattern: { type: 'string' },
      glob: { type: 'string', description: 'Restrict search to files matching this glob; default **/*' },
      cwd: { type: 'string' },
    },
    required: ['pattern'],
  },
  concurrencySafe: true,
  parse(args) {
    if (typeof args.pattern !== 'string') return { __error: 'pattern required' }
    return {
      pattern: args.pattern,
      glob: typeof args.glob === 'string' ? args.glob : undefined,
      cwd: typeof args.cwd === 'string' ? args.cwd : undefined,
    }
  },
  async call(input, ctx) {
    const re = new RegExp(input.pattern)
    const base = input.cwd ?? ctx.cwd
    const pattern = input.glob ?? '**/*'
    const matches: Match[] = []
    const files = await fg(pattern, { cwd: base, onlyFiles: true, dot: false })
    for (const rel of files) {
      const p = resolve(base, rel)
      let raw: string
      try { raw = readFileSync(p, 'utf8') } catch { continue }
      const lines = raw.split('\n')
      for (let i = 0; i < lines.length; i++) {
        if (re.test(lines[i]!)) {
          matches.push({ path: p, line: i + 1, text: lines[i]! })
          if (matches.length >= 200) return { ok: true, data: { matches } }
        }
      }
    }
    return { ok: true, data: { matches } }
  },
  renderResult(r) {
    if (!r.ok) return `Error: ${r.error}`
    if (r.data.matches.length === 0) return '(no matches)'
    return r.data.matches.map(m => `${m.path}:${m.line}:${m.text}`).join('\n')
  },
}
