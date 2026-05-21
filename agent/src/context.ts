import { readFileSync, readdirSync } from 'fs'
import { join } from 'path'
import { spawnSync } from 'child_process'
import type { Registry } from './tools/registry'

export type ContextInputs = {
  cwd: string
  iteration: number
  agentId: string
  registry: Registry
  rolePromptPath: string
  skillsDir: string
}

export function buildSystemPrompt(inputs: ContextInputs): string {
  const tpl = readFileSync(inputs.rolePromptPath, 'utf8')
  const gitHead = safeSpawn(['git', 'rev-parse', '--short', 'HEAD'], inputs.cwd)
  const platform = `${process.platform} ${process.arch}`
  const skillCatalog = buildSkillCatalog(inputs.skillsDir)
  return tpl
    .replaceAll('<%cwd%>', inputs.cwd)
    .replaceAll('<%platform%>', platform)
    .replaceAll('<%gitHead%>', gitHead)
    .replaceAll('<%iteration%>', String(inputs.iteration))
    .replaceAll('<%skillCatalog%>', skillCatalog)
}

function safeSpawn(argv: string[], cwd: string): string {
  const [cmd, ...rest] = argv
  if (!cmd) return 'unknown'
  const r = spawnSync(cmd, rest, { cwd, stdio: ['ignore', 'pipe', 'ignore'] })
  if (r.status !== 0 || !r.stdout) return 'unknown'
  return r.stdout.toString().trim()
}

function buildSkillCatalog(skillsDir: string): string {
  const files = readdirSync(skillsDir).filter(f => f.endsWith('.md'))
  return files.map(f => {
    const body = readFileSync(join(skillsDir, f), 'utf8')
    const name = body.match(/^name:\s*(.+)$/m)?.[1]?.trim() ?? f.replace('.md', '')
    const desc = body.match(/^description:\s*(.+)$/m)?.[1]?.trim() ?? '(no description)'
    return `- ${name}: ${desc}`
  }).join('\n')
}
