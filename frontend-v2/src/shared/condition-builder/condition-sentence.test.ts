import { describe, expect, it } from 'vitest'

import type { ConditionField } from './condition-rule'
import { conditionText } from './condition-sentence'

const FIELDS: ConditionField[] = [
  { name: 'handler_dept_id', label: 'Phòng xử lý', ops: ['not_empty', 'empty', 'in', 'not_in'] },
  { name: 'is_urgent', label: 'Đơn gấp', kind: 'bool', ops: ['eq'] },
  { name: 'line_count', label: 'Số dòng hàng', kind: 'number', ops: ['lte', 'gte'] },
]

const options = () => [
  { id: 5, label: 'Nhà máy Bắc Ninh' },
  { id: 7, label: 'Nhà máy Long An' },
]

describe('conditionText', () => {
  it('reads the common dispatch rule as one plain sentence', () => {
    expect(
      conditionText([{ field: 'handler_dept_id', op: 'not_empty', value: null }], FIELDS, options),
    ).toBe('Phòng xử lý có giá trị')
  })

  it('joins rows with "và", the way the backend combines them', () => {
    const text = conditionText(
      [
        { field: 'handler_dept_id', op: 'in', value: [5, 7] },
        { field: 'is_urgent', op: 'eq', value: false },
        { field: 'line_count', op: 'lte', value: 0 },
      ],
      FIELDS,
      options,
    )
    expect(text).toBe(
      'Phòng xử lý thuộc Nhà máy Bắc Ninh, Nhà máy Long An và Đơn gấp là Không và Số dòng hàng từ 0 trở xuống',
    )
  })

  it('shows an ellipsis for a row still being filled in, and the raw id for a vanished option', () => {
    expect(
      conditionText(
        [
          { field: 'line_count', op: 'gte', value: null },
          { field: 'handler_dept_id', op: 'in', value: [99] },
        ],
        FIELDS,
        options,
      ),
    ).toBe('Số dòng hàng từ … trở lên và Phòng xử lý thuộc 99')
  })

  it('skips rows whose field is not in the catalogue instead of printing a blank', () => {
    expect(conditionText([{ field: 'ghost', op: 'empty', value: null }], FIELDS, options)).toBe('')
  })
})
