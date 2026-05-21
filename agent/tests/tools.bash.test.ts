import { describe, it, expect, beforeEach } from 'vitest'
import { mkdtempSync, realpathSync } from 'fs'
import { tmpdir } from 'os'
import { join } from 'path'
import { bashTool } from '../src/tools/bash'
import { createReadFileCache } from '../src/state/readFileCache'
import { createLogger } from '../src/logger'

let dir: string
beforeEach(() => { dir = mkdtempSync(join(tmpdir(), 'bash-')) })

function ctx() {
  return { cwd: dir, logger: createLogger(dir), readFileCache: createReadFileCache(), agentId: 'root', iteration: 0 }
}

describe('bash tool', () => {
  it('runs a command and captures stdout', async () => {
    const r = await bashTool.call({ cmd: 'echo hello' }, ctx())
    expect(r.ok).toBe(true)
    if (r.ok) {
      expect(r.data.exitCode).toBe(0)
      expect(r.data.stdout).toContain('hello')
    }
  })

  it('captures non-zero exit', async () => {
    const r = await bashTool.call({ cmd: 'exit 7' }, ctx())
    expect(r.ok).toBe(true)
    if (r.ok) expect(r.data.exitCode).toBe(7)
  })

  it('honors cwd', async () => {
    const r = await bashTool.call({ cmd: 'pwd' }, ctx())
    expect(r.ok).toBe(true)
    if (r.ok) expect(r.data.stdout.trim()).toBe(realpathSync(dir))
  })

  it('respects timeout', async () => {
    const r = await bashTool.call({ cmd: 'sleep 5', timeout_ms: 200 }, ctx())
    expect(r.ok).toBe(true)
    if (r.ok) expect(r.data.timedOut).toBe(true)
  })
})
