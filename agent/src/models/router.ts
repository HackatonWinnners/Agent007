import type { ChatMessage, ChatResponse, ModelClient, ToolSchema } from './types'

export type Role = 'primary_coder' | 'planner' | 'tester' | 'failure_analyst' | 'self_test_writer'

export type RouterRequest = {
  role: Role
  messages: ChatMessage[]
  tools?: ToolSchema[]
  temperature?: number
  maxTokens?: number
}

export type RouterOptions = {
  primary: ModelClient
  fallback: ModelClient
  models: Record<Role | 'fallback', string>
  onIntervention(info: { type: string; what: string; why: string }): void
  retryDelaysMs?: number[]
}

const RETRYABLE = new Set([408, 429, 500, 502, 503, 504])

export function createRouter(opts: RouterOptions) {
  const delays = opts.retryDelaysMs ?? [1000, 4000, 12000]

  return {
    async complete(req: RouterRequest): Promise<ChatResponse> {
      const primaryModel = opts.models[req.role]
      const fullRequest = {
        model: primaryModel,
        messages: req.messages,
        tools: req.tools,
        temperature: req.temperature,
        maxTokens: req.maxTokens,
      }
      let lastErr: unknown
      for (let attempt = 0; attempt < delays.length; attempt++) {
        try {
          return await opts.primary.complete(fullRequest)
        } catch (e) {
          lastErr = e
          const status = (e as { status?: number }).status
          if (status && !RETRYABLE.has(status)) break
          await new Promise(r => setTimeout(r, delays[attempt] ?? 1000))
        }
      }
      opts.onIntervention({
        type: 'auto-fallback',
        what: `switched ${req.role} to fallback model ${opts.models.fallback}`,
        why: `primary failed: ${(lastErr as Error)?.message ?? 'unknown'}`,
      })
      return opts.fallback.complete({ ...fullRequest, model: opts.models.fallback })
    },
  }
}
