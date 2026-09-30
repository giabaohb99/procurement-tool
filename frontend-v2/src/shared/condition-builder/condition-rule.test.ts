import { describe, expect, it } from 'vitest'

import {
  buildCondition,
  defaultConditionValue,
  describeRow,
  fullRow,
  parseCondition,
  type ConditionField,
} from './condition-rule'

/** Bộ ô kiểu luồng duyệt văn bản: toàn ô danh mục. */
const DOC_FIELDS: ConditionField[] = [
  { name: 'secrecy_level', label: 'Mức mật', ops: ['gte', 'lte', 'eq', 'ne'] },
  { name: 'doc_type_id', label: 'Loại văn bản', ops: ['in', 'not_in'] },
]

/** Bộ ô kiểu điều kiện bỏ qua điều phối YCMH: có phép không-giá-trị, ô số, ô có/không. */
const PR_FIELDS: ConditionField[] = [
  { name: 'handler_dept_id', label: 'Phòng xử lý', ops: ['not_empty', 'empty', 'in', 'not_in'] },
  { name: 'is_urgent', label: 'Đơn gấp', kind: 'bool', ops: ['eq'] },
  { name: 'line_count', label: 'Số dòng hàng', kind: 'number', ops: ['lte', 'gte', 'eq'] },
]

describe('parseCondition', () => {
  it('treats an empty string as no condition, not as a hand-written one', () => {
    expect(parseCondition('', DOC_FIELDS)).toEqual({ rows: [], advanced: false })
    expect(parseCondition('   ', DOC_FIELDS)).toEqual({ rows: [], advanced: false })
  })

  it('reads a one-row condition', () => {
    const result = parseCondition('[{"field":"secrecy_level","op":"gte","value":3}]', DOC_FIELDS)

    expect(result.advanced).toBe(false)
    expect(result.rows).toEqual([{ field: 'secrecy_level', op: 'gte', value: 3 }])
  })

  it('keeps the number list of an "in" row', () => {
    const result = parseCondition('[{"field":"doc_type_id","op":"in","value":[3,5]}]', DOC_FIELDS)

    expect(result.rows).toEqual([{ field: 'doc_type_id', op: 'in', value: [3, 5] }])
  })

  it('flags broken JSON as hand-written instead of silently returning nothing', () => {
    //  Trả rỗng lặng lẽ là bộ chọn ghi đè mất điều kiện người khác đã viết —
    //  luồng đổi hành vi mà không ai bấm gì.
    expect(parseCondition('[{"field":', DOC_FIELDS).advanced).toBe(true)
  })

  it('flags a non-list or an empty list as hand-written', () => {
    expect(parseCondition('{"field":"secrecy_level"}', DOC_FIELDS).advanced).toBe(true)
    expect(parseCondition('[]', DOC_FIELDS).advanced).toBe(true)
    expect(parseCondition('null', DOC_FIELDS).advanced).toBe(true)
  })

  it('flags a field outside the catalogue as hand-written', () => {
    const result = parseCondition('[{"field":"total","op":"gte","value":50000000}]', DOC_FIELDS)

    expect(result.advanced).toBe(true)
    expect(result.rows).toEqual([])
  })

  it('flags an unknown op or a non-numeric value as hand-written', () => {
    expect(
      parseCondition('[{"field":"secrecy_level","op":"like","value":3}]', DOC_FIELDS).advanced,
    ).toBe(true)
    expect(
      parseCondition('[{"field":"secrecy_level","op":"eq","value":"cao"}]', DOC_FIELDS).advanced,
    ).toBe(true)
  })

  it('flags an op the field does not offer as hand-written', () => {
    //  Ô chọn phép chỉ bày phép của ô đó; đọc vào một phép ngoài danh sách thì
    //  ô chọn hiện trống và người dùng không biết điều kiện đang là gì.
    expect(
      parseCondition('[{"field":"secrecy_level","op":"in","value":[3]}]', DOC_FIELDS).advanced,
    ).toBe(true)
  })

  it('flags an empty "in" list as hand-written because it never matches', () => {
    expect(
      parseCondition('[{"field":"doc_type_id","op":"in","value":[]}]', DOC_FIELDS).advanced,
    ).toBe(true)
  })

  it('treats the whole string as hand-written when one row is broken', () => {
    const raw =
      '[{"field":"secrecy_level","op":"gte","value":3},{"field":"total","op":"gte","value":1}]'

    expect(parseCondition(raw, DOC_FIELDS).advanced).toBe(true)
  })

  it('rejects rows that are not objects', () => {
    expect(parseCondition('["secrecy_level"]', DOC_FIELDS).advanced).toBe(true)
    expect(parseCondition('[null]', DOC_FIELDS).advanced).toBe(true)
  })

  it('reads a value-free op and ignores any stray value', () => {
    const result = parseCondition(
      '[{"field":"handler_dept_id","op":"not_empty","value":"rác"}]',
      PR_FIELDS,
    )
    expect(result).toEqual({
      rows: [{ field: 'handler_dept_id', op: 'not_empty', value: null }],
      advanced: false,
    })
  })

  it('reads a yes/no field only from a real JSON boolean', () => {
    expect(parseCondition('[{"field":"is_urgent","op":"eq","value":false}]', PR_FIELDS).rows).toEqual(
      [{ field: 'is_urgent', op: 'eq', value: false }],
    )
    //  Backend so bằng chuỗi: str(False) là "False", nên `0` không bao giờ khớp
    //  — đọc nó thành «Không» là nói dối người dùng.
    expect(parseCondition('[{"field":"is_urgent","op":"eq","value":0}]', PR_FIELDS).advanced).toBe(
      true,
    )
    expect(
      parseCondition('[{"field":"is_urgent","op":"eq","value":"false"}]', PR_FIELDS).advanced,
    ).toBe(true)
  })

  it('reads zero as a real number for a number field', () => {
    expect(parseCondition('[{"field":"line_count","op":"lte","value":0}]', PR_FIELDS).rows).toEqual([
      { field: 'line_count', op: 'lte', value: 0 },
    ])
    expect(
      parseCondition('[{"field":"line_count","op":"lte","value":"2"}]', PR_FIELDS).advanced,
    ).toBe(true)
    expect(
      parseCondition('[{"field":"line_count","op":"lte","value":null}]', PR_FIELDS).advanced,
    ).toBe(true)
  })
})

describe('buildCondition', () => {
  it('returns an empty string when there is no row (always applies)', () => {
    expect(buildCondition([])).toBe('')
  })

  it('drops a scale row with no level chosen (value 0)', () => {
    //  `{"value":0}` là điều kiện không mức nào khớp — bước lặng lẽ không chạy.
    expect(buildCondition([{ field: 'secrecy_level', op: 'gte', value: 0 }])).toBe('')
  })

  it('drops an "in" row with nothing chosen', () => {
    //  Gửi `in: []` xuống backend là điều kiện không bao giờ khớp: bước lặng lẽ
    //  không chạy và người khai tưởng mình khai thiếu ở chỗ khác.
    const raw = buildCondition([
      { field: 'doc_type_id', op: 'in', value: [] },
      { field: 'secrecy_level', op: 'gte', value: 3 },
    ])

    expect(JSON.parse(raw)).toEqual([{ field: 'secrecy_level', op: 'gte', value: 3 }])
  })

  it('round-trips parse then build to the original string', () => {
    const original =
      '[{"field":"secrecy_level","op":"gte","value":3},{"field":"doc_type_id","op":"in","value":[2]}]'
    const rows = parseCondition(original, DOC_FIELDS).rows

    expect(buildCondition(rows, DOC_FIELDS)).toBe(original)
  })

  it('writes value-free ops without a value key, exactly what the backend example expects', () => {
    expect(buildCondition([{ field: 'handler_dept_id', op: 'not_empty', value: null }], PR_FIELDS)).toBe(
      '[{"field":"handler_dept_id","op":"not_empty"}]',
    )
  })

  it('keeps false for yes/no and zero for number fields, drops an empty number', () => {
    const raw = buildCondition(
      [
        { field: 'is_urgent', op: 'eq', value: false },
        { field: 'line_count', op: 'lte', value: 0 },
        { field: 'line_count', op: 'gte', value: null },
      ],
      PR_FIELDS,
    )
    expect(JSON.parse(raw)).toEqual([
      { field: 'is_urgent', op: 'eq', value: false },
      { field: 'line_count', op: 'lte', value: 0 },
    ])
  })

  it('round-trips every shape of the dispatch rule', () => {
    const original =
      '[{"field":"handler_dept_id","op":"in","value":[5,7]},{"field":"is_urgent","op":"eq","value":true},{"field":"line_count","op":"gte","value":3}]'
    expect(buildCondition(parseCondition(original, PR_FIELDS).rows, PR_FIELDS)).toBe(original)
  })
})

describe('fullRow and defaultConditionValue', () => {
  it('starts every kind in a state the user must still fill in, except yes/no and value-free', () => {
    expect(fullRow({ field: 'x', op: 'in', value: defaultConditionValue('in') })).toBe(false)
    expect(fullRow({ field: 'x', op: 'eq', value: defaultConditionValue('eq') })).toBe(false)
    expect(
      fullRow({ field: 'x', op: 'lte', value: defaultConditionValue('lte', 'number') }, 'number'),
    ).toBe(false)
    expect(fullRow({ field: 'x', op: 'eq', value: defaultConditionValue('eq', 'bool') }, 'bool')).toBe(
      true,
    )
    expect(fullRow({ field: 'x', op: 'empty', value: defaultConditionValue('empty') })).toBe(true)
  })

  it('never counts a row without a field as complete', () => {
    expect(fullRow({ field: '', op: 'not_empty', value: null })).toBe(false)
  })

  it('rejects NaN and Infinity from a number box', () => {
    expect(fullRow({ field: 'x', op: 'eq', value: Number.NaN }, 'number')).toBe(false)
    expect(fullRow({ field: 'x', op: 'eq', value: Number.POSITIVE_INFINITY }, 'number')).toBe(false)
  })
})

describe('describeRow', () => {
  it('uses a sentence template per op instead of gluing words together', () => {
    expect(describeRow('gte', 'Mức mật', 'Mật')).toBe('Mức mật từ Mật trở lên')
    expect(describeRow('lte', 'Độ khẩn', 'Khẩn')).toBe('Độ khẩn từ Khẩn trở xuống')
    expect(describeRow('eq', 'Mức mật', 'Nội bộ')).toBe('Mức mật là Nội bộ')
    expect(describeRow('in', 'Loại văn bản', 'Quy chế, Quy trình')).toBe(
      'Loại văn bản thuộc Quy chế, Quy trình',
    )
    expect(describeRow('not_in', 'Pháp nhân', 'DEGO')).toBe('Pháp nhân không thuộc DEGO')
    expect(describeRow('not_empty', 'Phòng xử lý', '')).toBe('Phòng xử lý có giá trị')
    expect(describeRow('empty', 'Phòng xử lý', '')).toBe('Phòng xử lý để trống')
  })
})
