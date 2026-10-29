import { describe, expect, it } from 'vitest'

import { buildSubPeriods } from './headcount-plan-periods'
import { describeActualNotes } from './headcount-plan-actual-notes'

const YEAR = buildSubPeriods(1, 1)
const NAMES = new Map([
  ['THUONG_13', 'Thưởng tháng 13'],
  ['QUA_83', 'Quà 8/3'],
])

describe('notes under the actual rows', () => {
  it('names the items with no actual source, so nobody compares the full plan with a partial actual', () => {
    const notes = describeActualNotes({ missing_codes: ['THUONG_13', 'QUA_83'], months_counted: [3, null, null, null] }, YEAR, NAMES)
    expect(notes).toEqual(['Thực tế chưa gồm: Thưởng tháng 13, Quà 8/3.'])
  })

  it('says why there is no comparison when the viewer sees only part of the contracts', () => {
    const notes = describeActualNotes({ missing_codes: [], months_counted: [3], limited_scope: true }, YEAR, NAMES)
    expect(notes[0]).toMatch(/^Không so thực tế/)
  })

  it('falls back to the code when the item is no longer in the plan', () => {
    expect(describeActualNotes({ missing_codes: ['DA_BO'], months_counted: [] }, YEAR, NAMES)).toEqual([
      'Thực tế chưa gồm: DA_BO.',
    ])
  })

  it('flags only the running sub-period — not finished, not future, not one with 0 months counted', () => {
    const notes = describeActualNotes({ missing_codes: [], months_counted: [3, 3, 2, null] }, YEAR, NAMES)
    expect(notes).toEqual(['Q3 đang chạy: tính 2 tháng đã qua.'])
    expect(describeActualNotes({ missing_codes: [], months_counted: [3, 0, null, null] }, YEAR, NAMES)).toEqual([])
  })

  it('says nothing when everything is covered and every counted sub-period is complete', () => {
    expect(describeActualNotes({ missing_codes: [], months_counted: [] }, YEAR, NAMES)).toEqual([])
  })

  it('tolerates a months_counted array shorter than the periods (older server)', () => {
    expect(describeActualNotes({ missing_codes: [], months_counted: [1] }, YEAR, NAMES)).toEqual([
      'Q1 đang chạy: tính 1 tháng đã qua.',
    ])
  })
})
