import { describe, expect, it } from 'vitest'

import {
  BENEFIT_OCCASION_PRESETS,
  BENEFIT_PARAM,
  buildClearBenefitParams,
  buildOccasionDateParams,
  buildOccasionPresetParams,
  findActiveOccasionPreset,
  monthOf,
  resolveNextOccurrence,
  resolveOccasionDate,
  type BenefitOccasionPresetId,
} from './benefit-occasion-presets'

const TODAY = new Date(2026, 9, 27) // 27/10/2026
const preset = (id: BenefitOccasionPresetId) => {
  const found = BENEFIT_OCCASION_PRESETS.find((p) => p.id === id)
  if (!found) throw new Error(`thiếu dịp ${id}`)
  return found
}

describe('buildOccasionPresetParams', () => {
  it('8/3 and 20/10 filter women only and jump the occasion to the next such day', () => {
    expect(buildOccasionPresetParams(preset('women_0803'), '2026-10-27', TODAY)).toEqual({
      preset: 'custom', date_from: '2027-03-08', date_to: '2027-03-08', compare: 'none', year: null,
      gender: '2', child_max_age: null, birth_month: null, seniority_years: null,
      occasion_label: 'Quốc tế Phụ nữ 8/3',
    })
    const oct = buildOccasionPresetParams(preset('women_2010'), '2026-10-27', TODAY)
    //  20/10 đã qua 7 ngày → năm sau (lập muộn thì tự chọn lại ngày).
    expect(oct).toMatchObject({ date_to: '2027-10-20', gender: '2', occasion_label: 'Ngày Phụ nữ Việt Nam 20/10' })
  })

  it('1/6 counts children up to 14, mid-autumn up to 15, and neither keeps a gender filter', () => {
    expect(buildOccasionPresetParams(preset('children_0106'), '2026-10-27', TODAY)).toMatchObject({
      date_to: '2027-06-01', child_max_age: '14', gender: null,
    })
    const midAutumn = buildOccasionPresetParams(preset('mid_autumn'), '2026-09-25', TODAY)
    expect(midAutumn).toMatchObject({ child_max_age: '15', gender: null, occasion_label: 'Tết Trung thu' })
    //  Âm lịch: không tự đặt ngày — giữ ngày dịp người lập đã chọn.
    expect(midAutumn).not.toHaveProperty('date_to')
  })

  it('Tết clears every audience filter a previous occasion left behind', () => {
    expect(buildOccasionPresetParams(preset('lunar_new_year'), '2027-02-06', TODAY)).toEqual({
      gender: null, child_max_age: null, birth_month: null, seniority_years: null,
      occasion_label: 'Tết Nguyên đán',
    })
  })

  it('birthday month takes the month of the occasion date, not of today', () => {
    expect(buildOccasionPresetParams(preset('birthday_month'), '2026-12-15', TODAY)).toMatchObject({
      birth_month: '12', occasion_label: 'Sinh nhật tháng 12',
    })
  })

  it('work anniversary asks for whole years 1, 3, 5, 10', () => {
    expect(buildOccasionPresetParams(preset('work_anniversary'), '2026-10-27', TODAY)).toMatchObject({
      seniority_years: '1,3,5,10', gender: null,
    })
  })

  it('only the birthday / children presets need the sensitive permission', () => {
    const sensitive = BENEFIT_OCCASION_PRESETS.filter((p) => p.needsSensitive).map((p) => p.id)
    expect(sensitive.sort()).toEqual(['birthday_month', 'children_0106', 'mid_autumn'])
  })
})

describe('resolveNextOccurrence', () => {
  it('counts today itself, then rolls to next year once the day has passed', () => {
    expect(resolveNextOccurrence(10, 27, TODAY)).toBe('2026-10-27')
    expect(resolveNextOccurrence(10, 26, TODAY)).toBe('2027-10-26')
    expect(resolveNextOccurrence(12, 31, TODAY)).toBe('2026-12-31')
  })
})

describe('buildOccasionDateParams', () => {
  it('sets a single custom day and turns comparison off', () => {
    expect(buildOccasionDateParams('2026-11-20', new URLSearchParams(), '2026-10-27')).toEqual({
      preset: 'custom', date_from: '2026-11-20', date_to: '2026-11-20', compare: 'none', year: null,
    })
  })

  it('moves the birthday month (and its auto label) along with the occasion date', () => {
    const current = new URLSearchParams({ birth_month: '10', occasion_label: 'Sinh nhật tháng 10' })
    expect(buildOccasionDateParams('2026-11-05', current, '2026-10-27')).toMatchObject({
      birth_month: '11', occasion_label: 'Sinh nhật tháng 11',
    })
  })

  it('keeps a birth month the user did not tie to the occasion, and a hand-typed label', () => {
    const unrelated = new URLSearchParams({ birth_month: '3' })
    expect(buildOccasionDateParams('2026-11-05', unrelated, '2026-10-27')).not.toHaveProperty('birth_month')
    const typed = new URLSearchParams({ birth_month: '10', occasion_label: 'Quà sinh nhật quý IV' })
    const next = buildOccasionDateParams('2026-11-05', typed, '2026-10-27')
    expect(next.birth_month).toBe('11')
    expect(next).not.toHaveProperty('occasion_label')
  })
})

describe('findActiveOccasionPreset', () => {
  it('lights the chip whose params are on the URL, and none once a param is edited by hand', () => {
    const p = buildOccasionPresetParams(preset('children_0106'), '2026-10-27', TODAY)
    const url = new URLSearchParams()
    for (const [k, v] of Object.entries(p)) if (v !== null) url.set(k, v)
    expect(findActiveOccasionPreset(url, '2027-06-01')).toBe('children_0106')
    url.set('child_max_age', '10')
    expect(findActiveOccasionPreset(url, '2027-06-01')).toBeNull()
  })

  it('does not light anything on an empty URL', () => {
    expect(findActiveOccasionPreset(new URLSearchParams(), '2026-10-27')).toBeNull()
  })
})

describe('resolveOccasionDate', () => {
  it('reads date_to of a custom period, else the end of the preset (default today)', () => {
    expect(resolveOccasionDate(new URLSearchParams('preset=custom&date_from=2026-03-08&date_to=2026-03-08'))).toBe('2026-03-08')
    expect(resolveOccasionDate(new URLSearchParams(), undefined, TODAY)).toBe('2026-10-27')
    expect(resolveOccasionDate(new URLSearchParams('preset=this_month'), undefined, TODAY)).toBe('2026-10-31')
  })

  it('falls back instead of showing a broken date for a hand-typed link', () => {
    expect(resolveOccasionDate(new URLSearchParams('preset=custom&date_to=hôm-qua'), undefined, TODAY)).toBe('2026-10-27')
    expect(resolveOccasionDate(new URLSearchParams('preset=xyz'), undefined, TODAY)).toBe('2026-10-27')
  })
})

describe('monthOf', () => {
  it('reads the month, and never returns month 0 or 13 for a malformed date', () => {
    expect(monthOf('2026-01-31')).toBe(1)
    expect(monthOf('2026-13-01', TODAY)).toBe(10)
    expect(monthOf('', TODAY)).toBe(10)
  })
})

describe('buildClearBenefitParams', () => {
  it('removes every H1 param in one write and leaves the period alone', () => {
    const cleared = buildClearBenefitParams()
    expect(Object.keys(cleared).sort()).toEqual(Object.values(BENEFIT_PARAM).sort())
    expect(Object.values(cleared).every((v) => v === null)).toBe(true)
    expect(cleared).not.toHaveProperty('date_to')
  })
})
