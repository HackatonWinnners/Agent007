import { describe, it, expect, vi } from 'vitest'
import type { ChatRequest, ChatResponse, ModelClient } from '../src/models/types'
import { createRouter } from '../src/models/router'

function ok(): ModelClient {
  return { complete: async () => ({ content: 'ok', toolCalls: [] }) as ChatResponse }
}
function fail(status: number): ModelClient {
  return {
    complete: async () => {
      const e = new Error(`x ${status}`) as Error & { status?: number }
      e.status = status
      throw e
    },
  }
}

describe('router', () => {
  it('routes role primary_coder to the configured primary model id', async () => {
    const spy = vi.fn(async (_: ChatRequest) => ({ content: 'p', toolCalls: [] }) as ChatResponse)
    const r = createRouter({
      primary: { complete: spy } as ModelClient,
      fallback: ok(),
      onIntervention: () => {},
      models: {
        primary_coder: 'PC',
        planner: 'PL',
        tester: 'T',
        failure_analyst: 'FA',
        self_test_writer: 'STW',
        fallback: 'F',
      },
    })
    await r.complete({ role: 'primary_coder', messages: [{ role: 'user', content: 'hi' }] })
    expect(spy).toHaveBeenCalledTimes(1)
    expect(spy.mock.calls[0]![0].model).toBe('PC')
  })

  it('falls back after retries exhaust and logs an intervention', async () => {
    const onIntervention = vi.fn()
    const fb = vi.fn(async () => ({ content: 'fb', toolCalls: [] }) as ChatResponse)
    const r = createRouter({
      primary: fail(500),
      fallback: { complete: fb } as ModelClient,
      onIntervention,
      models: {
        primary_coder: 'PC',
        planner: 'PL',
        tester: 'T',
        failure_analyst: 'FA',
        self_test_writer: 'STW',
        fallback: 'F',
      },
      retryDelaysMs: [1, 1, 1],
    })
    const out = await r.complete({ role: 'primary_coder', messages: [{ role: 'user', content: 'x' }] })
    expect(out.content).toBe('fb')
    expect(fb).toHaveBeenCalledTimes(1)
    expect(onIntervention).toHaveBeenCalledTimes(1)
  })

  it('does not retry on 401', async () => {
    const onIntervention = vi.fn()
    const fb = vi.fn(async () => ({ content: 'fb', toolCalls: [] }) as ChatResponse)
    const r = createRouter({
      primary: fail(401),
      fallback: { complete: fb } as ModelClient,
      onIntervention,
      models: {
        primary_coder: 'PC',
        planner: 'PL',
        tester: 'T',
        failure_analyst: 'FA',
        self_test_writer: 'STW',
        fallback: 'F',
      },
      retryDelaysMs: [1, 1, 1],
    })
    await r.complete({ role: 'primary_coder', messages: [{ role: 'user', content: 'x' }] })
    expect(fb).toHaveBeenCalledTimes(1)
    expect(onIntervention).toHaveBeenCalledTimes(1)
  })
})
