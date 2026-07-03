import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const HERE = path.dirname(fileURLToPath(import.meta.url))
const patterns = JSON.parse(
  readFileSync(path.join(HERE, '..', '..', 'patterns', 'patterns.json'), 'utf8'))

test('version bumped to 1.1.0', () => {
  assert.equal(patterns.version, '1.1.0')
})

test('has new conversational-hooks category with forced-sass phrases', () => {
  const cat = patterns.categories.find(c => c.id === 'conversational-hooks')
  assert.ok(cat, 'conversational-hooks category exists')
  assert.equal(cat.priority, 'high')
  const joined = JSON.stringify(cat.patterns)
  assert.match(joined, /here.?s the thing/i)
  assert.match(joined, /hot take/i)
})

test('has new ai-lexicon-2025 category with 2025 buzzwords', () => {
  const cat = patterns.categories.find(c => c.id === 'ai-lexicon-2025')
  assert.ok(cat, 'ai-lexicon-2025 category exists')
  const joined = JSON.stringify(cat.patterns)
  assert.match(joined, /empower/i)
  assert.match(joined, /elevate/i)
})

test('all existing category ids preserved (additive only)', () => {
  for (const id of ['inflated-symbolism'])
    assert.ok(patterns.categories.some(c => c.id === id), `${id} still present`)
})
