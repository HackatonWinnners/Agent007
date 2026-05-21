import { resolve } from 'path'

const cwd = process.cwd()

export const config = {
  cerebrasKey: process.env.CEREBRAS_API_KEY ?? '',
  cerebrasBaseUrl: process.env.CEREBRAS_BASE_URL ?? 'https://api.cerebras.ai/v1',
  nvidiaKey: process.env.NVIDIA_API_KEY ?? '',
  nvidiaBaseUrl: process.env.NVIDIA_BASE_URL ?? 'https://integrate.api.nvidia.com/v1',
  featherlessKey: process.env.FEATHERLESS_API_KEY ?? '',
  featherlessBaseUrl: process.env.FEATHERLESS_BASE_URL ?? 'https://api.featherless.ai/v1',
  ollamaBaseUrl: process.env.OLLAMA_BASE_URL ?? 'http://127.0.0.1:11434',
  maxIterations: Number(process.env.AGENT_MAX_ITERATIONS ?? 200),
  // Primary call must return within this many ms or the router falls back.
  primaryTimeoutMs: Number(process.env.AGENT_PRIMARY_TIMEOUT_MS ?? 60_000),
  logDir: resolve(cwd, process.env.AGENT_LOG_DIR ?? '../agent_logs'),
  repoRoot: resolve(cwd, '..'),
  solutionDir: resolve(cwd, '../solution'),
}

export const TOOL_BATCH_PARALLEL_LIMIT = 4
export const SUBAGENT_MAX_DEPTH = 1
export const SUBAGENT_MAX_CONCURRENT = 4
export const SUBAGENT_DEFAULT_MAX_ITER = 40
