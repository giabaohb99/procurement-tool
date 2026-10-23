import { describe, expect, it } from 'vitest'

import type { InventoryByWarehouse } from '@/modules/procurement/api/procurement-dashboard-api'
import { buildWarehouseValueBars, OTHER_LABEL, UNASSIGNED_LABEL } from './warehouse-value-bars'

function row(code: string, value: number, name = code, lines = 1): InventoryByWarehouse {
  return { warehouse_code: code, warehouse_name: name, value, lines }
}

describe('buildWarehouseValueBars', () => {
  it('keeps the top warehouses and folds the rest into one Khác bar', () => {
    const rows = [row('A', 900), row('B', 800), row('C', 700), row('D', 30), row('E', 20)]
    const bars = buildWarehouseValueBars(rows, 3)

    expect(bars.map((b) => b.label)).toEqual(['A', 'B', 'C', OTHER_LABEL])
    expect(bars.at(-1)?.value).toBe(50)
  })

  it('never makes a Khác bar out of a single leftover warehouse — shows it by name instead', () => {
    //  Một cột «Khác» chứa đúng một kho là giấu tên kho đó mà chẳng gọn thêm chút nào.
    const bars = buildWarehouseValueBars([row('A', 3), row('B', 2), row('C', 1)], 2)
    expect(bars.map((b) => b.label)).toEqual(['A', 'B', 'C'])
  })

  it('keeps the total equal to the sum of every warehouse — Khác must not drop money', () => {
    const rows = Array.from({ length: 12 }, (_, i) => row(`K${i}`, (i + 1) * 1_000_000.25))
    const total = rows.reduce((sum, r) => sum + r.value, 0)
    const bars = buildWarehouseValueBars(rows, 5)

    expect(bars.reduce((sum, b) => sum + b.value, 0)).toBeCloseTo(total, 2)
  })

  it('sorts biggest first even if the server order slips', () => {
    const bars = buildWarehouseValueBars([row('small', 1), row('big', 9), row('mid', 5)], 6)
    expect(bars.map((b) => b.label)).toEqual(['big', 'mid', 'small'])
  })

  it('labels rows without a warehouse code as Chưa gán kho', () => {
    const bars = buildWarehouseValueBars([row('', 5, '')], 6)
    expect(bars[0].label).toBe(UNASSIGNED_LABEL)
  })

  it('falls back to the code when the warehouse has no name', () => {
    expect(buildWarehouseValueBars([row('KHO-9', 5, '')], 6)[0].label).toBe('KHO-9')
  })

  it('keeps two warehouses with the same name apart by adding their codes', () => {
    //  Trục danh mục của recharts gộp hai nhãn trùng làm một dòng — mất hẳn một kho.
    const bars = buildWarehouseValueBars([row('K1', 5, 'Kho tổng'), row('K2', 3, 'Kho tổng')], 6)
    expect(bars.map((b) => b.label)).toEqual(['Kho tổng (K1)', 'Kho tổng (K2)'])
  })

  it('leaves out warehouses with nothing in stock, and zero or negative values', () => {
    //  Cột dài 0 chỉ chiếm một dòng vô ích; giá trị âm là dữ liệu hỏng và làm vỡ trục [0, max].
    const bars = buildWarehouseValueBars([row('A', 5), row('B', 0), row('C', -2)], 6)
    expect(bars.map((b) => b.label)).toEqual(['A'])
  })

  it('gives an empty list for no data, a missing key, or nothing positive', () => {
    expect(buildWarehouseValueBars([], 6)).toEqual([])
    expect(buildWarehouseValueBars(undefined, 6)).toEqual([])
    expect(buildWarehouseValueBars([row('A', 0)], 6)).toEqual([])
  })

  it('treats a top size below one as one, so the chart never draws only Khác', () => {
    const bars = buildWarehouseValueBars([row('A', 3), row('B', 2), row('C', 1)], 0)
    expect(bars[0].label).toBe('A')
    expect(bars.at(-1)?.label).toBe(OTHER_LABEL)
  })
})
