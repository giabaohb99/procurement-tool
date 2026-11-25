// duoc-CR-784 — cột của Lịch sử mua hàng: chế độ mã bắt đầu bằng Lần · Ngày mua · Mã VTBB; chế độ sản phẩm theo bản mẫu `renderHistBySP`
// (Mã SP · Tên sản phẩm · Thành phần · Mã VTBB · Tên vật tư · Lần · Ngày mua); cột xếp được chỉ gửi khóa máy chủ nhận.
import { renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { HISTORY_SORT_KEYS } from '../utils/packaging-history-print'
import { usePackagingHistoryColumns } from './use-packaging-history-columns'

const headers = (productMode: boolean, singleCode = false) =>
  renderHook(() => usePackagingHistoryColumns(productMode, singleCode)).result.current.map((column) => column.header)

describe('usePackagingHistoryColumns', () => {
  it('product mode follows the template column order and labels the value column "Giá trị mua"', () => {
    const list = headers(true)
    expect(list.slice(0, 7)).toEqual(['Mã SP', 'Tên sản phẩm', 'Thành phần', 'Mã VTBB', 'Tên vật tư', 'Lần', 'Ngày mua'])
    expect(list).toContain('Giá trị mua')
    expect(list).not.toContain('Thành tiền')
  })

  it('code mode keeps Lần first and drops the name column for a single code', () => {
    expect(headers(false).slice(0, 4)).toEqual(['Lần', 'Ngày mua', 'Mã VTBB', 'Tên vật tư'])
    expect(headers(false, true).slice(0, 3)).toEqual(['Lần', 'Ngày mua', 'Mã VTBB'])
    expect(headers(false)).not.toContain('Mã SP')
  })

  it('only sorts by keys the server accepts (rule 8)', () => {
    for (const productMode of [false, true]) {
      const columns = renderHook(() => usePackagingHistoryColumns(productMode, false)).result.current
      for (const column of columns.filter((item) => item.sortable)) {
        expect(HISTORY_SORT_KEYS).toContain(column.key)
      }
    }
  })
})
