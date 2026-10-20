import { describe, expect, it } from 'vitest'

import { UI_ACTION_CODE } from '@/core/telemetry/ui-event-codes'

import { abandonRate, actionName, formName, unusedNames, userShare } from './feature-usage-format'

describe('feature usage formatting (duoc-CR-655)', () => {
  it('maps action and form codes to Vietnamese labels, keeping unknown codes visible', () => {
    expect(actionName(UI_ACTION_CODE.EXPORT_EXCEL)).toBe('Xuất Excel')
    expect(formName(1)).toBe('Yêu cầu mua hàng')
    expect(actionName(99999)).toBe('Mã 99999')
  })

  it('computes user share and abandon rate, null (not 0%) when there is no denominator', () => {
    expect(userShare(3, 12)).toBe(0.25)
    expect(userShare(20, 12)).toBe(1)
    expect(userShare(1, 0)).toBeNull()
    expect(abandonRate({ uses: 4, abandons: 1 })).toBe(0.25)
    expect(abandonRate({ uses: 0, abandons: 0 })).toBeNull()
  })

  it('sorts unused names alphabetically in Vietnamese', () => {
    expect(unusedNames([1, 2], (c) => (c === 1 ? 'Ô' : 'A'))).toEqual(['A', 'Ô'])
  })
})
