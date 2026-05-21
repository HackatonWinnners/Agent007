import type { ChatMessage, ChatResponse, ModelClient, ToolSchema } from './types'

export type Role = 'primary_coder' | 'planner' | 'tester' | 'failure_analyst' | 'self_test_writer'

export type RouterRequest = {
  role: Role
  messages: ChatMessage[]
  tools?: ToolSchema[]
  temperature?: number
  maxTokens?: number
}

// A tier is one provider+model with its own cooldown.
export type RouterTier = {
  name: string
  client: ModelClient
  model: string  // for non-primary tiers, overrides MODELS[role]
}

export type RouterOptions = {
  primary: ModelClient
  fallback: ModelClient
  // Optional extra fallbacks tried in order when both primary and fallback fail.
  extraFallbacks?: RouterTier[]
  models: Record<Role | 'fallback', string>
  onIntervention(info: { type: string; what: string; why: string }): void
  retryDelaysMs?: number[]
  // Hard timeout on the WHOLE primary attempt sequence (including retries).
  // If exceeded, router triggers fallback. Default 60s.
  primaryTimeoutMs?: number
}

const RETRYABLE = new Set([408, 500, 502, 503, 504])
// 429 is special: it means we hit a rate limit, retrying immediately won't help.
// Instead we cool the primary for a minute and route via fallback during that window.
const RATE_LIMIT_STATUS = 429
const PRIMARY_COOLDOWN_MS = 60_000

export function createRouter(opts: RouterOptions) {
  const delays = opts.retryDelaysMs ?? [1000, 4000, 12000]
  const timeoutMs = opts.primaryTimeoutMs ?? 60_000
  let primaryColdUntil = 0  // epoch ms; while now < this, skip primary entirely

  async function tryPrimary(fullRequest: Parameters<ModelClient['complete']>[0]): Promise<ChatResponse> {
    let lastErr: unknown
    for (let attempt = 0; attempt < delays.length; attempt++) {
      try {
        return await opts.primary.complete(fullRequest)
      } catch (e) {
        lastErr = e
        const status = (e as { status?: number }).status
        if (status === RATE_LIMIT_STATUS) {
          // Mark primary as cold and stop trying — caller will use fallback.
          primaryColdUntil = Date.now() + PRIMARY_COOLDOWN_MS
          break
        }
        if (status && !RETRYABLE.has(status)) break
        await new Promise(r => setTimeout(r, delays[attempt] ?? 1000))
      }
    }
    throw lastErr ?? new Error('primary failed')
  }

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
      // If primary is in cooldown (recent 429), bypass it and walk the tier
      // chain instead.
      if (Date.now() < primaryColdUntil) {
        const msLeft = primaryColdUntil - Date.now()
        opts.onIntervention({
          type: 'primary-cooldown',
          what: `primary in cooldown, routing ${req.role} via tier chain`,
          why: `~${Math.ceil(msLeft / 1000)}s left after recent 429`,
        })
        return await walkTiers(fullRequest)
      }
      // Race primary attempt sequence against a hard timeout. Whichever resolves
      // first wins; on timeout we fall back to the secondary provider.
      let timeoutHandle: ReturnType<typeof setTimeout> | null = null
      const timeoutPromise = new Promise<{ kind: 'timeout' }>(resolveT => {
        timeoutHandle = setTimeout(() => resolveT({ kind: 'timeout' }), timeoutMs)
      })
      const primaryPromise = tryPrimary(fullRequest).then(
        r => ({ kind: 'ok' as const, response: r }),
        e => ({ kind: 'error' as const, error: e as Error }),
      )
      const winner = await Promise.race([primaryPromise, timeoutPromise])
      if (timeoutHandle) clearTimeout(timeoutHandle)

      if (winner.kind === 'ok') return winner.response

      const why = winner.kind === 'timeout'
        ? `primary exceeded ${timeoutMs}ms timeout`
        : `primary failed: ${winner.error?.message ?? 'unknown'}`
      opts.onIntervention({
        type: 'auto-fallback',
        what: `switched ${req.role} to fallback model ${opts.models.fallback}`,
        why,
      })

      return await walkTiers(fullRequest)
    },
  }

  async function walkTiers(fullRequest: Parameters<ModelClient['complete']>[0]): Promise<ChatResponse> {
    const tiers: { name: string; client: ModelClient; model: string }[] = [
      { name: 'fallback', client: opts.fallback, model: opts.models.fallback },
      ...(opts.extraFallbacks ?? []),
    ]
    let lastError: Error | null = null
    for (const tier of tiers) {
      try {
        return await tier.client.complete({ ...fullRequest, model: tier.model })
      } catch (e) {
        lastError = e as Error
        opts.onIntervention({
          type: 'fallback-failed',
          what: `${tier.name} (${tier.model}) failed, trying next tier`,
          why: (e as Error).message?.slice(0, 200) ?? 'unknown',
        })
      }
    }
    // All providers failed. Sleep and retry primary once before giving up.
    opts.onIntervention({
      type: 'all-providers-down',
      what: 'all tiers failed, sleeping 30s before retrying primary',
      why: lastError?.message?.slice(0, 200) ?? 'unknown',
    })
    await new Promise(r => setTimeout(r, 30_000))
    primaryColdUntil = 0
    return opts.primary.complete(fullRequest)
  }
}
