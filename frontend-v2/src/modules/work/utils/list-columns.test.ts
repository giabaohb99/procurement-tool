import { describe, expect, it } from 'vitest'

import type { CardFields } from '../types/view-options'
import type { WorkLabelField } from '../types/work'
import { WORK_FIELD_TYPE } from '../types/work'
import { buildListColumns, isFieldVisible } from './list-columns'

function field(id: number, name: string): WorkLabelField {
  return {
    id,
    list_id: 1,
    name,
    field_type: WORK_FIELD_TYPE.SINGLE,
    system_key: '',
    sort_order: id,
    value_count: 0,
    options: [],
  }
}

const ALL_ON: CardFields = [
  { key: 'assignees', visible: true },
  { key: 'due', visible: true },
  { key: 'subtasks', visible: true },
  { key: 'comments', visible: true },
]

describe('buildListColumns', () => {
  it('turns only the built-ins that ARE columns into columns', () => {
    //  `subtasks` và `comments` là huy hiệu cạnh tên, không phải cột — tách ra
    //  thành cột riêng thì hai cột ấy rỗng ở hầu hết các dòng.
    const columns = buildListColumns(ALL_ON, [])

    expect(columns.map((c) => c.key)).toEqual(['assignees', 'due'])
  })

  it('keeps the order the user dragged in the «Tùy chỉnh» menu', () => {
    const fields: CardFields = [
      { key: 'label:5', visible: true },
      { key: 'due', visible: true },
      { key: 'assignees', visible: true },
    ]
    const columns = buildListColumns(fields, [field(5, 'Phiên bản')])

    expect(columns.map((c) => c.key)).toEqual(['label:5', 'due', 'assignees'])
  })

  it('drops a field the user switched off', () => {
    const fields: CardFields = [
      { key: 'assignees', visible: false },
      { key: 'due', visible: true },
    ]

    expect(buildListColumns(fields, []).map((c) => c.key)).toEqual(['due'])
  })

  it('ignores a saved label key whose field was deleted', () => {
    //  localStorage là bản lưu cũ; trường đã xóa ở màn Thiết lập vẫn còn tên
    //  trong đó. Vẽ ra thì được một cột không tiêu đề, không dữ liệu.
    const fields: CardFields = [{ key: 'label:99', visible: true }]

    expect(buildListColumns(fields, [field(5, 'Phiên bản')])).toEqual([])
  })

  it('names a label column after the field, and carries the field along', () => {
    const version = field(5, 'Phiên bản')
    const [column] = buildListColumns([{ key: 'label:5', visible: true }], [version])

    expect(column.label).toBe('Phiên bản')
    expect(column.field).toBe(version)
  })

  it('gives every column a positive width so none collapses to nothing', () => {
    const columns = buildListColumns(
      [
        { key: 'assignees', visible: true },
        { key: 'due', visible: true },
        { key: 'label:5', visible: true },
      ],
      [field(5, 'Phiên bản')],
    )

    expect(columns).toHaveLength(3)
    expect(columns.every((c) => c.width > 0)).toBe(true)
  })

  it('returns nothing when everything is switched off', () => {
    expect(buildListColumns(ALL_ON.map((f) => ({ ...f, visible: false })), [])).toEqual([])
  })
})

describe('isFieldVisible', () => {
  it('reads the switch for badges that never become columns', () => {
    expect(isFieldVisible(ALL_ON, 'subtasks')).toBe(true)
    expect(isFieldVisible(ALL_ON, 'comments')).toBe(true)
  })

  it('is false for a switched-off field and for one that is not declared at all', () => {
    expect(isFieldVisible([{ key: 'subtasks', visible: false }], 'subtasks')).toBe(false)
    expect(isFieldVisible([], 'subtasks')).toBe(false)
  })
})
