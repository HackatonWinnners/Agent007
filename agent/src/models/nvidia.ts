import type { ChatMessage, ChatRequest, ChatResponse, ModelClient, ToolCall } from './types'

// NVIDIA NIM is OpenAI-compatible. Same wire format as Featherless. We keep a
// dedicated client mostly so the per-provider auth header and base URL stay
// explicit and so we can swap one without disturbing the other.

type ApiMessage =
  | { role: 'system' | 'user'; content: string }
  | {
      role: 'assistant'
      content: string | null
      tool_calls?: { id: string; type: 'function'; function: { name: string; arguments: string } }[]
    }
  | { role: 'tool'; tool_call_id: string; content: string }

function toApi(messages: ChatMessage[]): ApiMessage[] {
  return messages.map(m => {
    if (m.role === 'assistant') {
      return {
        role: 'assistant',
        content: m.content,
        tool_calls: m.toolCalls?.map(tc => ({
          id: tc.id,
          type: 'function' as const,
          function: { name: tc.name, arguments: JSON.stringify(tc.args) },
        })),
      }
    }
    if (m.role === 'tool') {
      return { role: 'tool', tool_call_id: m.toolCallId, content: m.content }
    }
    return { role: m.role, content: m.content }
  })
}

export function createNvidiaClient(opts: { apiKey: string; baseUrl: string }): ModelClient {
  return {
    async complete(req: ChatRequest): Promise<ChatResponse> {
      const body = {
        model: req.model,
        messages: toApi(req.messages),
        temperature: req.temperature ?? 0.2,
        max_tokens: req.maxTokens ?? 4096,
        ...(req.tools && req.tools.length > 0
          ? {
              tools: req.tools.map(t => ({
                type: 'function',
                function: { name: t.name, description: t.description, parameters: t.parameters },
              })),
              tool_choice: 'auto',
            }
          : {}),
      }

      const res = await fetch(`${opts.baseUrl}/chat/completions`, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          authorization: `Bearer ${opts.apiKey}`,
          accept: 'application/json',
        },
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const text = await res.text()
        const err = new Error(`NVIDIA ${res.status}: ${text.slice(0, 500)}`)
        ;(err as Error & { status?: number }).status = res.status
        throw err
      }

      const data = (await res.json()) as {
        choices: { message: { content: string | null; tool_calls?: { id: string; function: { name: string; arguments: string } }[] } }[]
        usage?: { prompt_tokens: number; completion_tokens: number }
      }

      const msg = data.choices[0]?.message
      const toolCalls: ToolCall[] = (msg?.tool_calls ?? [])
        .filter(tc => tc && tc.function && typeof tc.function.name === 'string' && tc.function.name.length > 0)
        .map((tc, i) => ({
          id: typeof tc.id === 'string' && tc.id.length > 0 ? tc.id : `nv-${Date.now()}-${i}`,
          name: tc.function.name,
          args: safeJson(tc.function.arguments),
        }))

      return {
        content: msg?.content ?? null,
        toolCalls,
        usage: data.usage
          ? { promptTokens: data.usage.prompt_tokens, completionTokens: data.usage.completion_tokens }
          : undefined,
      }
    },
  }
}

function safeJson(s: string): Record<string, unknown> {
  try {
    const v = JSON.parse(s)
    return typeof v === 'object' && v !== null ? (v as Record<string, unknown>) : {}
  } catch {
    return {}
  }
}
