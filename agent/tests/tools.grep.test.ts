import { describe, it, expect, beforeEach } from 'vitest'
import { mkdtempSync, writeFileSync, realpathSync } from 'fs'
import { tmpdir } from 'os'
import { join } from 'path'
import { grepTool } from '../src/tools/grep'
import { createReadFileCache } from '../src/state/readFileCache'
import { createLogger } from '../src/logger'

let dir: string
beforeEach(() => {
  dir = realpathSync(mkdtempSync(join(tmpdir(), 'grep-')))
  writeFileSync(join(dir, 'a.txt'), 'foo\nbar\nfoo bar\n')
  writeFileSync(join(dir, 'b.txt'), 'baz\n')
})

function ctx() {
  return { cwd: dir, logger: createLogger(dir), readFileCache: createReadFileCache(), agentId: 'root', iteration: 0 }
}

describe('grep tool', () => {
  it('returns matching file:line pairs', async () => {
    const r = await grepTool.call({ pattern: 'foo' }, ctx())
    expect(r.ok).toBe(true)
    if (r.ok) {
      const lines = r.data.matches.map(m => `${m.path.split('/').pop()}:${m.line}:${m.text.trim()}`).sort()
      expect(lines).toEqual(['a.txt:1:foo', 'a.txt:3:foo bar'])
    }
  })
})
