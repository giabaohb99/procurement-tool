import { describe, expect, it } from 'vitest'

import { buildPackagingPrintTitle, formatPrintFileDate } from './packaging-print-title'

const DAY = new Date(2026, 10, 5)

describe('buildPackagingPrintTitle', () => {
  it('keeps Vietnamese diacritics and spaces and ends with dd-mm-yyyy', () => {
    expect(buildPackagingPrintTitle('Lịch sử mua hàng', DAY)).toBe(
      'Giá nguyên vật liệu sản xuất - Lịch sử mua hàng - 05-11-2026',
    )
    expect(buildPackagingPrintTitle('Tác động giá bao bì', DAY)).toBe(
      'Giá nguyên vật liệu sản xuất - Tác động giá bao bì - 05-11-2026',
    )
  })

  it('replaces filesystem-forbidden characters and collapses whitespace', () => {
    const title = buildPackagingPrintTitle('A/B: "C"?  D', DAY)
    expect(title).toBe('Giá nguyên vật liệu sản xuất - A B C D - 05-11-2026')
    expect(title).not.toMatch(/[\\/:*?"<>|]/)
  })

  it('drops an empty subtitle without leaving a dangling separator', () => {
    expect(buildPackagingPrintTitle('  ', DAY)).toBe('Giá nguyên vật liệu sản xuất - 05-11-2026')
  })
})

describe('formatPrintFileDate', () => {
  it('zero-pads day and month', () => {
    expect(formatPrintFileDate(new Date(2026, 0, 3))).toBe('03-01-2026')
  })
})
