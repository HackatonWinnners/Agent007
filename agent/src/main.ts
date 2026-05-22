import { resolve, dirname } from 'path'
import { readFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { config } from './config'
import { createLogger } from './logger'
import { createReadFileCache } from './state/readFileCache'
import { createCerebrasClient } from './models/cerebras'
import { createOllamaClient } from './models/ollama'
import { createRouter, type Role as RouterRole } from './models/router'
import { createRegistry } from './tools/registry'
import { readTool } from './tools/read'
import { editTool } from './tools/edit'
import { writeTool } from './tools/write'
import { bashTool } from './tools/bash'
import { globTool } from './tools/glob'
import { grepTool } from './tools/grep'
import { runTestsTool } from './tools/run_tests'
import { loadSkillTool } from './tools/load_skill'
import { submitDoneTool } from './tools/submit_done'
import { spawnSubagentTool, setSpawnContext } from './tools/spawn_subagent'
import { buildSystemPrompt } from './context'
import { autoCommit } from './git'
import { runLoop } from './agent'
import { ui } from './ui'

const HERE = dirname(fileURLToPath(import.meta.url))

const args = parseArgs(process.argv.slice(2))
const specPath = resolve(process.cwd(), args.spec ?? '../secret_spec/SECRET_SPEC.md')
const workingRoot = resolve(args.repoRoot ?? '..')

const logger = createLogger(config.logDir)
const readFileCache = createReadFileCache()

// Hybrid: Cerebras Cloud (Qwen3-235B free tier, ~2000 tok/s) is primary —
// strong code reasoning. Local Ollama Qwen3-Coder-30B-A3B (UD-Q4_K_XL) is
// fallback — kicks in when Cerebras 429s on the per-minute token quota.
// Router has automatic 60s cooldown on 429 and walks the chain.
const cerebras = createCerebrasClient({ apiKey: config.cerebrasKey, baseUrl: config.cerebrasBaseUrl })
const ollama = createOllamaClient({ baseUrl: config.ollamaBaseUrl })

const PRIMARY_MODEL = 'qwen-3-235b-a22b-instruct-2507'                      // Cerebras
const LOCAL_MODEL  = 'hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:UD-Q4_K_XL'  // Ollama

const MODELS: Record<RouterRole | 'fallback', string> = {
  primary_coder: PRIMARY_MODEL,
  planner: PRIMARY_MODEL,
  tester: PRIMARY_MODEL,
  failure_analyst: PRIMARY_MODEL,
  self_test_writer: PRIMARY_MODEL,
  fallback: LOCAL_MODEL,
}

const router = createRouter({
  primary: cerebras,
  fallback: ollama,
  models: MODELS,
  primaryTimeoutMs: config.primaryTimeoutMs,
  onIntervention: info =>
    logger.intervention({
      type: info.type,
      what: info.what,
      why: info.why,
      filesAffected: [],
      touchedFinalCode: false,
    }),
})

const rootTools = createRegistry([
  readTool, writeTool, editTool, bashTool,
  globTool, grepTool, runTestsTool, loadSkillTool,
  spawnSubagentTool,
  submitDoneTool,
])

const SUBAGENT_TOOLS = {
  // Planner returns text-only plans — giving it tools makes it spin on reads
  // when Cerebras emits JSON-text tool calls our parser can't extract.
  planner: createRegistry([]),
  implementer: createRegistry([readTool, editTool, writeTool, bashTool, globTool, grepTool, runTestsTool, loadSkillTool]),
  tester: createRegistry([runTestsTool]),
  failure_analyst: createRegistry([readTool, grepTool, loadSkillTool]),
  self_test_writer: createRegistry([readTool, writeTool, bashTool, loadSkillTool]),
} as const

setSpawnContext({
  router,
  registryFor: role => SUBAGENT_TOOLS[role],
  systemPromptFor: (role, taskHint) => {
    const tpl = readFileSync(resolve(HERE, 'prompts', `role_${role}.md`), 'utf8')
    return `${tpl}\n\nTASK\n${taskHint}`
  },
})

const initialUserMessage = `Read the spec at ${specPath}. Build the program described under ${config.solutionDir} (default solution/main.py if the spec is silent on filename or language). Pass public tests then harden with self-tests.`

const systemPrompt = buildSystemPrompt({
  cwd: workingRoot,
  iteration: 0,
  agentId: 'root',
  registry: rootTools,
  rolePromptPath: resolve(HERE, 'prompts', 'system_root.md'),
  skillsDir: resolve(HERE, 'skills'),
})

ui.banner({
  agentId: 'root',
  role: 'primary_coder',
  model: MODELS.primary_coder,
  cwd: workingRoot,
  specPath,
  maxIter: config.maxIterations,
})

await runLoop({
  agentId: 'root',
  router,
  role: 'primary_coder',
  tools: rootTools,
  systemPrompt,
  initialUserMessage,
  maxIterations: config.maxIterations,
  cwd: workingRoot,
  logger,
  readFileCache,
  autoCommit,
  onIterationStart: () => {},
})

function parseArgs(argv: string[]): { spec?: string; repoRoot?: string } {
  const out: Record<string, string> = {}
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]!
    if (a === '--spec') out.spec = argv[++i]!
    else if (a === '--repo-root') out.repoRoot = argv[++i]!
  }
  return out
}
