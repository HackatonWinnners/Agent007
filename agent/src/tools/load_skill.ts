import { readFileSync, existsSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'
import type { Tool } from './types'

type Input = { name: string }

// Resolve skills/ relative to this source file, so the tool works whether
// the agent process was started from agent/ or from the team-repo root.
const HERE = dirname(fileURLToPath(import.meta.url))
const SKILLS_DIR = resolve(HERE, '..', 'skills')

export const loadSkillTool: Tool<Input, { name: string; body: string }> = {
  name: 'load_skill',
  description: 'Loads the body of a named skill (markdown) and returns it. Caller injects it as a system message.',
  parameters: {
    type: 'object',
    properties: { name: { type: 'string' } },
    required: ['name'],
  },
  concurrencySafe: true,
  parse(args) {
    if (typeof args.name !== 'string') return { __error: 'name required' }
    if (!/^[a-z0-9_\-]+$/i.test(args.name)) return { __error: 'invalid skill name' }
    return { name: args.name }
  },
  async call(input) {
    const p = resolve(SKILLS_DIR, `${input.name}.md`)
    if (!existsSync(p)) return { ok: false, error: `Skill not found: ${input.name}` }
    const body = readFileSync(p, 'utf8')
    return { ok: true, data: { name: input.name, body } }
  },
  renderResult(r) {
    if (!r.ok) return `Error: ${r.error}`
    return `Skill ${r.data.name} loaded:\n\n${r.data.body}`
  },
}
