import { statSync } from 'fs'

export type ReadEntry = { mtimeMs: number; content: string }

export type ReadFileCache = {
  get(path: string): ReadEntry | undefined
  set(path: string, content: string): void
  has(path: string): boolean
  clear(): void
}

export function createReadFileCache(): ReadFileCache {
  const m = new Map<string, ReadEntry>()
  return {
    get: p => m.get(p),
    set(p, content) {
      const mtimeMs = statSync(p).mtimeMs
      m.set(p, { mtimeMs, content })
    },
    has: p => m.has(p),
    clear: () => m.clear(),
  }
}
