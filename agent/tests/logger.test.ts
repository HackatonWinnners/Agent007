import { describe, it, expect, beforeEach } from 'vitest'
import { mkdtempSync, readFileSync, existsSync } from 'fs'
import { tmpdir } from 'os'
import { join } from 'path'
import { createLogger } from '../src/logger'

let dir: string
let log: ReturnType<typeof createLogger>

beforeEach(() => {
  dir = mkdtempSync(join(tmpdir(), 'log-'))
  log = createLogger(dir)
})

describe('logger', () => {
  it('appends a timestamped decision line to decisions.log', () => {
    log.decision({ iteration: 1, agentId: 'root', summary: 'plan', rationale: 'spec read' })
    const text = readFileSync(join(dir, 'decisions.log'), 'utf8')
    expect(text).toMatch(/^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] DECISION/m)
    expect(text).toContain('plan')
    expect(text).toContain('iteration":1')
  })

  it('writes intervention with required fields', () => {
    log.intervention({
      type: 'auto-fallback',
      what: 'switched to Ollama',
      why: 'Featherless 429',
      filesAffected: [],
      touchedFinalCode: false,
    })
    const text = readFileSync(join(dir, 'human_interventions.log'), 'utf8')
    expect(text).toContain('touchedFinalCode":false')
  })

  it('truncates stdout tails to 4 KiB for commands', () => {
    const big = 'x'.repeat(10_000)
    log.command({ cmd: 'echo big', exitCode: 0, durationMs: 1, stdoutTail: big })
    const text = readFileSync(join(dir, 'commands.log'), 'utf8')
    expect(text).toMatch(/"stdoutTail":"x{4096}"/)
  })

  it('creates the log directory if it does not exist', () => {
    const newDir = join(dir, 'nested', 'logs')
    const l = createLogger(newDir)
    l.error({ where: 't', message: 'm' })
    expect(existsSync(join(newDir, 'errors.log'))).toBe(true)
  })
})
