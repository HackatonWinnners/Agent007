import { spawnSync } from 'child_process'

export function autoCommit(opts: { cwd: string; message: string }): void {
  const add = spawnSync('git', ['add', '-A'], { cwd: opts.cwd, stdio: 'ignore' })
  if (add.status !== 0) return
  const diff = spawnSync('git', ['diff', '--cached', '--name-only'], { cwd: opts.cwd })
  const hasStaged = diff.stdout && diff.stdout.toString().trim().length > 0
  if (!hasStaged) return
  // message passed as a separate argv entry - no shell, no interpolation
  spawnSync('git', ['commit', '-m', opts.message], { cwd: opts.cwd, stdio: 'ignore' })
}
