import { spawn } from 'child_process'
import type { Tool } from './types'

type Input = { runner_cmd?: string; suite?: 'public' | 'self' }

type Output = {
  score: string | null
  exitCode: number
  failingCategories: string[]
  stdoutTail: string
}

const DEFAULT_PUBLIC =
  'python3 ../secret_spec/test_runner/run_tests.py --program "python3 ../solution/main.py" --suite public'
const DEFAULT_SELF = 'pytest -q ../solution/self_tests'

export const runTestsTool: Tool<Input, Output> = {
  name: 'run_tests',
  description: 'Runs the public test suite (default) or the self-test suite. Returns score, failing categories, exit code.',
  parameters: {
    type: 'object',
    properties: {
      runner_cmd: { type: 'string', description: 'Override the runner command.' },
      suite: { type: 'string', enum: ['public', 'self'] },
    },
  },
  concurrencySafe: false,
  parse(args) {
    return {
      runner_cmd: typeof args.runner_cmd === 'string' ? args.runner_cmd : undefined,
      suite: args.suite === 'self' ? 'self' : 'public',
    }
  },
  async call(input, ctx) {
    const cmd = input.runner_cmd ?? (input.suite === 'self' ? DEFAULT_SELF : DEFAULT_PUBLIC)
    return new Promise(resolve => {
      const start = Date.now()
      // cmd is the agent prompt default constant or the model's runner_cmd override,
      // deliberately executed under a shell. See tools/bash.ts note.
      const child = spawn('/bin/bash', ['-lc', cmd], { cwd: ctx.cwd })
      let stdout = ''
      let stderr = ''
      child.stdout.on('data', (c: Buffer) => { stdout += c.toString('utf8') })
      child.stderr.on('data', (c: Buffer) => { stderr += c.toString('utf8') })
      child.on('close', code => {
        const exitCode = code ?? -1
        const combined = `${stdout}\n${stderr}`
        const scoreMatch = combined.match(/(\d+)\s*\/\s*(\d+)/)
        const score = scoreMatch ? `${scoreMatch[1]}/${scoreMatch[2]}` : null
        const failingCategories = parseFailingCategories(combined)
        ctx.logger.testRun({ score: score ?? 'unknown', failingCategories })
        ctx.logger.command({ cmd, exitCode, durationMs: Date.now() - start, stdoutTail: combined })
        resolve({
          ok: true,
          data: { score, exitCode, failingCategories, stdoutTail: combined.slice(-4096) },
        })
      })
    })
  },
  renderResult(r) {
    if (!r.ok) return `Error: ${r.error}`
    const head = `score=${r.data.score ?? 'unknown'} exit=${r.data.exitCode}\n`
    const cats = r.data.failingCategories.length > 0
      ? `failing categories: ${r.data.failingCategories.join(', ')}\n`
      : ''
    return head + cats + `\n--- tail ---\n${r.data.stdoutTail}`
  },
}

function parseFailingCategories(text: string): string[] {
  // Generic best-effort parser. The actual public runner format is unknown until
  // reveal; tweak this once the real output is visible.
  const lines = text.split('\n')
  const out = new Set<string>()
  for (const l of lines) {
    const m = l.match(/(?:FAIL|FAILED|category|group)[^a-zA-Z]+([a-zA-Z0-9_\-]+)/)
    if (m && m[1]) out.add(m[1].toLowerCase())
  }
  return [...out]
}
