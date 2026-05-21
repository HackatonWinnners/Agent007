import { readFileSync, writeFileSync, existsSync, statSync } from 'fs'
import type { Tool } from './types'

type Input = { file_path: string; old_string: string; new_string: string; replace_all?: boolean }

export const editTool: Tool<Input, { matches: number; replaceAll: boolean }> = {
  name: 'edit',
  description:
    'Performs exact string replacement in a file. Requires the file to have been read first in this session. If old_string occurs more than once, replace_all must be true. Use the smallest unique old_string.',
  parameters: {
    type: 'object',
    properties: {
      file_path: { type: 'string' },
      old_string: { type: 'string' },
      new_string: { type: 'string' },
      replace_all: { type: 'boolean' },
    },
    required: ['file_path', 'old_string', 'new_string'],
  },
  concurrencySafe: false,
  parse(args) {
    if (typeof args.file_path !== 'string' || args.file_path.length === 0) {
      return { __error: 'file_path is required (absolute path string). Example: edit(file_path="...", old_string="...", new_string="...")' }
    }
    if (typeof args.old_string !== 'string') return { __error: 'old_string is required (substring to replace)' }
    if (typeof args.new_string !== 'string') return { __error: 'new_string is required (replacement string; may be empty for deletion)' }
    return {
      file_path: args.file_path,
      old_string: args.old_string,
      new_string: args.new_string,
      replace_all: args.replace_all === true,
    }
  },
  async call(input, ctx) {
    if (input.old_string === input.new_string) {
      return { ok: false, error: 'old_string and new_string are identical, no change' }
    }
    if (!existsSync(input.file_path)) {
      return { ok: false, error: `File not found: ${input.file_path}` }
    }
    const cached = ctx.readFileCache.get(input.file_path)
    if (!cached) {
      return { ok: false, error: 'File must be read first before editing. Use the read tool.' }
    }
    const stat = statSync(input.file_path)
    if (stat.mtimeMs > cached.mtimeMs) {
      return { ok: false, error: 'File modified since read. Read it again before editing.' }
    }
    const content = readFileSync(input.file_path, 'utf8')
    const matches = content.split(input.old_string).length - 1
    if (matches === 0) {
      return { ok: false, error: `old_string not found in ${input.file_path}` }
    }
    if (matches > 1 && !input.replace_all) {
      return {
        ok: false,
        error: `${matches} matches of old_string in file. Set replace_all=true, or use a more unique old_string.`,
      }
    }
    const updated = input.replace_all
      ? content.split(input.old_string).join(input.new_string)
      : content.replace(input.old_string, input.new_string)
    writeFileSync(input.file_path, updated, 'utf8')
    ctx.readFileCache.set(input.file_path, updated)
    return { ok: true, data: { matches, replaceAll: input.replace_all === true } }
  },
  renderResult(r) {
    if (!r.ok) return `Error: ${r.error}`
    return r.data.replaceAll
      ? `File updated. Replaced ${r.data.matches} occurrence(s).`
      : 'File updated.'
  },
}
