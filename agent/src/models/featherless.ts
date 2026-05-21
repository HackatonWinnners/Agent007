import type { ChatMessage, ChatRequest, ChatResponse, ModelClient, ToolCall } from './types'

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

export function createFeatherlessClient(opts: { apiKey: string; baseUrl: string }): ModelClient {
  return {
    async complete(req: ChatRequest): Promise<ChatResponse> {
      const body = {
        model: req.model,
        messages: toApi(req.messages),
        temperature: req.temperature ?? 0.2,
        max_tokens: req.maxTokens ?? 16384,
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
        },
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const text = await res.text()
        const err = new Error(`Featherless ${res.status}: ${text.slice(0, 500)}`)
        ;(err as Error & { status?: number }).status = res.status
        throw err
      }

      const data = (await res.json()) as {
        choices: { message: { content: string | null; tool_calls?: { id: string; function: { name: string; arguments: string } }[] } }[]
        usage?: { prompt_tokens: number; completion_tokens: number }
      }

      const msg = data.choices[0]?.message
      if (process.env.AGENT_DEBUG === '1' && msg?.tool_calls) {
        for (const tc of msg.tool_calls) {
          console.error(`[DEBUG] tc raw: ${JSON.stringify(tc).slice(0, 400)}`)
        }
      }
      // Some Featherless backends (notably models without proper tool-calling support)
      // return null/missing id and name. Synthesize sane defaults so we can echo
      // a valid assistant message back on the next turn.
      const nativeToolCalls: ToolCall[] = (msg?.tool_calls ?? [])
        .filter(tc => tc && tc.function && typeof tc.function.name === 'string' && tc.function.name.length > 0)
        .map((tc, i) => ({
          id: typeof tc.id === 'string' && tc.id.length > 0 ? tc.id : `tc-${Date.now()}-${i}`,
          name: tc.function.name,
          args: safeJson(tc.function.arguments),
        }))

      let content = msg?.content ?? null
      let toolCalls = nativeToolCalls

      // Fallback: Qwen3-Coder sometimes emits <function=NAME><parameter=K>V</parameter>...</function>
      // directly inside content instead of using the OpenAI-style tool_calls field.
      // Parse it and remove from content so the model doesn't see its own XML next turn.
      if (toolCalls.length === 0 && typeof content === 'string' && content.includes('<function=')) {
        const { calls, stripped } = parseXmlToolCalls(content)
        if (calls.length > 0) {
          toolCalls = calls
          content = stripped.trim() || null
          if (process.env.AGENT_DEBUG === '1') {
            console.error(`[DEBUG] parsed ${calls.length} XML tool_calls from content`)
          }
        }
      }

      return {
        content,
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

// Qwen3-Coder native tool-call format:
//   <function=NAME>
//   <parameter=KEY>VALUE</parameter>
//   ...
//   </function>
// Featherless sometimes wraps these in <tool_call>...</tool_call> too; we
// ignore the outer wrappers.
function parseXmlToolCalls(content: string): { calls: ToolCall[]; stripped: string } {
  const calls: ToolCall[] = []
  const fnRe = /<function=([a-zA-Z_][a-zA-Z0-9_]*)>([\s\S]*?)<\/function>/g
  const paramRe = /<parameter=([a-zA-Z_][a-zA-Z0-9_]*)>([\s\S]*?)<\/parameter>/g
  for (const m of content.matchAll(fnRe)) {
    const name = m[1]
    const body = m[2] ?? ''
    if (!name) continue
    const args: Record<string, unknown> = {}
    for (const pm of body.matchAll(paramRe)) {
      const k = pm[1]
      const v = pm[2] ?? ''
      if (!k) continue
      const vTrim = v.replace(/^\n+|\n+$/g, '')
      try { args[k] = JSON.parse(vTrim) } catch { args[k] = vTrim }
    }
    // If no <parameter=...> tags, try parsing the function body as JSON.
    if (Object.keys(args).length === 0) {
      const bodyTrim = body.trim()
      if (bodyTrim.startsWith('{')) {
        try {
          const parsed = JSON.parse(bodyTrim)
          if (typeof parsed === 'object' && parsed !== null) {
            Object.assign(args, parsed as Record<string, unknown>)
          }
        } catch { /* ignore */ }
      }
    }
    calls.push({ id: `xml-${Date.now()}-${calls.length}`, name, args })
  }
  const stripped = content.replace(fnRe, '').replace(/<\/?tool_call>/g, '').trim()
  return { calls, stripped }
}
