import { describe, expect, it } from 'vitest'

import { canMoveWithinGroup, layoutColumnGroups } from './column-groups'

const col = (key: string, group?: string) => ({ key, group })

describe('layoutColumnGroups', () => {
  it('returns null when no column declares a group (table renders as before)', () => {
    expect(layoutColumnGroups([col('a'), col('b')], [])).toBeNull()
  })

  it('merges adjacent columns of the same group into one colSpan segment', () => {
    const layout = layoutColumnGroups(
      [col('code', 'Thông tin'), col('name', 'Thông tin'), col('d1', 'Lần 1'), col('p1', 'Lần 1'), col('avg', 'TB')],
      [],
    )
    expect(layout?.segments.map((s) => [s.label, s.span])).toEqual([
      ['Thông tin', 2],
      ['Lần 1', 2],
      ['TB', 1],
    ])
  })

  it('marks the last column of each group (not of the table)', () => {
    const layout = layoutColumnGroups(
      [col('code', 'Thông tin'), col('d1', 'Lần 1'), col('p1', 'Lần 1'), col('d2', 'Lần 2'), col('avg', 'TB')],
      [],
    )
    expect([...layout!.groupEndKeys]).toEqual(['code', 'p1', 'd2'])
    expect(layout!.segments.map((s) => s.dividerAfter)).toEqual([true, true, true, false])
  })

  it('shrinks the group when a column is hidden (caller passes visible columns only)', () => {
    const visible = [col('code', 'Thông tin'), col('d1', 'Lần 1'), col('p1', 'Lần 1')].filter((c) => c.key !== 'd1')
    expect(layoutColumnGroups(visible, [])?.segments.map((s) => [s.label, s.span])).toEqual([
      ['Thông tin', 1],
      ['Lần 1', 1],
    ])
  })

  it('splits a group at the pinned boundary so the pinned part can stay sticky', () => {
    const layout = layoutColumnGroups(
      [col('code', 'Thông tin'), col('name', 'Thông tin'), col('d1', 'Lần 1')],
      ['code'],
    )
    // the label is written once, on the unpinned part; the pinned part stays blank
    expect(layout?.segments.map((s) => [s.label, s.span, s.pinned])).toEqual([
      ['', 1, true],
      ['Thông tin', 1, false],
      ['Lần 1', 1, false],
    ])
    // only the last segment of the run carries the divider
    expect(layout?.segments.map((s) => s.dividerAfter)).toEqual([false, true, false])
  })

  it('keeps the label on the pinned part when the whole group is pinned', () => {
    const layout = layoutColumnGroups([col('code', 'Thông tin'), col('d1', 'Lần 1')], ['code'])
    expect(layout?.segments.map((s) => [s.label, s.pinned])).toEqual([
      ['Thông tin', true],
      ['Lần 1', false],
    ])
  })

  it('treats ungrouped columns as an unlabeled run', () => {
    const layout = layoutColumnGroups([col('a'), col('b', 'G')], [])
    expect(layout?.segments.map((s) => s.label)).toEqual(['', 'G'])
  })
})

describe('canMoveWithinGroup', () => {
  const cols = [col('a', 'G1'), col('b', 'G1'), col('c', 'G2'), col('x'), col('y')]
  it('allows moves inside one group and blocks moves across groups', () => {
    expect(canMoveWithinGroup(cols, 'a', 'b')).toBe(true)
    expect(canMoveWithinGroup(cols, 'a', 'c')).toBe(false)
  })
  it('treats ungrouped columns as one shared group (old tables keep free reordering)', () => {
    expect(canMoveWithinGroup(cols, 'x', 'y')).toBe(true)
    expect(canMoveWithinGroup(cols.map((c) => ({ key: c.key })), 'a', 'c')).toBe(true)
  })
})
