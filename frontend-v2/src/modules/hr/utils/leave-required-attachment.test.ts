import { describe, expect, it } from 'vitest'

import { listTypesRequiringAttachment } from './leave-required-attachment'

const types = [
  { id: 1, name: 'Phép năm', require_attachment: false },
  { id: 2, name: 'Nghỉ ốm', require_attachment: true },
  { id: 3, name: 'Nghỉ cưới', require_attachment: true },
]

describe('listTypesRequiringAttachment', () => {
  it('returns nothing for an empty form or unchosen lines', () => {
    expect(listTypesRequiringAttachment([], types)).toEqual([])
    expect(listTypesRequiringAttachment([{ leave_type_id: 0, days: 1 }], types)).toEqual([])
  })

  it('ignores types without the flag', () => {
    expect(listTypesRequiringAttachment([{ leave_type_id: 1, days: 2 }], types)).toEqual([])
  })

  it('flags a multi-type request when only one line needs a file', () => {
    const lines = [
      { leave_type_id: 1, days: 2 },
      { leave_type_id: 2, days: 1 },
    ]
    expect(listTypesRequiringAttachment(lines, types)).toEqual(['Nghỉ ốm'])
  })

  it('does not repeat a type listed twice and survives an unknown type id', () => {
    const lines = [
      { leave_type_id: 3, days: 1 },
      { leave_type_id: 3, days: 1 },
      { leave_type_id: 99, days: 1 },
    ]
    expect(listTypesRequiringAttachment(lines, types)).toEqual(['Nghỉ cưới'])
  })
})
