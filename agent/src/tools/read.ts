import { readFileSync, existsSync } from 'fs'
import type { Tool } from './types'

type Input = { file_path: string; offset?: number; limit?: number }

export const readTool: Tool<Input, { content: string }> = {
  name: 'read',
  description:
    'Reads a file from disk. Returns content with line-number prefix "N\\tline". Use offset/limit to read partial files.',
  parameters: {
    type: 'object',
    properties: {
      file_path: { type: 'string', description: 'Absolute file path.' },
      offset: { type: 'integer', minimum: 0 },
      limit: { type: 'integer', minimum: 1 },
    },
    required: ['file_path'],
  },
  concurrencySafe: true,
  parse(args) {
    const fp = args.file_path
    if (typeof fp !== 'string' || fp.length === 0) {
      return { __error: 'file_path is required (absolute path string). Example: read(file_path="/abs/path/file.txt")' }
    }
    return {
      file_path: fp,
      offset: typeof args.offset === 'number' ? args.offset : undefined,
      limit: typeof args.limit === 'number' ? args.limit : undefined,
    }
  },
  async call(input, ctx) {
    if (!existsSync(input.file_path)) return { ok: false, error: `File not found: ${input.file_path}` }
    let raw: string
    try {
      raw = readFileSync(input.file_path, 'utf8')
    } catch (e) {
      const msg = (e as Error & { code?: string }).code === 'EISDIR'
        ? `Path is a directory, not a file: ${input.file_path}. Use the glob tool to list contents.`
        : `Could not read file ${input.file_path}: ${(e as Error).message}`
      return { ok: false, error: msg }
    }
    const rawLines = raw.split('\n')
    // Drop the trailing empty element produced by files that end with a newline,
    // so "hello\nworld\n" gives 2 numbered lines, not 3.
    const lines = rawLines.length > 0 && rawLines[rawLines.length - 1] === ''
      ? rawLines.slice(0, -1)
      : rawLines
    const start = input.offset ?? 0
    const end = input.limit ? Math.min(lines.length, start + input.limit) : lines.length
    const sliced = lines.slice(start, end)
    const content = sliced.map((l, i) => `${start + i + 1}\t${l}`).join('\n') + (sliced.length > 0 ? '\n' : '')
    ctx.readFileCache.set(input.file_path, raw)
    return { ok: true, data: { content } }
  },
  renderResult(r) {
    return r.ok ? r.data.content : `Error: ${r.error}`
  },
}
