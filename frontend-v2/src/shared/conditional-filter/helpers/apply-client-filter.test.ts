import { describe, expect, it } from 'vitest'

import { applyClientFilter } from './apply-client-filter'
import type { FilterFieldDefinition, FilterRow, FilterState, FilterValue } from '../types'

const TEN: FilterFieldDefinition = { name: 'ten', label: 'Tên', type: 'text' }
const SO: FilterFieldDefinition = { name: 'so', label: 'Số', type: 'number' }
const NGAY: FilterFieldDefinition = { name: 'ngay', label: 'Ngày', type: 'date' }
const CO: FilterFieldDefinition = { name: 'co', label: 'Cờ', type: 'boolean' }

function state(rows: Partial<FilterRow>[], conjunction: 'and' | 'or' = 'and'): FilterState {
  return {
    conjunction,
    rows: rows.map((row, index) => ({
      id: String(index),
      field: null,
      operator: null,
      value: null as FilterValue,
      ...row,
    })),
  }
}

const HANG = [
  { ten: 'Quy chế bảo mật', so: 5, ngay: '2026-03-01', co: true },
  { ten: 'Quy trình mua hàng', so: 12, ngay: '2026-09-15', co: false },
  { ten: 'Thông báo nghỉ Tết', so: 0, ngay: null, co: false },
]

describe('applyClientFilter', () => {
  it('không có điều kiện nào hợp lệ thì trả nguyên danh sách', () => {
    expect(applyClientFilter(HANG, state([]))).toHaveLength(3)
    //  Dòng thiếu operator chưa phải điều kiện — không được lọc mất gì.
    expect(applyClientFilter(HANG, state([{ field: TEN }]))).toHaveLength(3)
  })

  it('nhiều điều kiện nối bằng VÀ thì phải thỏa hết', () => {
    const ket_qua = applyClientFilter(
      HANG,
      state([
        { field: TEN, operator: 'contains', value: 'quy' },
        { field: SO, operator: 'gt', value: 10 },
      ]),
    )
    expect(ket_qua.map((row) => row.ten)).toEqual(['Quy trình mua hàng'])
  })

  it('nối bằng HOẶC thì chỉ cần thỏa một', () => {
    const ket_qua = applyClientFilter(
      HANG,
      state(
        [
          { field: SO, operator: 'is', value: 5 },
          { field: TEN, operator: 'contains', value: 'tết' },
        ],
        'or',
      ),
    )
    expect(ket_qua).toHaveLength(2)
  })

  it('so khớp chữ không phân biệt hoa thường', () => {
    const ket_qua = applyClientFilter(
      HANG,
      state([{ field: TEN, operator: 'contains', value: 'BẢO MẬT' }]),
    )
    expect(ket_qua).toHaveLength(1)
  })

  describe('để trống / có giá trị', () => {
    it('số 0 và cờ false là CÓ giá trị, không phải để trống', () => {
      //  Lỗi kinh điển: dùng `!value` nên số 0 bị coi là rỗng và biến mất khỏi
      //  kết quả "có giá trị".
      const ket_qua = applyClientFilter(HANG, state([{ field: SO, operator: 'is_not_empty' }]))
      expect(ket_qua).toHaveLength(3)
    })

    it('null là để trống', () => {
      const ket_qua = applyClientFilter(HANG, state([{ field: NGAY, operator: 'is_empty' }]))
      expect(ket_qua.map((row) => row.ten)).toEqual(['Thông báo nghỉ Tết'])
    })
  })

  describe('khoảng hở một đầu', () => {
    it('số: bỏ trống đầu trên thì không chặn phía trên', () => {
      const ket_qua = applyClientFilter(
        HANG,
        state([{ field: SO, operator: 'between', value: ['5', ''] }]),
      )
      expect(ket_qua.map((row) => row.so)).toEqual([5, 12])
    })

    it('ngày: bỏ trống đầu dưới thì không chặn phía dưới', () => {
      const ket_qua = applyClientFilter(
        HANG,
        state([{ field: NGAY, operator: 'between', value: ['', '2026-06-30'] }]),
      )
      expect(ket_qua.map((row) => row.ten)).toEqual(['Quy chế bảo mật'])
    })
  })

  describe('ngày', () => {
    it('so sánh đúng thứ tự thời gian', () => {
      const ket_qua = applyClientFilter(
        HANG,
        state([{ field: NGAY, operator: 'gte', value: '2026-06-01' }]),
      )
      expect(ket_qua.map((row) => row.ten)).toEqual(['Quy trình mua hàng'])
    })

    it('dòng KHÔNG có ngày bị loại khỏi mọi phép so sánh mốc', () => {
      //  Coi như lọt thì dòng trống ngày nằm lẫn trong kết quả "từ ngày X" —
      //  người đọc tưởng nó có ngày trong khoảng.
      const ket_qua = applyClientFilter(
        HANG,
        state([{ field: NGAY, operator: 'lte', value: '2030-01-01' }]),
      )
      expect(ket_qua.map((row) => row.ten)).not.toContain('Thông báo nghỉ Tết')
    })

    it('mốc ngày khớp được cả giá trị có kèm giờ', () => {
      const hang = [{ ngay: '2026-03-01T08:30:00' }]
      const ket_qua = applyClientFilter(
        hang,
        state([{ field: NGAY, operator: 'is', value: '2026-03-01' }]),
      )
      expect(ket_qua).toHaveLength(1)
    })
  })

  it('cờ đúng/sai nhận cả chuỗi "true" từ ô chọn', () => {
    const ket_qua = applyClientFilter(
      HANG,
      state([{ field: CO, operator: 'is', value: 'true' }]),
    )
    expect(ket_qua.map((row) => row.ten)).toEqual(['Quy chế bảo mật'])
  })

  it('operator không đánh giá được thì LOẠI dòng, không cho lọt', () => {
    //  Cho lọt là người dùng tưởng đã lọc mà đang nhìn nguyên danh sách — sai
    //  mà không có dấu hiệu gì.
    const ket_qua = applyClientFilter(
      HANG,
      state([{ field: TEN, operator: 'gt', value: 'x' }]),
    )
    expect(ket_qua).toHaveLength(0)
  })
})
