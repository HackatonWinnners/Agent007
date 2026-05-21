export type ToolCall = {
  id: string
  name: string
  args: Record<string, unknown>
}

export type ChatMessage =
  | { role: 'system'; content: string }
  | { role: 'user'; content: string }
  | { role: 'assistant'; content: string | null; toolCalls?: ToolCall[] }
  | { role: 'tool'; toolCallId: string; content: string }

export type ToolSchema = {
  name: string
  description: string
  parameters: Record<string, unknown>
}

export type ChatRequest = {
  model: string
  messages: ChatMessage[]
  tools?: ToolSchema[]
  temperature?: number
  maxTokens?: number
}

export type ChatResponse = {
  content: string | null
  toolCalls: ToolCall[]
  usage?: { promptTokens: number; completionTokens: number }
}

export type ModelClient = {
  complete(req: ChatRequest): Promise<ChatResponse>
}
