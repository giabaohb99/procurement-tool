import { describe, expect, it } from 'vitest'

import {
  BUILTIN_CARD_FIELDS,
  DEFAULT_CARD_FIELDS,
  labelFieldId,
  mergeCardFields,
  type CardFields,
} from './view-options'

/**
 * Trường hiện trên thẻ (kiểu *Customize* của Lark).
 *
 * Chỗ dễ hỏng ÂM THẦM: bộ nhãn tùy biến là của TỪNG dự án, còn thứ tự thì nhớ ở
 * `localStorage`. Trộn sai một nhịp là nhãn vừa khai không hiện, hoặc nhãn đã
 * xóa để lại một dòng ma trong menu.
 */

const keys = (fields: CardFields) => fields.map((f) => f.key)

describe('mergeCardFields', () => {
  it('keeps the remembered order instead of resetting to the default one', () => {
    const saved: CardFields = [
      { key: 'due', visible: true },
      { key: 'priority', visible: false },
    ]
    const merged = mergeCardFields(saved, [])
    expect(keys(merged).slice(0, 2)).toEqual(['due', 'priority'])
    expect(merged.find((f) => f.key === 'priority')?.visible).toBe(false)
  })

  it('appends a label field that was just declared, switched ON', () => {
    //  Khai trường mới ở Thiết lập xong mà thẻ không đổi gì thì người dùng tưởng
    //  hỏng — nên nhãn mới phải bật sẵn.
    const merged = mergeCardFields(DEFAULT_CARD_FIELDS, [7])
    expect(keys(merged)).toContain('label:7')
    expect(merged.find((f) => f.key === 'label:7')?.visible).toBe(true)
  })

  it('drops a label field that was deleted, leaving no ghost row', () => {
    const saved: CardFields = [...DEFAULT_CARD_FIELDS, { key: 'label:9', visible: true }]
    expect(keys(mergeCardFields(saved, []))).not.toContain('label:9')
  })

  it('adds a newly shipped builtin field to an old remembered order', () => {
    const merged = mergeCardFields([{ key: 'due', visible: false }], [])
    for (const builtin of BUILTIN_CARD_FIELDS) {
      expect(keys(merged), builtin.key).toContain(builtin.key)
    }
    expect(merged.find((f) => f.key === 'due')?.visible).toBe(false)
  })

  it('never duplicates a key, whatever junk the storage holds', () => {
    const saved: CardFields = [
      { key: 'due', visible: true },
      { key: 'due', visible: false },
      { key: 'label:3', visible: true },
    ]
    const merged = mergeCardFields(saved, [3])
    //  Trùng khóa là React `key` trùng → cảnh báo và dòng nhảy lung tung khi kéo.
    expect(new Set(keys(merged)).size).toBe(keys(merged).length)
  })

  it('survives an empty remembered list and an empty project', () => {
    expect(keys(mergeCardFields([], []))).toEqual(BUILTIN_CARD_FIELDS.map((f) => f.key))
    expect(mergeCardFields([], [1, 2])).toHaveLength(BUILTIN_CARD_FIELDS.length + 2)
  })
})

describe('labelFieldId', () => {
  it('reads the id back only for genuine label keys', () => {
    expect(labelFieldId('label:12')).toBe(12)
    expect(labelFieldId('priority')).toBeNull()
    expect(labelFieldId('due')).toBeNull()
  })

  it.each(['label:0', 'label:-1', 'label:', 'label:1.5', 'label:abc', 'label:1e3'])(
    'rejects the junk key %p rather than inventing a field id',
    (raw) => {
      expect(labelFieldId(raw as never)).toBeNull()
    },
  )
})
