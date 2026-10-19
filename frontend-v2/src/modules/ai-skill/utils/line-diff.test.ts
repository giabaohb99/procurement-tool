import { describe, expect, it } from 'vitest'

import { MAX_DIFF_CELLS, diffLines } from './line-diff'

describe('diffLines', () => {
  it('marks nothing when both versions are identical', () => {
    const d = diffLines('a\nb\nc', 'a\nb\nc')
    expect(d.added).toBe(0)
    expect(d.removed).toBe(0)
    expect(d.left.every((l) => l.kind === 'same')).toBe(true)
  })

  it('finds one changed line in the middle as one removed plus one added', () => {
    const d = diffLines('mở đầu\ncũ\nkết', 'mở đầu\nmới\nkết')
    expect(d.removed).toBe(1)
    expect(d.added).toBe(1)
    expect(d.left.find((l) => l.kind === 'removed')?.text).toBe('cũ')
    expect(d.right.find((l) => l.kind === 'added')?.text).toBe('mới')
  })

  it('handles empty sides: first publish (old empty) is all added, wiping the body is all removed', () => {
    expect(diffLines('', 'a\nb')).toMatchObject({ added: 2, removed: 0 })
    expect(diffLines('a\nb', '')).toMatchObject({ added: 0, removed: 2 })
    expect(diffLines('', '')).toMatchObject({ added: 0, removed: 0, left: [], right: [] })
  })

  it('treats Windows line endings the same as Unix ones (pasted from Notepad)', () => {
    const d = diffLines('a\r\nb\r\n', 'a\nb\n')
    expect(d.added + d.removed).toBe(0)
  })

  it('keeps duplicate lines aligned instead of reporting the whole block as changed', () => {
    const d = diffLines('-\n-\nx\n-', '-\n-\n-')
    expect(d.removed).toBe(1)
    expect(d.added).toBe(0)
  })

  it('refuses to build a huge table and falls back to plain side by side', () => {
    const side = Math.ceil(Math.sqrt(MAX_DIFF_CELLS)) + 1
    const big = Array.from({ length: side }, (_, i) => `dòng ${i}`).join('\n')
    const d = diffLines(big, `${big}\nthêm`)
    expect(d.tooLarge).toBe(true)
    expect(d.right).toHaveLength(side + 1)
    expect(d.added).toBe(0)
  })
})
