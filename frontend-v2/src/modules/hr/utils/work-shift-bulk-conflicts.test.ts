import { describe, expect, it } from 'vitest'

import { rosterCell, rosterItem, rosterLeave } from '../components/work-roster-fixture'
import { findLeaveHeldCells } from './work-shift-bulk-conflicts'

const IT = { id: 4, name: 'IT' }

describe('findLeaveHeldCells', () => {
  const items = [
    rosterItem(1, 'An', IT, [rosterCell('2026-10-05', { leave_hold: true }), rosterCell('2026-10-06')]),
    rosterItem(2, 'Bình', IT, [rosterCell('2026-10-05'), rosterCell('2026-10-06', { leave: rosterLeave() })]),
  ]

  it('lists every chosen (person × day) held by a leave, via the flag or the visible leave', () => {
    expect(findLeaveHeldCells(items, [1, 2], ['2026-10-05', '2026-10-06'])).toEqual([
      { employeeId: 1, date: '2026-10-05' },
      { employeeId: 2, date: '2026-10-06' },
    ])
  })

  it('ignores people / days not chosen, unknown ids and days missing from the page', () => {
    expect(findLeaveHeldCells(items, [2], ['2026-10-05'])).toEqual([])
    expect(findLeaveHeldCells(items, [99], ['2026-10-05'])).toEqual([])
    expect(findLeaveHeldCells(items, [1], ['2026-12-31'])).toEqual([])
    expect(findLeaveHeldCells([], [1], ['2026-10-05'])).toEqual([])
  })
})
