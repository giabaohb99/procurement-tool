// bao-CR-718 — số tệp dự kiến và câu bộ lọc của hộp xác nhận "Xuất toàn bộ theo bộ lọc". Phải khớp cách
// backend chia tệp (`line_export.py`): lệch một là hộp ghi 7 tệp mà chuông báo 8.
import { describe, expect, it } from 'vitest'

import { CUSTOMS_EXPORT_STATUS } from '../types/customs'
import {
  buildFullExportConfirmMessage,
  describeCustomsFilters,
  estimateExportFileCount,
  exportProgressPercent,
  formatExportExpiry,
} from './customs-export'

describe('estimateExportFileCount', () => {
  it('rounds up to whole files of 50.000 rows, exactly like the backend', () => {
    expect(estimateExportFileCount(1)).toBe(1)
    expect(estimateExportFileCount(50_000)).toBe(1)
    expect(estimateExportFileCount(50_001)).toBe(2)
    //  Số đo thật của lần chạy thử backend: 328.374 dòng ra 7 tệp.
    expect(estimateExportFileCount(328_374)).toBe(7)
  })

  it('gives zero files for zero, negative or broken totals instead of NaN / negative counts', () => {
    expect(estimateExportFileCount(0)).toBe(0)
    expect(estimateExportFileCount(-5)).toBe(0)
    expect(estimateExportFileCount(Number.NaN)).toBe(0)
    expect(estimateExportFileCount(Number.POSITIVE_INFINITY)).toBe(0)
  })
})

describe('describeCustomsFilters', () => {
  it('says the whole dataset when no filter is set (blank or whitespace-only values do not count)', () => {
    expect(describeCustomsFilters({})).toBe('Toàn bộ dữ liệu')
    expect(describeCustomsFilters({ q: '   ', hs_code: '' })).toBe('Toàn bộ dữ liệu')
  })

  it('lists active filters in the backend order with the same labels', () => {
    expect(describeCustomsFilters({ hs_code: '3808', q: 'abamectin' })).toBe(
      'Tên hàng: abamectin · Mã HS: 3808',
    )
  })

  it('shows importer / partner NAMES instead of the id list when names are known', () => {
    expect(
      describeCustomsFilters(
        { importer_id: '12,34', partner_id: '9' },
        { importer: 'Cty A, Cty B', partner: '' },
      ),
    ).toBe('Doanh nghiệp: Cty A, Cty B · Đối tác: 9')
  })

  it('translates product kind codes, keeping unknown codes as they are', () => {
    expect(describeCustomsFilters({ product_kind: '1,2,7' })).toBe('Loại hàng: Thành phẩm, Nguyên liệu, 7')
  })
})

describe('buildFullExportConfirmMessage', () => {
  it('states the filter, the row count and the expected file count, plus bell + 7-day keep', () => {
    const message = buildFullExportConfirmMessage(328_374, 'Tên hàng: abamectin')
    expect(message).toContain('Bộ lọc: Tên hàng: abamectin')
    expect(message).toContain('328.374')
    expect(message).toContain('dự kiến 7 tệp')
    expect(message).toContain('báo chuông')
    expect(message).toContain('7 ngày')
  })

  it('handles a single row as one file', () => {
    expect(buildFullExportConfirmMessage(1, 'Toàn bộ dữ liệu')).toContain('dự kiến 1 tệp')
  })
})

describe('exportProgressPercent', () => {
  it('clamps to 0..100 and never divides by zero', () => {
    expect(exportProgressPercent({ rows_done: 0, total_rows: 0, status: CUSTOMS_EXPORT_STATUS.queued })).toBe(0)
    expect(exportProgressPercent({ rows_done: 50, total_rows: 200, status: CUSTOMS_EXPORT_STATUS.running })).toBe(25)
    //  Bảng có thêm dòng sau khi chụp số đếm — không được vượt 100%.
    expect(exportProgressPercent({ rows_done: 300, total_rows: 200, status: CUSTOMS_EXPORT_STATUS.running })).toBe(
      100,
    )
  })

  it('shows a done batch as full even if the counters lag', () => {
    expect(exportProgressPercent({ rows_done: 10, total_rows: 200, status: CUSTOMS_EXPORT_STATUS.done })).toBe(100)
  })
})

describe('formatExportExpiry', () => {
  it('reads null as keep forever', () => {
    expect(formatExportExpiry(null)).toBe('Giữ mãi')
    //  Mốc backend là UTC trần → giờ Việt Nam (+7).
    expect(formatExportExpiry('2026-11-10T08:30:00')).toBe('10/11/2026 15:30')
  })
})
