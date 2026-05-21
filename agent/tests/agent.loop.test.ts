import { describe, it, expect, vi } from 'vitest'
import type { ChatResponse } from '../src/models/types'
import { runLoop } from '../src/agent'

describe('agent loop', () => {
  it('stops when the model returns no tool calls', async () => {
    const router = {
      complete: vi.fn(async () => ({ content: null, toolCalls: [] }) as ChatResponse),
    }
    const result = await runLoop({
      agentId: 'root',
      router: router as any,
      role: 'primary_coder' as const,
      tools: { list: () => [], byName: () => undefined, schemas: () => [], invoke: async () => ({ rendered: '', raw: { ok: true, data: {} } }) } as any,
      systemPrompt: 'sys',
      initialUserMessage: 'do it',
      maxIterations: 5,
      cwd: process.cwd(),
      logger: stubLogger(),
      readFileCache: { get: () => undefined, set: () => {}, has: () => false, clear: () => {} } as any,
      autoCommit: () => {},
      onIterationStart: () => {},
    })
    expect(result.halted).toBe(false)
    expect(router.complete).toHaveBeenCalled()
  })

  it('halts after submit_done', async () => {
    let n = 0
    const router = {
      complete: vi.fn(async () => {
        n++
        if (n === 1) return { content: null, toolCalls: [{ id: '1', name: 'submit_done', args: { reason: 'ok' } }] } as ChatResponse
        return { content: null, toolCalls: [] } as ChatResponse
      }),
    }
    const reg = {
      list: () => [{ name: 'submit_done', concurrencySafe: false } as any],
      byName: (n: string) => (n === 'submit_done' ? ({ name: 'submit_done', concurrencySafe: false } as any) : undefined),
      schemas: () => [],
      invoke: async () => ({ rendered: 'halt', raw: { ok: true, data: { reason: 'ok' } } }),
    }
    const out = await runLoop({
      agentId: 'root',
      router: router as any,
      role: 'primary_coder' as const,
      tools: reg as any,
      systemPrompt: 'sys',
      initialUserMessage: 'do it',
      maxIterations: 5,
      cwd: process.cwd(),
      logger: stubLogger(),
      readFileCache: { get: () => undefined, set: () => {}, has: () => false, clear: () => {} } as any,
      autoCommit: () => {},
      onIterationStart: () => {},
    })
    expect(out.halted).toBe(true)
  })
})

function stubLogger() {
  return {
    prompt: () => {}, decision: () => {}, command: () => {},
    testRun: () => {}, error: () => {}, intervention: () => {},
  } as any
}
