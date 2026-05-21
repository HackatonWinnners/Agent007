import { describe, it, expect, beforeEach } from 'vitest'
import { mkdtempSync, writeFileSync, mkdirSync, realpathSync } from 'fs'
import { tmpdir } from 'os'
import { join } from 'path'
import { globTool } from '../src/tools/glob'
import { createReadFileCache } from '../src/state/readFileCache'
import { createLogger } from '../src/logger'

let dir: string
beforeEach(() => {
  dir = realpathSync(mkdtempSync(join(tmpdir(), 'glob-')))
  mkdirSync(join(dir, 'src'))
  writeFileSync(join(dir, 'src', 'a.py'), '')
  writeFileSync(join(dir, 'src', 'b.py'), '')
  writeFileSync(join(dir, 'src', 'c.txt'), '')
})

function ctx() {
  return { cwd: dir, logger: createLogger(dir), readFileCache: createReadFileCache(), agentId: 'root', iteration: 0 }
}

describe('glob tool', () => {
  it('finds files by pattern', async () => {
    const r = await globTool.call({ pattern: '**/*.py' }, ctx())
    expect(r.ok).toBe(true)
    if (r.ok) {
      const names = r.data.paths.map(p => p.replace(dir + '/', ''))
      expect(names.sort()).toEqual(['src/a.py', 'src/b.py'])
    }
  })
})
