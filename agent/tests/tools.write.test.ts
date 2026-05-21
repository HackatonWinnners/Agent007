import { describe, it, expect, beforeEach } from 'vitest'
import { mkdtempSync, existsSync, readFileSync, writeFileSync } from 'fs'
import { tmpdir } from 'os'
import { join } from 'path'
import { writeTool } from '../src/tools/write'
import { createReadFileCache } from '../src/state/readFileCache'
import { createLogger } from '../src/logger'

let dir: string
beforeEach(() => { dir = mkdtempSync(join(tmpdir(), 'write-')) })

function ctx() {
  return { cwd: dir, logger: createLogger(dir), readFileCache: createReadFileCache(), agentId: 'root', iteration: 0 }
}

describe('write tool', () => {
  it('creates a new file', async () => {
    const p = join(dir, 'new.txt')
    const r = await writeTool.call({ file_path: p, content: 'hello\n' }, ctx())
    expect(r.ok).toBe(true)
    expect(existsSync(p)).toBe(true)
    expect(readFileSync(p, 'utf8')).toBe('hello\n')
  })

  it('refuses to overwrite without overwrite=true', async () => {
    const p = join(dir, 'existing.txt')
    writeFileSync(p, 'old\n')
    const r = await writeTool.call({ file_path: p, content: 'new' }, ctx())
    expect(r.ok).toBe(false)
  })

  it('overwrites when overwrite=true', async () => {
    const p = join(dir, 'existing.txt')
    writeFileSync(p, 'old\n')
    const r = await writeTool.call({ file_path: p, content: 'new\n', overwrite: true }, ctx())
    expect(r.ok).toBe(true)
    expect(readFileSync(p, 'utf8')).toBe('new\n')
  })

  it('creates intermediate directories', async () => {
    const p = join(dir, 'a/b/c.txt')
    const r = await writeTool.call({ file_path: p, content: 'x' }, ctx())
    expect(r.ok).toBe(true)
    expect(readFileSync(p, 'utf8')).toBe('x')
  })
})
