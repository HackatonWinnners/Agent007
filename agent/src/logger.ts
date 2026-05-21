import { mkdirSync, appendFileSync } from 'fs'
import { join } from 'path'

type Kind = 'PROMPT' | 'DECISION' | 'COMMAND' | 'TEST_RUN' | 'ERROR' | 'INTERVENTION'

const FILE: Record<Kind, string> = {
  PROMPT: 'prompts.log',
  DECISION: 'decisions.log',
  COMMAND: 'commands.log',
  TEST_RUN: 'test_runs.log',
  ERROR: 'errors.log',
  INTERVENTION: 'human_interventions.log',
}

function ts(): string {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function tail(s: string, max: number): string {
  return s.length <= max ? s : s.slice(s.length - max)
}

export function createLogger(dir: string) {
  mkdirSync(dir, { recursive: true })

  function write(kind: Kind, payload: Record<string, unknown>) {
    const line = `[${ts()}] ${kind} ${JSON.stringify(payload)}\n`
    appendFileSync(join(dir, FILE[kind]), line)
  }

  return {
    prompt(p: { role: 'user' | 'system' | 'assistant'; content: string; target: string }) {
      write('PROMPT', p)
    },
    decision(p: { iteration: number; agentId: string; summary: string; rationale?: string }) {
      write('DECISION', p)
    },
    command(p: { cmd: string; exitCode: number; durationMs: number; stdoutTail: string }) {
      write('COMMAND', { ...p, stdoutTail: tail(p.stdoutTail, 4096) })
    },
    testRun(p: { score: string; failingCategories: string[]; delta?: number }) {
      write('TEST_RUN', p)
    },
    error(p: { where: string; message: string; stack?: string }) {
      write('ERROR', p)
    },
    intervention(p: {
      type: string
      what: string
      why: string
      filesAffected: string[]
      touchedFinalCode: boolean
      notes?: string
    }) {
      write('INTERVENTION', p)
    },
  }
}

export type Logger = ReturnType<typeof createLogger>
