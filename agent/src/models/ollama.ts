import type { ChatMessage, ChatRequest, ChatResponse, ModelClient, ToolCall } from './types'

export function createOllamaClient(opts: { baseUrl: string }): ModelClient {
  return {
    async complete(req: ChatRequest): Promise<ChatResponse> {
      const body = {
        model: req.model,
        messages: req.messages.map(adapt),
        stream: false,
        options: { temperature: req.temperature ?? 0.2 },
        ...(req.tools && req.tools.length > 0
          ? {
              tools: req.tools.map(t => ({
                type: 'function',
                function: { name: t.name, description: t.description, parameters: t.parameters },
              })),
            }
          : {}),
      }

      const res = await fetch(`${opts.baseUrl}/api/chat`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        throw new Error(`Ollama ${res.status}: ${await res.text()}`)
      }

      const data = (await res.json()) as {
        message?: {
          content?: string
          tool_calls?: { function: { name: string; arguments: Record<string, unknown> } }[]
        }
      }

      const m = data.message
      const toolCalls: ToolCall[] = (m?.tool_calls ?? []).map((tc, i) => ({
        id: `ollama-${Date.now()}-${i}`,
        name: tc.function.name,
        args: tc.function.arguments,
      }))

      return { content: m?.content ?? null, toolCalls }
    },
  }
}

function adapt(m: ChatMessage) {
  if (m.role === 'tool') return { role: 'tool', content: m.content }
  if (m.role === 'assistant') return { role: 'assistant', content: m.content ?? '' }
  return { role: m.role, content: m.content }
}
