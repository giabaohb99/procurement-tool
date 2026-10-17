import { describe, expect, it } from 'vitest'

import { chapterNumber, clampProgress, cursorAt, reached, typedText } from './chapter-timeline'

describe('cursorAt', () => {
  const path = [
    { at: 0.2, x: 10, y: 10 },
    { at: 0.6, x: 50, y: 90, click: true },
  ]

  it('returns null when a chapter has no cursor path', () => {
    expect(cursorAt([], 0.5)).toBeNull()
  })

  it('stays on the first point before it and on the last point after it', () => {
    expect(cursorAt(path, 0)).toMatchObject({ x: 10, y: 10 })
    expect(cursorAt(path, 1)).toMatchObject({ x: 50, y: 90 })
  })

  it('moves in a straight line between two points', () => {
    const mid = cursorAt(path, 0.4)
    expect(mid?.x).toBeCloseTo(30)
    expect(mid?.y).toBeCloseTo(50)
  })

  it('does not depend on the order the points were written in', () => {
    expect(cursorAt([...path].reverse(), 0.4)?.x).toBeCloseTo(30)
  })

  it('shows the click ring only right after a click point', () => {
    expect(cursorAt(path, 0.59)?.clicking).toBe(false)
    expect(cursorAt(path, 0.61)?.clicking).toBe(true)
    expect(cursorAt(path, 0.7)?.clicking).toBe(false)
  })

  it('treats a broken progress value as the start instead of jumping to NaN coordinates', () => {
    expect(cursorAt(path, Number.NaN)).toMatchObject({ x: 10, y: 10 })
    expect(cursorAt(path, -3)).toMatchObject({ x: 10, y: 10 })
    expect(cursorAt(path, 42)).toMatchObject({ x: 50, y: 90 })
  })

  it('handles two points at the same moment without dividing by zero', () => {
    const state = cursorAt([{ at: 0.5, x: 0, y: 0 }, { at: 0.5, x: 100, y: 100 }], 0.5)
    expect(Number.isFinite(state?.x)).toBe(true)
  })
})

describe('typedText', () => {
  it('types nothing before the start and everything after the end', () => {
    expect(typedText('Tạo bộ', 0.1, 0.2, 0.6)).toBe('')
    expect(typedText('Tạo bộ', 0.9, 0.2, 0.6)).toBe('Tạo bộ')
  })

  it('cuts by character, not by UTF-16 unit, so Vietnamese letters never split', () => {
    const half = typedText('Quy trình', 0.5)
    expect('Quy trình'.startsWith(half)).toBe(true)
    expect(half.length).toBeGreaterThan(0)
  })

  it('shows the full text at once when the typing window is empty or reversed', () => {
    expect(typedText('abc', 0.5, 0.5, 0.5)).toBe('abc')
    expect(typedText('abc', 0.4, 0.5, 0.2)).toBe('')
  })

  it('returns an empty string for empty input at any progress', () => {
    expect(typedText('', 0.7)).toBe('')
  })
})

describe('small helpers', () => {
  it('numbers chapters with two digits starting from 01', () => {
    expect(chapterNumber(0)).toBe('01')
    expect(chapterNumber(8)).toBe('09')
    expect(chapterNumber(-2)).toBe('01')
    expect(chapterNumber(99)).toBe('100')
  })

  it('clamps progress into 0..1', () => {
    expect(clampProgress(Number.POSITIVE_INFINITY)).toBe(0)
    expect(clampProgress(0.3)).toBe(0.3)
    expect(reached(0.5, 0.5)).toBe(true)
    expect(reached(0.49, 0.5)).toBe(false)
  })
})
