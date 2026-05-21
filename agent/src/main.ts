import { resolve, dirname } from 'path'
import { readFileSync } from 'fs'
import { fileURLToPath } from 'url'
import { config } from './config'
import { createLogger } from './logger'
import { createReadFileCache } from './state/readFileCache'
import { createNvidiaClient } from './models/nvidia'
import { createFeatherlessClient } from './models/featherless'
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
// Resolve spec path relative to the process cwd (where the user ran `bun run`),
// NOT relative to workingRoot. This lets `--spec ../demo/toy_spec.md` work when
// the agent process runs from agent/ and demo/ is a sibling of agent/.
const specPath = resolve(process.cwd(), args.spec ?? '../secret_spec/SECRET_SPEC.md')
const workingRoot = resolve(args.repoRoot ?? '..')

const logger = createLogger(config.logDir)
const readFileCache = createReadFileCache()

const nvidia = createNvidiaClient({ apiKey: config.nvidiaKey, baseUrl: config.nvidiaBaseUrl })
const featherless = createFeatherlessClient({ apiKey: config.featherlessKey, baseUrl: config.featherlessBaseUrl })
const ollama = createOllamaClient({ baseUrl: config.ollamaBaseUrl })
// NVIDIA NIM was hanging on the real spec (likely cold-start or queue depth on
// the free tier), so we swapped to Featherless as primary. NVIDIA stays wired
// as the fallback in case Featherless rate-limits us.
const primaryClient = featherless
const fallbackClient = nvidia
void ollama

// DeepSeek-V4-Pro is tools=False on Featherless — our entire agent depends on
// tool calls (every role's runLoop sends tools), so V4-Pro is unusable here
// without a major architecture rewrite. Use DeepSeek-V3.2 (newest with tools=True)
// for everything. Fallback also on Featherless so we don't need Ollama running.
const MODELS: Record<RouterRole | 'fallback', string> = {
  primary_coder: 'Qwen/Qwen3-Coder-480B-A35B-Instruct',
  planner: 'Qwen/Qwen3-Coder-480B-A35B-Instruct',
  tester: 'Qwen/Qwen3-Coder-480B-A35B-Instruct',
  failure_analyst: 'Qwen/Qwen3-Coder-480B-A35B-Instruct',
  self_test_writer: 'Qwen/Qwen3-Coder-480B-A35B-Instruct',
  // Fallback hits NVIDIA NIM with the lowercase namespaced id.
  fallback: 'qwen/qwen3-coder-480b-a35b-instruct',
}

const router = createRouter({
  primary: primaryClient,
  fallback: fallbackClient,
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

// Root toolset for the real hackathon task. We re-enable run_tests, edit,
// glob, grep, load_skill — DeepSeek-V3.2's empty-args glitch doesn't affect
// Qwen3-Coder which is our actual primary on NVIDIA. Subagents stay off to
// keep the loop linear and easier to debug overnight.
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
