import { describe, expect, it } from 'vitest'

import type { WorkLabelField, WorkMember } from '../types/work'
import { WORK_FIELD_TYPE } from '../types/work'
import { toDraftLabelValues } from './draft-label-value'

function field(fieldType: number): WorkLabelField {
  return {
    id: 7,
    list_id: 1,
    name: 'Trường thử',
    field_type: fieldType,
    system_key: '',
    sort_order: 1,
    value_count: 0,
    options: [],
  }
}

const MEMBERS: WorkMember[] = [
  {
    id: 1,
    employee_id: 42,
    role: 3,
    department_id: null,
    employee_name: 'Trần Thị Nhân Sự',
    employee_code: 'NS01',
  },
]

describe('toDraftLabelValues', () => {
  it('maps a multi-select array to one value per option', () => {
    const values = toDraftLabelValues(field(WORK_FIELD_TYPE.MULTI), [3, 9], [])

    expect(values.map((v) => v.option_id)).toEqual([3, 9])
    expect(values.every((v) => v.field_id === 7)).toBe(true)
  })

  it('resolves a person field to the member name so the cell is not blank', () => {
    const [value] = toDraftLabelValues(field(WORK_FIELD_TYPE.PERSON), 42, MEMBERS)

    expect(value.value_employee_id).toBe(42)
    expect(value.value_employee_name).toBe('Trần Thị Nhân Sự')
  })

  it('keeps a person id that is not in the member list, with an empty name', () => {
    //  Người vừa bị gỡ khỏi dự án trong lúc dòng nháp đang mở: giữ id để không
    //  âm thầm nuốt lựa chọn, tên để trống vì thật sự không tra được.
    const [value] = toDraftLabelValues(field(WORK_FIELD_TYPE.PERSON), 999, MEMBERS)

    expect(value.value_employee_id).toBe(999)
    expect(value.value_employee_name).toBe('')
  })

  it('stores a number as a string, matching what the server returns', () => {
    expect(toDraftLabelValues(field(WORK_FIELD_TYPE.NUMBER), 12.5, [])[0].value_number).toBe('12.5')
  })

  it('keeps 0 — it is a real number, not "chưa đặt"', () => {
    expect(toDraftLabelValues(field(WORK_FIELD_TYPE.NUMBER), 0, [])[0].value_number).toBe('0')
  })

  it('maps date and text straight through', () => {
    expect(toDraftLabelValues(field(WORK_FIELD_TYPE.DATE), '2026-09-01', [])[0].value_date).toBe(
      '2026-09-01',
    )
    expect(toDraftLabelValues(field(WORK_FIELD_TYPE.TEXT), 'ghi chú', [])[0].value_text).toBe(
      'ghi chú',
    )
  })

  it('treats null, undefined and empty string as «chưa đặt»', () => {
    const single = field(WORK_FIELD_TYPE.SINGLE)

    expect(toDraftLabelValues(single, null, [])).toEqual([])
    expect(toDraftLabelValues(single, undefined, [])).toEqual([])
    expect(toDraftLabelValues(single, '', [])).toEqual([])
  })

  it('rejects a value of the wrong shape instead of building a broken row', () => {
    //  Bản nháp cũ trong bộ nhớ, hoặc người dùng bỏ chọn: đừng dựng một dòng
    //  giá trị rỗng rồi gửi lên máy chủ.
    expect(toDraftLabelValues(field(WORK_FIELD_TYPE.MULTI), 5, [])).toEqual([])
    expect(toDraftLabelValues(field(WORK_FIELD_TYPE.PERSON), 'ai đó', MEMBERS)).toEqual([])
    expect(toDraftLabelValues(field(WORK_FIELD_TYPE.DATE), 20260901, [])).toEqual([])
    expect(toDraftLabelValues(field(WORK_FIELD_TYPE.SINGLE), 'ba', [])).toEqual([])
  })

  it('drops non-numeric junk inside a multi-select array', () => {
    const values = toDraftLabelValues(field(WORK_FIELD_TYPE.MULTI), [3, 'x', null, 9], [])

    expect(values.map((v) => v.option_id)).toEqual([3, 9])
  })

  it('returns an empty list for an empty multi-select array', () => {
    expect(toDraftLabelValues(field(WORK_FIELD_TYPE.MULTI), [], [])).toEqual([])
  })
})
