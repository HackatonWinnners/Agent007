import { resolve, dirname } from 'path'
import { readFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { config } from './config'
import { createLogger } from './logger'
import { createReadFileCache } from './state/readFileCache'
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
// Spec path resolves relative to cwd of `bun run` (typically the agent/ dir),
// so `--spec ../secret_spec/SECRET_SPEC.md` works out of the box.
const specPath = resolve(process.cwd(), args.spec ?? '../secret_spec/SECRET_SPEC.md')
const workingRoot = resolve(args.repoRoot ?? '..')

const logger = createLogger(config.logDir)
const readFileCache = createReadFileCache()

// Single provider: local Ollama. Chosen for predictable latency, zero rate
// limits, no network dependency, and full hackathon-rule compliance (purely
// local inference). Both primary and fallback point at the same Ollama
// instance — fallback is exercised only when the primary call itself throws.
const ollama = createOllamaClient({ baseUrl: config.ollamaBaseUrl })

const MODEL_ID = 'hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:UD-Q4_K_XL'

const MODELS: Record<RouterRole | 'fallback', string> = {
  primary_coder: MODEL_ID,
  planner: MODEL_ID,
  tester: MODEL_ID,
  failure_analyst: MODEL_ID,
  self_test_writer: MODEL_ID,
  fallback: MODEL_ID,
}

const router = createRouter({
  primary: ollama,
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
  submitDoneTool,
])
void spawnSubagentTool

const SUBAGENT_TOOLS = {
  planner: createRegistry([readTool, loadSkillTool]),
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
