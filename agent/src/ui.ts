// Pretty terminal UI for the agent loop. ANSI-colored, no extra deps.
// Suppressed when AGENT_QUIET=1 or stdout is not a TTY.

const isTty = process.stdout.isTTY === true
const forced = process.env.AGENT_FORCE_UI === '1'
const quiet = process.env.AGENT_QUIET === '1' || (!isTty && !forced)

const c = {
  reset: '\x1b[0m',
  dim: '\x1b[2m',
  bold: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  gray: '\x1b[90m',
  brightGreen: '\x1b[92m',
  brightYellow: '\x1b[93m',
  brightCyan: '\x1b[96m',
}

function write(s: string): void {
  if (!quiet) process.stdout.write(s)
}

function hms(): string {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

export const ui = {
  banner(opts: { agentId: string; role: string; model: string; cwd: string; specPath: string; maxIter: number }) {
    if (quiet) return
    const line = (label: string, value: string) =>
      `  ${c.dim}${label.padEnd(12)}${c.reset}${value}\n`
    const w = '─'.repeat(60)
    write(
      `\n${c.bold}${c.brightCyan}╭${w}╮${c.reset}\n` +
      `${c.bold}${c.brightCyan}│${c.reset}  ${c.bold}NEEDLE AGENT${c.reset}${c.dim}  hackathon coding agent${c.reset}${' '.repeat(20)}${c.bold}${c.brightCyan}│${c.reset}\n` +
      `${c.bold}${c.brightCyan}╰${w}╯${c.reset}\n` +
      line('agent', opts.agentId) +
      line('role', opts.role) +
      line('model', opts.model) +
      line('cwd', opts.cwd) +
      line('spec', opts.specPath) +
      line('max iter', String(opts.maxIter)) +
      `\n`
    )
  },

  iter(opts: { agentId: string; iteration: number }) {
    if (quiet) return
    write(`\n${c.bold}${c.cyan}┌─ iter ${opts.iteration} ${c.dim}[${opts.agentId}]${c.reset} ${c.dim}${hms()}${c.reset}\n`)
  },

  thinking(text: string) {
    if (quiet || !text) return
    const trimmed = text.trim()
    if (!trimmed) return
    const lines = trimmed.split('\n').slice(0, 6)
    for (const l of lines) {
      write(`${c.cyan}│${c.reset} ${c.dim}${l.slice(0, 160)}${c.reset}\n`)
    }
  },

  toolCall(name: string, args: Record<string, unknown>) {
    if (quiet) return
    const short = shortArgs(name, args)
    write(`${c.cyan}│${c.reset} ${c.bold}${c.brightYellow}● ${name}${c.reset} ${c.dim}${short}${c.reset}\n`)
  },

  toolResult(name: string, ok: boolean, summary: string) {
    if (quiet) return
    const icon = ok ? `${c.brightGreen}✓${c.reset}` : `${c.red}✗${c.reset}`
    const line = summary.split('\n')[0]?.slice(0, 140) ?? ''
    write(`${c.cyan}│${c.reset}   ${icon} ${c.dim}${line}${c.reset}\n`)
  },

  intervention(type: string, what: string) {
    if (quiet) return
    write(`${c.cyan}│${c.reset} ${c.yellow}⚠ intervention${c.reset} ${c.dim}${type}: ${what}${c.reset}\n`)
  },

  closeIter() {
    if (quiet) return
    write(`${c.cyan}└─${c.reset}\n`)
  },

  halt(reason: string) {
    if (quiet) return
    write(`\n${c.bold}${c.brightGreen}✓ submit_done${c.reset} ${c.dim}${reason.slice(0, 200)}${c.reset}\n`)
  },

  done(iterations: number) {
    if (quiet) return
    write(`\n${c.bold}${c.brightCyan}━━ done in ${iterations} iterations ━━${c.reset}\n\n`)
  },

  error(where: string, message: string) {
    if (quiet) return
    write(`\n${c.bold}${c.red}✗ error in ${where}${c.reset}\n${c.red}${message.slice(0, 400)}${c.reset}\n`)
  },
}

function shortArgs(name: string, args: Record<string, unknown>): string {
  if (name === 'read' || name === 'edit' || name === 'write') {
    const p = String(args.file_path ?? '')
    return p ? trimMiddle(p, 70) : '(no path)'
  }
  if (name === 'bash') {
    const cmd = String(args.cmd ?? '').replace(/\s+/g, ' ')
    return trimMiddle(cmd, 100)
  }
  if (name === 'glob' || name === 'grep') {
    return `pattern=${String(args.pattern ?? '?').slice(0, 60)}`
  }
  if (name === 'run_tests') {
    return args.runner_cmd ? trimMiddle(String(args.runner_cmd), 80) : `suite=${args.suite ?? 'public'}`
  }
  if (name === 'spawn_subagent') {
    return `role=${args.role ?? '?'} task=${trimMiddle(String(args.task ?? ''), 60)}`
  }
  if (name === 'load_skill') {
    return String(args.name ?? '?')
  }
  if (name === 'submit_done') {
    return trimMiddle(String(args.reason ?? ''), 80)
  }
  const s = JSON.stringify(args)
  return trimMiddle(s, 80)
}

function trimMiddle(s: string, max: number): string {
  if (s.length <= max) return s
  const half = Math.floor((max - 3) / 2)
  return `${s.slice(0, half)}...${s.slice(s.length - half)}`
}
