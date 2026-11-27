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

  //  bao-CR-801 — màn Lịch sử mua nguyên liệu: cùng bộ cột, khác nhãn hai cột mã / tên; không có chế độ sản phẩm.
  it('raw-material screen relabels the code and name columns and never shows the product columns', () => {
    const material = (productMode: boolean, singleCode = false) =>
      renderHook(() => usePackagingHistoryColumns(productMode, singleCode, true)).result.current
    expect(material(false).map((column) => column.header).slice(0, 4)).toEqual([
      'Lần',
      'Ngày mua',
      'Mã nguyên liệu',
      'Tên nguyên liệu',
    ])
    expect(material(false, true).map((column) => column.header).slice(0, 3)).toEqual([
      'Lần',
      'Ngày mua',
      'Mã nguyên liệu',
    ])
    //  Kể cả bị gọi nhầm với chế độ sản phẩm: không có Mã SP / Thành phần.
    const headers = material(true).map((column) => column.header)
    for (const header of ['Mã SP', 'Tên sản phẩm', 'Thành phần', 'Mã VTBB', 'Tên vật tư']) {
      expect(headers).not.toContain(header)
    }
    //  Phần còn lại y hệt màn VTBB (cùng khóa cột, cùng thứ tự) nên máy chủ nhận đúng các khóa xếp.
    const packaging = renderHook(() => usePackagingHistoryColumns(false, false)).result.current
    expect(material(false).map((column) => column.key)).toEqual(packaging.map((column) => column.key))
    for (const column of material(false).filter((item) => item.sortable)) {
      expect(HISTORY_SORT_KEYS).toContain(column.key)
    }
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
