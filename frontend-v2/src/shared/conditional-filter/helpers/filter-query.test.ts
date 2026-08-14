import { describe, expect, it } from 'vitest'

import type { FilterConfig, FilterRow, FilterState, OperatorType } from '../types'
import { buildRestQuery } from './query-builder'
import { deserializeUrlToFilters, serializeFiltersToUrl } from './serializer'

const FIELDS: FilterConfig['fields'] = [
  { name: 'name', label: 'Tên', type: 'text' },
  { name: 'total_amount', label: 'Thành tiền', type: 'number' },
  { name: 'status', label: 'Trạng thái', type: 'select' },
  { name: 'expected_date', label: 'Ngày cần', type: 'date' },
  // Tên cột tự chứa `__`: backend tách hậu tố bằng lần `__` CUỐI cùng.
  { name: 'supplier__code', label: 'Mã NCC', type: 'text' },
]

const config: FilterConfig = { fields: FIELDS }

function field(name: string) {
  const found = FIELDS.find((item) => item.name === name)
  if (!found) throw new Error(`Test viết sai tên trường: ${name}`)
  return found
}

function row(name: string, operator: OperatorType, value: FilterRow['value']): FilterRow {
  return { id: `row-${name}-${operator}`, field: field(name), operator, value }
}

function state(rows: FilterRow[], conjunction: FilterState['conjunction'] = 'and') {
  return { rows, conjunction }
}

describe('buildRestQuery', () => {
  it('dịch operator thành hậu tố param của backend', () => {
    expect(
      buildRestQuery(
        state([
          row('name', 'contains', 'bàn'),
          row('total_amount', 'gte', 1_000_000),
          row('status', 'is_not', 'draft'),
        ]),
      ),
    ).toEqual({
      name__contains: 'bàn',
      total_amount__gte: '1000000',
      status__ne: 'draft',
    })
  })

  it('"để trống" / "có giá trị" dùng chung hậu tố isnull, phân biệt bằng true/false', () => {
    expect(buildRestQuery(state([row('expected_date', 'is_empty', null)]))).toEqual({
      expected_date__isnull: 'true',
    })
    expect(buildRestQuery(state([row('expected_date', 'is_not_empty', null)]))).toEqual({
      expected_date__isnull: 'false',
    })
  })

  it('between và in nối bằng dấu phẩy', () => {
    expect(
      buildRestQuery(
        state([
          row('expected_date', 'between', ['2026-08-01', '2026-08-31']),
          row('status', 'in', ['draft', 'approved']),
        ]),
      ),
    ).toEqual({
      expected_date__between: '2026-08-01,2026-08-31',
      status__in: 'draft,approved',
    })
  })

  it('dòng chưa nhập xong bị bỏ qua, không làm hỏng danh sách', () => {
    const rows: FilterRow[] = [
      { id: 'a', field: null, operator: null, value: null },
      row('name', 'contains', ''), // chưa gõ gì
      row('expected_date', 'between', ['', '']), // hở cả hai đầu
      row('status', 'in', []), // chưa chọn gì
      row('name', 'contains', 'ghế'), // dòng duy nhất hợp lệ
    ]
    expect(buildRestQuery(state(rows))).toEqual({ name__contains: 'ghế' })
  })

  it('chỉ gửi conjunction=or, và chỉ khi có từ 2 điều kiện trở lên', () => {
    const two = state([row('name', 'contains', 'bàn'), row('status', 'is', 'draft')], 'or')
    expect(buildRestQuery(two).conjunction).toBe('or')

    const one = state([row('name', 'contains', 'bàn')], 'or')
    expect(one).toBeDefined()
    expect(buildRestQuery(one)).toEqual({ name__contains: 'bàn' })

    const and = state([row('name', 'contains', 'bàn'), row('status', 'is', 'draft')])
    expect(buildRestQuery(and).conjunction).toBeUndefined()
  })
})

describe('serializeFiltersToUrl -> deserializeUrlToFilters', () => {
  it('đi một vòng URL rồi quay lại vẫn ra đúng bộ điều kiện đó', () => {
    const original = state(
      [
        row('name', 'contains', 'bàn'),
        row('total_amount', 'gte', 1_000_000),
        row('expected_date', 'between', ['2026-08-01', '2026-08-31']),
        row('status', 'in', ['draft', 'approved']),
        row('supplier__code', 'is', 'NCC-001'),
      ],
      'or',
    )

    const params = serializeFiltersToUrl(original)
    const restored = deserializeUrlToFilters(params, config)

    expect(restored.conjunction).toBe('or')
    // So sánh ở mức query cuối: `id` của dòng sinh ngẫu nhiên nên không so trực tiếp.
    expect(buildRestQuery(restored)).toEqual(buildRestQuery(original))
    expect(restored.rows.map((item) => item.field?.name)).toEqual([
      'name',
      'total_amount',
      'expected_date',
      'status',
      'supplier__code',
    ])
  })

  it('tách hậu tố bằng lần `__` CUỐI, giữ nguyên tên cột có chứa `__`', () => {
    const restored = deserializeUrlToFilters(
      new URLSearchParams('supplier__code__contains=NCC'),
      config,
    )
    expect(restored.rows).toHaveLength(1)
    expect(restored.rows[0].field?.name).toBe('supplier__code')
    expect(restored.rows[0].operator).toBe('contains')
  })

  it('param lạ do người dùng sửa tay URL bị bỏ qua chứ không ném lỗi', () => {
    const restored = deserializeUrlToFilters(
      new URLSearchParams(
        [
          'page=2', // không có `__`
          'khong_ton_tai__eq=1', // trường không khai báo
          'name__khonghieu=x', // hậu tố sai
          'name__contains=bàn', // hợp lệ
        ].join('&'),
      ),
      config,
    )
    expect(buildRestQuery(restored)).toEqual({ name__contains: 'bàn' })
  })

  it('đọc lại isnull ra đúng "để trống" hay "có giá trị"', () => {
    const empty = deserializeUrlToFilters(
      new URLSearchParams('expected_date__isnull=true'),
      config,
    )
    expect(empty.rows[0].operator).toBe('is_empty')
    expect(empty.rows[0].value).toBeNull()

    const notEmpty = deserializeUrlToFilters(
      new URLSearchParams('expected_date__isnull=false'),
      config,
    )
    expect(notEmpty.rows[0].operator).toBe('is_not_empty')
  })

  it('mặc định là AND khi URL không nói gì', () => {
    expect(deserializeUrlToFilters(new URLSearchParams(''), config).conjunction).toBe('and')
  })
})
