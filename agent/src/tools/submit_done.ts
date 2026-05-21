import type { Tool } from './types'

export const submitDoneTool: Tool<{ reason: string }, { reason: string }> = {
  name: 'submit_done',
  description:
    'Signals that the agent considers the task complete. Use only after public tests have been run and look stable. Root loop will exit after this call.',
  parameters: {
    type: 'object',
    properties: { reason: { type: 'string' } },
    required: ['reason'],
  },
  concurrencySafe: false,
  parse(args) {
    if (typeof args.reason !== 'string') return { __error: 'reason required' }
    return { reason: args.reason }
  },
  async call(input) {
    return { ok: true, data: { reason: input.reason } }
  },
  renderResult(r) {
    return r.ok ? `Halt signal received: ${r.data.reason}` : `Error: ${r.error}`
  },
}
