import { describe, it, expect, beforeEach } from 'vitest'
import { mkdtempSync, writeFileSync } from 'fs'
import { tmpdir } from 'os'
import { join } from 'path'
import { readTool } from '../src/tools/read'
import { createReadFileCache } from '../src/state/readFileCache'
import { createLogger } from '../src/logger'

let dir: string
beforeEach(() => { dir = mkdtempSync(join(tmpdir(), 'read-')) })

function ctx() {
  return { cwd: dir, logger: createLogger(dir), readFileCache: createReadFileCache(), agentId: 'root', iteration: 0 }
}

describe('read tool', () => {
  it('returns file content with line-number prefix', async () => {
    writeFileSync(join(dir, 'a.txt'), 'hello\nworld\n')
    const r = await readTool.call({ file_path: join(dir, 'a.txt') }, ctx())
    expect(r.ok).toBe(true)
    if (r.ok) {
      expect(r.data.content).toBe('1\thello\n2\tworld\n')
    }
  })

  it('errors on missing file', async () => {
    const r = await readTool.call({ file_path: join(dir, 'nope.txt') }, ctx())
    expect(r.ok).toBe(false)
  })

  it('records the read in the cache', async () => {
    writeFileSync(join(dir, 'b.txt'), 'x\n')
    const c = ctx()
    await readTool.call({ file_path: join(dir, 'b.txt') }, c)
    expect(c.readFileCache.has(join(dir, 'b.txt'))).toBe(true)
  })
})
