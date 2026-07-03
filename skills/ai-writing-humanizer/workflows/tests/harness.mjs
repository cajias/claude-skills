// Workflow harness — load a Workflow .js file, strip `export const meta`,
// wrap the remaining body in an async function, and run with mocked globals.
//
// The injected runtime mirrors what the Workflow host provides:
//   args, phase, log, agent, parallel, pipeline, workflow, budget
//
// Plain Node ESM. node:test + node:assert/strict at the caller. No deps.

import { readFile } from 'node:fs/promises'

const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor

/**
 * Strip the leading `export const meta = { ... }` block from a workflow script.
 * Handles multi-line objects by brace-counting from the first `{` after `meta`.
 * Also tolerates a trailing comma and any number of blank lines after the `}`.
 */
export function stripMetaBlock(src) {
  const metaIdx = src.search(/export\s+const\s+meta\s*=\s*\{/)
  if (metaIdx === -1) return src
  const braceStart = src.indexOf('{', metaIdx)
  let depth = 0
  let inStr = null
  let escape = false
  let end = -1
  for (let i = braceStart; i < src.length; i++) {
    const ch = src[i]
    if (escape) { escape = false; continue }
    if (inStr) {
      if (ch === '\\') { escape = true; continue }
      if (ch === inStr) inStr = null
      continue
    }
    if (ch === '"' || ch === "'" || ch === '`') { inStr = ch; continue }
    if (ch === '{') depth++
    else if (ch === '}') {
      depth--
      if (depth === 0) { end = i; break }
    }
  }
  if (end === -1) throw new Error('harness: unterminated meta block')
  // Consume optional trailing comma + whitespace/newlines after closing brace.
  let tail = end + 1
  while (tail < src.length && /[\s,]/.test(src[tail])) tail++
  return src.slice(0, metaIdx) + src.slice(tail)
}

/**
 * Load a workflow .js file and execute it against mock globals.
 *
 * @param {object} cfg
 * @param {string} cfg.scriptPath - absolute path to the workflow .js
 * @param {*}      cfg.args       - value to pass as the global `args`
 * @param {Function} [cfg.mockAgent]    - (prompt, opts) => any   (default: () => null)
 * @param {Function} [cfg.mockWorkflow] - (name, subArgs) => any  (default: () => null)
 * @param {object}   [cfg.budget]       - { total, spent, remaining }
 * @returns {Promise<{ result: any, error: Error|null, agentCalls: Array, workflowCalls: Array, phases: string[], logs: string[] }>}
 */
export async function runWorkflow({
  scriptPath,
  args,
  mockAgent = () => null,
  mockWorkflow = () => null,
  budget = { total: null, spent: () => 0, remaining: () => Infinity },
} = {}) {
  const raw = await readFile(scriptPath, 'utf8')
  const stripped = stripMetaBlock(raw)

  const agentCalls = []
  const workflowCalls = []
  const phases = []
  const logs = []

  const agent = async (prompt, opts) => {
    const value = await mockAgent(prompt, opts, agentCalls.length)
    agentCalls.push({ prompt, opts, value })
    return value
  }
  const workflowFn = async (name, subArgs) => {
    const value = await mockWorkflow(name, subArgs, workflowCalls.length)
    workflowCalls.push({ name, subArgs, value })
    return value
  }
  const phase = (title) => { phases.push(title) }
  const log = (msg) => { logs.push(String(msg)) }
  const parallel = (thunks) =>
    Promise.all(thunks.map((t) => (typeof t === 'function' ? t() : t)))
  const pipeline = async (items, ...stages) => {
    // Real runtime contract: every stage receives (prevResult, originalItem, index).
    const out = []
    for (let i = 0; i < items.length; i++) {
      let cur = items[i]
      for (const stage of stages) cur = await stage(cur, items[i], i)
      out.push(cur)
    }
    return out
  }

  let result = null
  let error = null
  try {
    const fn = new AsyncFunction(
      'args', 'phase', 'log', 'agent', 'parallel', 'pipeline', 'workflow', 'budget',
      stripped,
    )
    result = await fn(args, phase, log, agent, parallel, pipeline, workflowFn, budget)
  } catch (e) {
    error = e
  }

  return { result, error, agentCalls, workflowCalls, phases, logs }
}
