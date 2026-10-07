import { describe, expect, it } from 'vitest'

import { filterPlaceholders, formatPlaceholderToken, groupPlaceholders } from './labor-contract-placeholder-groups'

const item = (key: string, group: string) => ({ key, label: key, group, example: '' })

describe('formatPlaceholderToken', () => {
  it('dựng đúng dạng người soạn mẫu gõ vào Word', () => {
    expect(formatPlaceholderToken('ho_ten')).toBe('{{ ho_ten }}')
  })
})

describe('groupPlaceholders', () => {
  it('gom theo nhóm, giữ thứ tự nhóm và thứ tự biến backend trả', () => {
    const out = groupPlaceholders([item('a', 'X'), item('b', 'Y'), item('c', 'X')])
    expect(out.map((g) => g.group)).toEqual(['X', 'Y'])
    expect(out[0].items.map((i) => i.key)).toEqual(['a', 'c'])
  })

  it('danh sách rỗng / null / undefined cho mảng rỗng', () => {
    expect(groupPlaceholders([])).toEqual([])
    expect(groupPlaceholders(null)).toEqual([])
    expect(groupPlaceholders(undefined)).toEqual([])
  })

  it('biến thiếu nhóm rơi vào «Khác» thay vì mất', () => {
    expect(groupPlaceholders([item('a', '')])[0].group).toBe('Khác')
  })
})

//  duoc-CR-606 — ô tìm của khung «Chèn biến».
describe('filterPlaceholders', () => {
  const items = [
    { key: 'ho_ten', label: 'Họ và tên', group: 'Người lao động', example: '' },
    { key: 'luong_co_ban', label: 'Lương cơ bản', group: 'Lương', example: '' },
    { key: 'dia_chi', label: 'Địa chỉ thường trú', group: 'Người lao động', example: '' },
  ]

  it('matches label without accents or case', () => {
    expect(filterPlaceholders(items, 'LUONG').map((i) => i.key)).toEqual(['luong_co_ban'])
    expect(filterPlaceholders(items, 'dia chi').map((i) => i.key)).toEqual(['dia_chi'])
  })

  it('matches the variable key too', () => {
    expect(filterPlaceholders(items, 'ho_ten').map((i) => i.key)).toEqual(['ho_ten'])
  })

  it('keeps everything for an empty or whitespace query and survives null', () => {
    expect(filterPlaceholders(items, '   ')).toHaveLength(3)
    expect(filterPlaceholders(null, 'x')).toEqual([])
    expect(filterPlaceholders(undefined, '')).toEqual([])
  })

  it('returns nothing for a query that matches no variable', () => {
    expect(filterPlaceholders(items, 'zzz')).toEqual([])
  })
})
