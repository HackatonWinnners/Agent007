import { spawn } from 'child_process'
import type { Tool } from './types'

type Input = { cmd: string; timeout_ms?: number; cwd?: string }
type Output = { exitCode: number; stdout: string; stderr: string; durationMs: number; timedOut: boolean }

export const bashTool: Tool<Input, Output> = {
  name: 'bash',
  description: 'Runs a shell command via /bin/bash -lc. Captures stdout, stderr, exit code. Default timeout 60000ms.',
  parameters: {
    type: 'object',
    properties: {
      cmd: { type: 'string' },
      timeout_ms: { type: 'integer', minimum: 100 },
      cwd: { type: 'string' },
    },
    required: ['cmd'],
  },
  concurrencySafe: false,
  parse(args) {
    if (typeof args.cmd !== 'string' || args.cmd.length === 0) return { __error: 'cmd required' }
    return {
      cmd: args.cmd,
      timeout_ms: typeof args.timeout_ms === 'number' ? args.timeout_ms : undefined,
      cwd: typeof args.cwd === 'string' ? args.cwd : undefined,
    }
  },
  async call(input, ctx) {
    const start = Date.now()
    const timeout = input.timeout_ms ?? 60_000
    return new Promise(resolve => {
      // cmd is intentionally passed to a shell because models need shell features.
      // No external input is concatenated into this string here.
      const child = spawn('/bin/bash', ['-lc', input.cmd], { cwd: input.cwd ?? ctx.cwd })
      let stdout = ''
      let stderr = ''
      let timedOut = false
      const timer = setTimeout(() => {
        timedOut = true
        child.kill('SIGKILL')
      }, timeout)
      child.stdout.on('data', (c: Buffer) => { stdout += c.toString('utf8') })
      child.stderr.on('data', (c: Buffer) => { stderr += c.toString('utf8') })
      child.on('close', code => {
        clearTimeout(timer)
        const durationMs = Date.now() - start
        const exitCode = code ?? (timedOut ? 124 : -1)
        ctx.logger.command({ cmd: input.cmd, exitCode, durationMs, stdoutTail: stdout })
        resolve({ ok: true, data: { exitCode, stdout, stderr, durationMs, timedOut } })
      })
    })
  },
  renderResult(r) {
    if (!r.ok) return `Error: ${r.error}`
    const head = `exit=${r.data.exitCode} duration=${r.data.durationMs}ms${r.data.timedOut ? ' TIMEOUT' : ''}\n`
    const so = r.data.stdout.length > 0 ? `--- stdout ---\n${r.data.stdout}\n` : ''
    const se = r.data.stderr.length > 0 ? `--- stderr ---\n${r.data.stderr}\n` : ''
    return head + so + se
  },
}
