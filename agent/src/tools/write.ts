import { writeFileSync, existsSync, mkdirSync } from 'fs'
import { dirname } from 'path'
import type { Tool } from './types'

type Input = { file_path: string; content: string; overwrite?: boolean }

export const writeTool: Tool<Input, { bytes: number; created: boolean }> = {
  name: 'write',
  description: 'Creates a new file with the given content. Refuses to overwrite an existing file unless overwrite=true.',
  parameters: {
    type: 'object',
    properties: {
      file_path: { type: 'string' },
      content: { type: 'string' },
      overwrite: { type: 'boolean' },
    },
    required: ['file_path', 'content'],
  },
  concurrencySafe: false,
  parse(args) {
    if (typeof args.file_path !== 'string') return { __error: 'file_path required' }
    if (typeof args.content !== 'string') return { __error: 'content required' }
    return { file_path: args.file_path, content: args.content, overwrite: args.overwrite === true }
  },
  async call(input, ctx) {
    const exists = existsSync(input.file_path)
    if (exists && !input.overwrite) {
      return { ok: false, error: `File exists: ${input.file_path}. Set overwrite=true to replace, or use edit.` }
    }
    mkdirSync(dirname(input.file_path), { recursive: true })
    writeFileSync(input.file_path, input.content, 'utf8')
    ctx.readFileCache.set(input.file_path, input.content)
    return { ok: true, data: { bytes: Buffer.byteLength(input.content, 'utf8'), created: !exists } }
  },
  renderResult(r) {
    if (!r.ok) return `Error: ${r.error}`
    return `${r.data.created ? 'Created' : 'Overwrote'} file (${r.data.bytes} bytes).`
  },
}
