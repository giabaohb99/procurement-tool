// bao-CR-470 — kiểm các hàm thuần của màn Tra cứu giá hải quan: cổng "đủ bộ lọc để vẽ biểu
// đồ", tham số gửi API, câu bảng rỗng, trạng thái lô nạp, gộp chuỗi so sánh, dải tháng.
import { describe, expect, it } from 'vitest'

import type {
  CustomsCompare,
  CustomsFilters,
  CustomsImportBatch,
  CustomsSeriesPoint,
} from '../types/customs'
import {
  addNamedId,
  buildCompareParams,
  buildCustomsParams,
  buildPriceAxis,
  classifyCoverageMonth,
  cleanCompareTerms,
  CUSTOMS_NEED_FILTER_MESSAGE,
  EMPTY_CUSTOMS_FILTERS,
  formatBannedLabel,
  formatBatchStatus,
  formatCompactQuantity,
  formatThresholdKg,
  formatVnd,
  regulationSeverity,
  removeNamedId,
  sortRegulationsBySeverity,
  splitNamedIds,
  formatCustomsUnit,
  formatCustomsUnitChip,
  formatRegulationListLabel,
  formatUsd,
  hasChartFilter,
  isBatchRunning,
  isBatchUsable,
  isValidHsLookup,
  isValidRegulationLookup,
  mergeCompareSeries,
  resolveLinesEmptyMessage,
  resolveRevertState,
  sumReplacedLines,
} from './customs'

function makeBatch(overrides: Partial<CustomsImportBatch>): CustomsImportBatch {
  return {
    id: 1,
    mode: 0,
    status: 2,
    filename: 'a.xls',
    file_size: 1,
    total_rows: 0,
    created_count: 0,
    deleted_count: 0,
    skipped_count: 0,
    warning_count: 0,
    error_count: 0,
    error_summary: null,
    date_from: '',
    date_to: '',
    date_fixed: 0,
    created_at: null,
    created_by: null,
    created_by_name: null,
    started_at: null,
    finished_at: null,
    ...overrides,
  }
}

function makePoint(period: string, wavg: number | null, count = 5): CustomsSeriesPoint {
  return {
    period,
    label: period,
    count,
    qty: 0,
    min: wavg,
    max: wavg,
    wavg,
    low_data: count > 0 && count < 5,
  }
}

describe('hasChartFilter', () => {
  it('blocks the chart when neither keyword nor HS code is set', () => {
    expect(hasChartFilter(EMPTY_CUSTOMS_FILTERS)).toBe(false)
  })

  it('treats whitespace-only keyword or HS code as empty', () => {
    expect(hasChartFilter({ q: '   ', hs_code: '\t' })).toBe(false)
  })

  it('opens the chart with a keyword alone or an HS code alone', () => {
    expect(hasChartFilter({ q: 'atrazine', hs_code: '' })).toBe(true)
    expect(hasChartFilter({ q: '', hs_code: '3808' })).toBe(true)
  })

  it('does not open the chart on narrowing filters alone (origin, importer, dates)', () => {
    const narrowed: CustomsFilters = {
      ...EMPTY_CUSTOMS_FILTERS,
      origin: 'CN',
      importer_id: '12',
      date_from: '2026-01-01',
    }
    expect(hasChartFilter(narrowed)).toBe(false)
  })

  it('keeps the exact wording the backend returns in its 400 message', () => {
    expect(CUSTOMS_NEED_FILTER_MESSAGE).toBe(
      'Nhập tên hàng / hoạt chất hoặc chọn mã HS để xem biểu đồ.',
    )
  })
})

describe('buildCustomsParams', () => {
  it('sends nothing for an empty filter set', () => {
    expect(buildCustomsParams(EMPTY_CUSTOMS_FILTERS)).toEqual({})
  })

  it('drops blank values and trims the rest', () => {
    expect(
      buildCustomsParams({
        ...EMPTY_CUSTOMS_FILTERS,
        q: '  ATRAZINE ',
        hs_code: ' ',
        importer_id: '7',
        date_to: '2026-09',
      }),
    ).toEqual({ q: 'ATRAZINE', importer_id: '7', date_to: '2026-09' })
  })

  it('keeps an id of "0" because 0 is a real value, not the "all" sentinel', () => {
    expect(buildCustomsParams({ ...EMPTY_CUSTOMS_FILTERS, partner_id: '0' })).toEqual({
      partner_id: '0',
    })
  })
})

describe('resolveLinesEmptyMessage', () => {
  it('says "no customs data yet" only when coverage total is exactly zero', () => {
    expect(resolveLinesEmptyMessage(0, true)).toContain('Chưa có dữ liệu hải quan')
    expect(resolveLinesEmptyMessage(0, true)).toContain('Nạp dữ liệu')
    expect(resolveLinesEmptyMessage(0, false)).toContain('Liên hệ người phụ trách')
  })

  it('says "nothing matches the filter" when data exists or coverage has not loaded', () => {
    expect(resolveLinesEmptyMessage(18243, true)).toContain('Không có dòng hàng nào khớp bộ lọc')
    expect(resolveLinesEmptyMessage(undefined, true)).toContain('Không có dòng hàng nào khớp bộ lọc')
  })
})

describe('batch state helpers', () => {
  it('polls queued and running batches only', () => {
    expect(isBatchRunning(makeBatch({ status: 0 }))).toBe(true)
    expect(isBatchRunning(makeBatch({ status: 1 }))).toBe(true)
    for (const status of [2, 3, 4]) expect(isBatchRunning(makeBatch({ status }))).toBe(false)
  })

  it('applies only finished dry runs that produced rows', () => {
    expect(isBatchUsable(makeBatch({ status: 2, created_count: 10 }))).toBe(true)
    expect(isBatchUsable(makeBatch({ status: 2, created_count: 0 }))).toBe(false)
    expect(isBatchUsable(makeBatch({ status: 3, created_count: 10 }))).toBe(false)
  })

  it('sums replaced rows over usable batches only', () => {
    const batches = [
      makeBatch({ id: 1, status: 2, created_count: 5, deleted_count: 100 }),
      makeBatch({ id: 2, status: 3, created_count: 5, deleted_count: 999 }),
      makeBatch({ id: 3, status: 2, created_count: 0, deleted_count: 50 }),
      makeBatch({ id: 4, status: 2, created_count: 1, deleted_count: 0 }),
    ]
    expect(sumReplacedLines(batches)).toBe(100)
    expect(sumReplacedLines([])).toBe(0)
  })

  it('allows revert only for a finished apply batch that replaced nothing', () => {
    expect(resolveRevertState(makeBatch({ mode: 1, status: 2, deleted_count: 0 }))).toBe('allowed')
    expect(resolveRevertState(makeBatch({ mode: 1, status: 2, deleted_count: 4772 }))).toBe(
      'blocked',
    )
    expect(resolveRevertState(makeBatch({ mode: 0, status: 2, deleted_count: 0 }))).toBe('hidden')
    expect(resolveRevertState(makeBatch({ mode: 1, status: 4, deleted_count: 0 }))).toBe('hidden')
    expect(resolveRevertState(makeBatch({ mode: 1, status: 1, deleted_count: 0 }))).toBe('hidden')
  })

  it('labels batch status by mode', () => {
    expect(formatBatchStatus({ mode: 0, status: 2 })).toBe('Chạy thử xong')
    expect(formatBatchStatus({ mode: 1, status: 2 })).toBe('Đã ghi')
    expect(formatBatchStatus({ mode: 1, status: 4 })).toBe('Đã hoàn tác')
    expect(formatBatchStatus({ mode: 0, status: 3 })).toBe('Lỗi')
    expect(formatBatchStatus({ mode: 0, status: 0 })).toBe('Đang chạy')
  })
})

describe('compare helpers', () => {
  it('trims, drops blanks and case-insensitive duplicates, and caps at five terms', () => {
    expect(cleanCompareTerms([' a ', '', 'A', 'b', 'c', 'd', 'e', 'f'])).toEqual([
      'a',
      'b',
      'c',
      'd',
      'e',
    ])
    expect(cleanCompareTerms([])).toEqual([])
  })

  it('applies the page filters except the keyword, and adds the unit only when chosen', () => {
    const params = buildCompareParams(
      ['atrazine', 'glyphosate'],
      { ...EMPTY_CUSTOMS_FILTERS, q: 'atrazine', origin: 'CN' },
      'quarter',
      '',
    )
    expect(params).toEqual({ origin: 'CN', period: 'quarter', terms: ['atrazine', 'glyphosate'] })
    expect(buildCompareParams(['a', 'b'], EMPTY_CUSTOMS_FILTERS, 'month', 'KGM').chart_unit).toBe(
      'KGM',
    )
  })

  it('merges series on a shared, sorted period axis and leaves missing periods null', () => {
    const data: Pick<CustomsCompare, 'terms'> = {
      terms: [
        { term: 'a', kpi: {}, series: [makePoint('2026-02', 3), makePoint('2026-01', 2)] },
        { term: 'b', kpi: {}, series: [makePoint('2026-03', 9, 2)] },
      ],
    }
    const rows = mergeCompareSeries(data)
    expect(rows.map((row) => row.period)).toEqual(['2026-01', '2026-02', '2026-03'])
    expect(rows[0].values).toEqual([2, null])
    expect(rows[2].values).toEqual([null, 9])
    expect(rows[2].lowData).toEqual([false, true])
  })

  it('keeps an empty period (count 0, wavg null) as a gap, never as zero', () => {
    const rows = mergeCompareSeries({
      terms: [{ term: 'a', kpi: {}, series: [makePoint('2026-07', null, 0)] }],
    })
    expect(rows[0].values).toEqual([null])
    expect(rows[0].counts).toEqual([0])
  })

  it('returns no rows when there are no terms', () => {
    expect(mergeCompareSeries({ terms: [] })).toEqual([])
  })
})

describe('classifyCoverageMonth', () => {
  const today = new Date(2026, 8, 23) // 23/09/2026

  it('marks months after today as future regardless of count', () => {
    expect(classifyCoverageMonth(2026, 9, 0, today)).toBe('future')
    expect(classifyCoverageMonth(2027, 0, 5, today)).toBe('future')
  })

  it('shows the current and past months as filled or empty', () => {
    expect(classifyCoverageMonth(2026, 8, 12, today)).toBe('filled')
    expect(classifyCoverageMonth(2026, 6, 0, today)).toBe('empty')
    expect(classifyCoverageMonth(2025, 11, 0, today)).toBe('empty')
  })
})

describe('formatting', () => {
  it('keeps up to four decimals on USD prices instead of rounding to whole units', () => {
    expect(formatUsd(2.8174)).toBe('2,8174')
    expect(formatUsd(3.1)).toBe('3,1')
  })

  it('shows a dash for missing prices but a real zero for zero', () => {
    expect(formatUsd(null)).toBe('—')
    expect(formatUsd(undefined)).toBe('—')
    expect(formatUsd('')).toBe('—')
    expect(formatUsd(0)).toBe('0')
  })

  it('maps UN/ECE unit codes and passes unknown codes through', () => {
    expect(formatCustomsUnit('KGM')).toBe('kg')
    expect(formatCustomsUnit('LTR')).toBe('lít')
    expect(formatCustomsUnit('XYZ')).toBe('XYZ')
    expect(formatCustomsUnitChip('LTR')).toBe('lít (LTR)')
    expect(formatCustomsUnitChip('UNK')).toBe('UNK')     // mã chưa rõ nghĩa: không đoán
    expect(formatCustomsUnit('')).toBe('')
    expect(formatCustomsUnit(null)).toBe('')
  })

  it('labels regulation list codes and never hides an unknown code', () => {
    expect(formatRegulationListLabel(10)).toBe('TT 75/2025 · Hoạt chất cấm')
    expect(formatRegulationListLabel('4')).toBe('NĐ 24/2026 · Phụ lục IV (ngưỡng khối lượng)')
    expect(formatRegulationListLabel(99)).toBe('Danh sách 99')
    expect(formatRegulationListLabel(null)).toBe('')
  })
})

describe('lookup validation', () => {
  it('requires at least four digits of HS code, ignoring punctuation', () => {
    expect(isValidHsLookup('3808')).toBe(true)
    expect(isValidHsLookup('38.08')).toBe(true)
    expect(isValidHsLookup('380')).toBe(false)
    expect(isValidHsLookup('abcd')).toBe(false)
    expect(isValidHsLookup('')).toBe(false)
  })

  it('requires at least two non-blank characters for a regulation lookup', () => {
    expect(isValidRegulationLookup('Cl')).toBe(true)
    expect(isValidRegulationLookup(' C ')).toBe(false)
    expect(isValidRegulationLookup('')).toBe(false)
  })
})

describe('buildPriceAxis', () => {
  // Lỗi thật ở bản v1: vài dòng 250 USD/lít giữa đám 2–4 USD/lít kéo trục giá lên trần,
  // đường bình quân dẹp sát đáy. Trục phải ôm p25/p75 + bình quân, KHÔNG ôm thấp/cao.
  it('ignores extreme min/max and spans only p25/p75 and the weighted average', () => {
    const axis = buildPriceAxis([
      { p25: 2.5, p75: 3.5, wavg: 3 },
      { p25: 2.8, p75: 4, wavg: 3.2 },
    ])
    expect(axis).not.toBeNull()
    const [low, high] = axis?.domain ?? [0, 0]
    expect(low).toBeLessThanOrEqual(2.5)
    expect(low).toBeGreaterThanOrEqual(0)
    expect(high).toBeGreaterThanOrEqual(4)
    expect(high).toBeLessThan(10)
  })

  it('extends the axis to a weighted average that falls outside p25–p75', () => {
    const axis = buildPriceAxis([{ p25: 2, p75: 3, wavg: 6 }])
    expect(axis?.domain[1]).toBeGreaterThanOrEqual(6)
  })

  it('produces evenly spaced round ticks that start and end on the domain', () => {
    const axis = buildPriceAxis([{ p25: 2.74, p75: 6, wavg: 3.36 }])
    const ticks = axis?.ticks ?? []
    expect(ticks[0]).toBe(axis?.domain[0])
    expect(ticks[ticks.length - 1]).toBe(axis?.domain[1])
    const steps = ticks.slice(1).map((tick, index) => Number((tick - ticks[index]).toFixed(9)))
    expect(new Set(steps).size).toBe(1)
    // Không có đuôi sai số dấu phẩy động kiểu 0.30000000000000004
    for (const tick of ticks) expect(String(tick).length).toBeLessThan(8)
  })

  it('never goes below zero and still draws an axis when every value is equal', () => {
    const axis = buildPriceAxis([{ p25: 0.05, p75: 0.05, wavg: 0.05 }])
    expect(axis?.domain[0]).toBeGreaterThanOrEqual(0)
    expect((axis?.domain[1] ?? 0) > (axis?.domain[0] ?? 0)).toBe(true)
    const zero = buildPriceAxis([{ p25: 0, p75: 0, wavg: 0 }])
    expect(zero?.domain[0]).toBe(0)
    expect((zero?.domain[1] ?? 0) > 0).toBe(true)
  })

  it('skips empty periods and returns null when nothing has a price', () => {
    expect(buildPriceAxis([])).toBeNull()
    expect(buildPriceAxis([{ p25: null, p75: null, wavg: null }])).toBeNull()
    expect(buildPriceAxis([{ wavg: null }])).toBeNull()
    expect(
      buildPriceAxis([
        { p25: null, p75: null, wavg: null },
        { p25: 10, p75: 12, wavg: 11 },
      ])?.domain[1],
    ).toBeGreaterThanOrEqual(12)
  })

  it('falls back to the weighted average when an older backend sends no percentiles', () => {
    expect(buildPriceAxis([{ wavg: 5 }])?.domain[1]).toBeGreaterThanOrEqual(5)
  })
})

describe('formatCompactQuantity', () => {
  it('shortens large quantities so axis labels are not clipped', () => {
    expect(formatCompactQuantity(2_000_000)).toBe('2 tr')
    expect(formatCompactQuantity(1_500_000_000)).toBe('1,5 tỷ')
    expect(formatCompactQuantity(500_000)).toBe('500 N')
    expect(formatCompactQuantity(1_250)).toBe('1,3 N')
  })

  it('keeps small and zero values as they are', () => {
    expect(formatCompactQuantity(0)).toBe('0')
    expect(formatCompactQuantity(999)).toBe('999')
    expect(formatCompactQuantity(12.5)).toBe('12,5')
  })

  it('returns an empty label for non-finite input', () => {
    expect(formatCompactQuantity(Number.NaN)).toBe('')
    expect(formatCompactQuantity(Number.POSITIVE_INFINITY)).toBe('')
  })
})

// bao-CR-477 — ngưỡng khối lượng và mức nghiêm trọng của danh mục hóa chất theo văn bản.
describe('formatThresholdKg', () => {
  it('keeps sub-kilogram thresholds instead of rounding them to zero', () => {
    // Methyl isocyanate có ngưỡng 0,15 kg: làm tròn thành «0 kg» là nói ngược hẳn với luật.
    expect(formatThresholdKg(0.15)).toBe('0,15 kg')
    expect(formatThresholdKg(0.75)).toBe('0,75 kg')
  })

  it('groups thousands the Vietnamese way', () => {
    expect(formatThresholdKg(1000)).toBe('1.000 kg')
    expect(formatThresholdKg(5000)).toBe('5.000 kg')
  })

  it('returns an empty string when there is no usable threshold', () => {
    expect(formatThresholdKg(null)).toBe('')
    expect(formatThresholdKg(undefined)).toBe('')
    expect(formatThresholdKg(Number.NaN)).toBe('')
    expect(formatThresholdKg(-1)).toBe('')
  })

  it('still shows a zero threshold, which is a real value and not "no threshold"', () => {
    expect(formatThresholdKg(0)).toBe('0 kg')
  })
})

describe('formatBannedLabel', () => {
  it('names the year when the source gives one, and says only CẤM otherwise', () => {
    expect(formatBannedLabel(2026)).toBe('CẤM từ 2026')
    expect(formatBannedLabel(null)).toBe('CẤM')
    expect(formatBannedLabel(undefined)).toBe('CẤM')
  })
})

describe('sortRegulationsBySeverity', () => {
  const row = (list_code: number, name: string, threshold_kg: number | null = null) => ({
    list_code,
    name,
    threshold_kg,
  })

  it('puts banned substances first and plain catalogue entries last', () => {
    const sorted = sortRegulationsBySeverity([
      row(1, 'Phụ lục I'),
      row(11, 'Công bố theo lô'),
      row(4, 'Có ngưỡng', 100),
      row(3, 'Tiền chất'),
      row(10, 'Hoạt chất cấm'),
    ])
    expect(sorted.map((r) => r.list_code)).toEqual([10, 3, 4, 11, 1])
  })

  it('ranks the lower threshold first inside the same list', () => {
    const sorted = sortRegulationsBySeverity([
      row(4, 'Methanol', 1000),
      row(4, 'Methyl isocyanate', 0.15),
      row(4, 'Chlorine', 25),
    ])
    expect(sorted.map((r) => r.name)).toEqual(['Methyl isocyanate', 'Chlorine', 'Methanol'])
  })

  it('keeps unknown list codes visible, at the end', () => {
    const sorted = sortRegulationsBySeverity([row(99, 'Mã lạ'), row(2, 'Phụ lục II')])
    expect(sorted.map((r) => r.list_code)).toEqual([2, 99])
    expect(regulationSeverity(99)).toBeGreaterThan(regulationSeverity(2))
  })

  it('returns a new array and leaves the query data untouched', () => {
    const input = [row(1, 'B'), row(10, 'A')]
    const sorted = sortRegulationsBySeverity(input)
    expect(sorted).not.toBe(input)
    expect(input.map((r) => r.list_code)).toEqual([1, 10])
  })

  it('handles an empty list', () => {
    expect(sortRegulationsBySeverity([])).toEqual([])
  })
})

describe('nhiều doanh nghiệp / đối tác trên URL — bao-CR-493', () => {
  it('keeps ids and names in lock-step and never duplicates a chip', () => {
    const one = addNamedId('', '', 12, 'Công ty A')
    expect(one).toEqual({ ids: '12', names: 'Công ty A' })
    const two = addNamedId(one.ids, one.names, 34, 'Công ty B|C,D')
    expect(two).toEqual({ ids: '12,34', names: 'Công ty A|Công ty B C D' })
    expect(addNamedId(two.ids, two.names, '12', 'lại A')).toEqual(two)
  })

  it('splits back into chips and tolerates a missing name', () => {
    expect(splitNamedIds('12,34', 'A')).toEqual([
      { id: '12', name: 'A' },
      { id: '34', name: '' },
    ])
    expect(splitNamedIds('', '')).toEqual([])
    expect(splitNamedIds(' , 5 ,', '|X')).toEqual([{ id: '5', name: '' }])
  })

  it('removes one chip without touching the others', () => {
    expect(removeNamedId('12,34,56', 'A|B|C', '34')).toEqual({ ids: '12,56', names: 'A|C' })
    expect(removeNamedId('12', 'A', '12')).toEqual({ ids: '', names: '' })
  })
})

describe('formatVnd — bao-CR-493', () => {
  it('prints whole dong with thousands separators and a dash when empty', () => {
    expect(formatVnd(78285.4)).toBe('78.285')
    expect(formatVnd(null)).toBe('—')
    expect(formatVnd(0)).toBe('0')
  })
})
