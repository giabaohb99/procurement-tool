import { describe, expect, it } from 'vitest'

import type { PackagingCodeOption } from '../types/packaging-cost-types'
import {
  buildPackagingCodeMatcher,
  collectPackagingGroups,
  collectSearchGroups,
  sortPackagingCodeOptions,
} from './packaging-code-match'

const option = (code: string, group: string, name = ''): PackagingCodeOption => ({
  code,
  name,
  group,
  usage: 1,
  new: null,
})

const OPTIONS = [
  option('THC0012', 'Thùng', 'Thùng carton 5 lớp'),
  option('NDT0417.2', 'Nhãn thùng', 'Nhãn thùng HH0417'),
  option('NHG0100', 'Nhãn', 'Nhãn chai 1 lít'),
  option('NAP0085', 'Nắp', 'Nắp 28mm đỏ'),
  option('CPT0105', 'Chai', 'Chai PET 1 lít'),
  option('HOP0002', 'Hộp', 'Hộp giấy'),
]
const GROUPS = collectPackagingGroups(OPTIONS)

const pick = (query: string) =>
  OPTIONS.filter(buildPackagingCodeMatcher(query, GROUPS)).map((o) => o.code)

describe('buildPackagingCodeMatcher', () => {
  it('treats a bare group name as a group filter, not a text search', () => {
    expect(pick('chai')).toEqual(['CPT0105'])
  })

  it('maps "nhan" to the Nhãn group only, never also Nhãn thùng (exact name wins)', () => {
    expect(pick('nhan')).toEqual(['NHG0100'])
  })

  it('accepts several groups separated by commas, with or without accents', () => {
    expect(pick('nhãn, thùng').sort()).toEqual(['NHG0100', 'THC0012'])
    expect(pick('nhan thung')).toEqual(['NDT0417.2'])
  })

  it('falls back to an accent-insensitive search when one part is not a group', () => {
    expect(pick('nắp 0085')).toEqual(['NAP0085'])
    expect(pick('NAP 0085')).toEqual(['NAP0085'])
    expect(pick('chai, xyz')).toEqual([])
  })

  it('returns everything for blank or whitespace-only input', () => {
    expect(pick('')).toHaveLength(OPTIONS.length)
    expect(pick('   ')).toHaveLength(OPTIONS.length)
    expect(pick(' , ')).toHaveLength(OPTIONS.length)
  })

  it('searches inside names too, and requires every word to match', () => {
    expect(pick('pet 1 lit')).toEqual(['CPT0105'])
    expect(pick('pet hop')).toEqual([])
  })
})

describe('collectSearchGroups', () => {
  //  Lỗi thật thấy khi mở thử 20/11/2026: định mức chưa có mã thùng nào, gõ "thùng" + Chọn tất cả chọn
  //  nhầm 104 mã Nhãn thùng (tìm chữ khớp tên nhóm "Nhãn thùng").
  it('still reads "thùng" as the Thùng group when no carton code is in the data, so nothing is picked', () => {
    const noCarton = OPTIONS.filter((o) => o.group !== 'Thùng')
    const matcher = buildPackagingCodeMatcher('thùng', collectSearchGroups(noCarton))
    expect(noCarton.filter(matcher)).toEqual([])
  })
})

describe('sortPackagingCodeOptions', () => {
  it('orders bottle, cap, label, carton label, carton first, then other groups', () => {
    expect(sortPackagingCodeOptions(OPTIONS).map((o) => o.group)).toEqual([
      'Chai',
      'Nắp',
      'Nhãn',
      'Nhãn thùng',
      'Thùng',
      'Hộp',
    ])
  })

  it('does not mutate the input array', () => {
    const copy = [...OPTIONS]
    sortPackagingCodeOptions(OPTIONS)
    expect(OPTIONS).toEqual(copy)
  })
})
