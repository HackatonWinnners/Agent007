import { describe, it, expect, beforeEach } from 'vitest'
import { mkdtempSync, writeFileSync, readFileSync } from 'fs'
import { tmpdir } from 'os'
import { join } from 'path'
import { editTool } from '../src/tools/edit'
import { createReadFileCache } from '../src/state/readFileCache'
import { createLogger } from '../src/logger'

let dir: string
beforeEach(() => { dir = mkdtempSync(join(tmpdir(), 'edit-')) })

function ctx() {
  return { cwd: dir, logger: createLogger(dir), readFileCache: createReadFileCache(), agentId: 'root', iteration: 0 }
}

describe('edit tool', () => {
  it('refuses to edit a file that was not read first', async () => {
    const p = join(dir, 'a.txt')
    writeFileSync(p, 'hello world\n')
    const r = await editTool.call({ file_path: p, old_string: 'hello', new_string: 'hi' }, ctx())
    expect(r.ok).toBe(false)
    if (!r.ok) expect(r.error.toLowerCase()).toContain('read')
  })

  it('performs an exact replacement after read', async () => {
    const p = join(dir, 'a.txt')
    writeFileSync(p, 'hello world\n')
    const c = ctx()
    c.readFileCache.set(p, 'hello world\n')
    const r = await editTool.call({ file_path: p, old_string: 'hello', new_string: 'hi' }, c)
    expect(r.ok).toBe(true)
    expect(readFileSync(p, 'utf8')).toBe('hi world\n')
  })

  it('errors on multiple matches without replace_all', async () => {
    const p = join(dir, 'a.txt')
    writeFileSync(p, 'x x x\n')
    const c = ctx()
    c.readFileCache.set(p, 'x x x\n')
    const r = await editTool.call({ file_path: p, old_string: 'x', new_string: 'y' }, c)
    expect(r.ok).toBe(false)
    if (!r.ok) expect(r.error.toLowerCase()).toContain('matches')
  })

  it('replaces all when replace_all=true', async () => {
    const p = join(dir, 'a.txt')
    writeFileSync(p, 'x x x\n')
    const c = ctx()
    c.readFileCache.set(p, 'x x x\n')
    const r = await editTool.call({ file_path: p, old_string: 'x', new_string: 'y', replace_all: true }, c)
    expect(r.ok).toBe(true)
    expect(readFileSync(p, 'utf8')).toBe('y y y\n')
  })

  it('errors on no match', async () => {
    const p = join(dir, 'a.txt')
    writeFileSync(p, 'hello\n')
    const c = ctx()
    c.readFileCache.set(p, 'hello\n')
    const r = await editTool.call({ file_path: p, old_string: 'NOPE', new_string: 'x' }, c)
    expect(r.ok).toBe(false)
  })
})
