import { describe, expect, it } from 'vitest'

import {
  describeRemainingTerm,
  parsePesticideToxicity,
  toSentenceCaseIfShouting,
} from './customs-pesticide-display'

describe('parsePesticideToxicity', () => {
  it('splits the two-group source string into GHS and WHO chips', () => {
    expect(
      parsePesticideToxicity(
        'GHS 5 (GHS - Nhóm 5: Rất ít độc/Không độc); WHO 4 (WHO - Nhóm 4: Ít độc)',
      ),
    ).toEqual([
      { code: 'GHS 5', label: 'Rất ít độc/Không độc', severity: 'low' },
      { code: 'WHO 4', label: 'Ít độc', severity: 'low' },
    ])
  })

  it('grades "Độc cao" as high and "Độc trung bình" as medium', () => {
    const items = parsePesticideToxicity(
      'GHS 3 (GHS - Nhóm 3: Độc trung bình); WHO 2 (WHO - Nhóm 2: Độc cao)',
    )
    expect(items.map((i) => i.severity)).toEqual(['medium', 'high'])
  })

  //  110 thuốc trong dữ liệu thật để trống ô này — không được ra một thẻ rỗng.
  it.each(['', null, undefined, ' ; '])('returns no chip for an empty value (%j)', (raw) => {
    expect(parsePesticideToxicity(raw)).toEqual([])
  })

  it('keeps an off-pattern segment verbatim instead of dropping it', () => {
    expect(parsePesticideToxicity('Nhóm III; GHS 4 (GHS - Nhóm 4: Ít độc)')).toEqual([
      { code: '', label: 'Nhóm III', severity: 'unknown' },
      { code: 'GHS 4', label: 'Ít độc', severity: 'low' },
    ])
  })

  it('accepts a WHO class with letters (1a, 1b)', () => {
    expect(parsePesticideToxicity('WHO 1b (WHO - Nhóm Ib: Rất độc)')[0]).toEqual({
      code: 'WHO 1b',
      label: 'Rất độc',
      severity: 'high',
    })
  })
})

describe('toSentenceCaseIfShouting', () => {
  it('turns the all-caps source sector into sentence case, keeping Vietnamese marks', () => {
    expect(toSentenceCaseIfShouting('THUỐC SỬ DỤNG TRONG NÔNG NGHIỆP')).toBe(
      'Thuốc sử dụng trong nông nghiệp',
    )
  })

  it('leaves a mixed-case value untouched (may hold proper names or acronyms)', () => {
    expect(toSentenceCaseIfShouting('Thuốc trừ bệnh WP')).toBe('Thuốc trừ bệnh WP')
  })

  it.each(['', '123', '12% w/w'])('leaves a value without upper-case letters alone (%j)', (value) => {
    expect(toSentenceCaseIfShouting(value)).toBe(value)
  })
})

describe('describeRemainingTerm', () => {
  const today = new Date(2026, 9, 1) // 01/10/2026

  it('counts calendar years and months left', () => {
    expect(describeRemainingTerm('2028-09-25', today)).toBe('còn 1 năm 11 tháng')
    expect(describeRemainingTerm('2028-10-01', today)).toBe('còn 2 năm')
  })

  it('switches to days inside the last month', () => {
    expect(describeRemainingTerm('2026-10-21', today)).toBe('còn 20 ngày')
    expect(describeRemainingTerm('2026-10-01', today)).toBe('Hết hạn hôm nay')
  })

  it('says expired for a past date, never a negative count', () => {
    expect(describeRemainingTerm('2026-09-30', today)).toBe('Đã hết hạn')
  })

  it.each([null, '', 'không rõ'])('returns null without a readable date (%j)', (value) => {
    expect(describeRemainingTerm(value, today)).toBeNull()
  })
})
