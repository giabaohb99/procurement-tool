import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type {
  LandedCostAmounts,
  LandedCostItemRow,
  LandedCostOrderRow,
  LandedCostReport,
} from '../types/import-landed-cost'
import { LandedCostItemCards, LandedCostOrderCards } from './import-landed-cost-cards'

const COST_TYPES = [
  { code: 1, no: '2.1', label: 'Cước biển' },
  { code: 2, no: '2.2', label: 'Phí lưu bãi' },
]

function amounts(overrides: Partial<LandedCostAmounts> = {}): LandedCostAmounts {
  return {
    qty_total: 1_000,
    weight_total: 2_500,
    currency: 'USD',
    currency_mixed: false,
    goods_amount: 12_345.67,
    goods_base: 312_000_000,
    //  Phí lưu bãi = 0: thẻ không in dòng đó, bảng thì vẫn giữ cột.
    by_type: { '1': 18_000_000, '2': 0 },
    cost_total: 18_000_000,
    landed_total: 330_000_000,
    price_per_kg: 132_000,
    ...overrides,
  }
}

function order(overrides: Partial<LandedCostOrderRow> = {}): LandedCostOrderRow {
  return {
    ...amounts(),
    po_id: 501,
    code: 'PO00501',
    order_date: '2026-09-01',
    etd_date: '2026-09-20',
    status: 'approved',
    status_label: 'Đã duyệt',
    note: '',
    supplier_code: 'NCC01',
    supplier_name: 'Shandong Agro Co., Ltd',
    customs_decl_no: '105123456789',
    customs_decl_date: '2026-10-02',
    exchange_rate: 25_270,
    ...overrides,
  }
}

function item(overrides: Partial<LandedCostItemRow> = {}): LandedCostItemRow {
  return {
    po_id: 501,
    code: 'PO00501',
    etd_date: '2026-09-20',
    status_label: 'Đã duyệt',
    item_id: 9001,
    product_code: 'NL-GLY-95',
    product_name: 'Glyphosate 95% TC',
    unit: 'kg',
    qty_order: 2_500,
    weight_kg: 2_500,
    goods_base: 312_000_000,
    by_type: { '1': 18_000_000, '2': 0 },
    cost_base: 18_000_000,
    landed_base: 330_000_000,
    price_per_unit: 132_000,
    price_per_kg: 132_000,
    ...overrides,
  }
}

function report(overrides: Partial<LandedCostReport> = {}): LandedCostReport {
  return {
    cost_types: COST_TYPES,
    orders: [order()],
    totals: { ...amounts(), order_count: 1 },
    items: [item()],
    item_totals: {
      line_count: 1,
      qty_order: 2_500,
      weight_kg: 2_500,
      goods_base: 312_000_000,
      by_type: { '1': 18_000_000, '2': 0 },
      cost_base: 18_000_000,
      landed_base: 330_000_000,
      price_per_kg: 132_000,
    },
    warnings: [],
    ...overrides,
  }
}

describe('LandedCostOrderCards', () => {
  it('turns each pivot column into one card, supplier first, totals card last', () => {
    render(<LandedCostOrderCards data={report()} />)

    expect(screen.getByText('Shandong Agro Co., Ltd')).toBeInTheDocument()
    expect(screen.getByText('PO00501')).toBeInTheDocument()
    expect(
      screen.getByText(/ETD 20\/09\/2026 · TK 105123456789 · 02\/10\/2026/),
    ).toBeInTheDocument()
    expect(screen.getByText(/Tỷ giá 25\.270/)).toBeInTheDocument()
    expect(screen.getByText('TỔNG (1 lô)')).toBeInTheDocument()
    //  Tiền in đủ chữ số ở cả thẻ lô lẫn thẻ TỔNG.
    expect(screen.getAllByText('330.000.000')).toHaveLength(2)
  })

  it('hides zero cost types but keeps the non-zero ones and the cost total', () => {
    render(<LandedCostOrderCards data={report()} />)

    expect(screen.getAllByText('2.1. Cước biển')).toHaveLength(2)
    expect(screen.queryByText(/Phí lưu bãi/)).not.toBeInTheDocument()
    expect(screen.getAllByText('2. Chi phí nhập khẩu (vnd)')).toHaveLength(2)
  })

  it('does not print a summed foreign amount when currencies are mixed', () => {
    render(
      <LandedCostOrderCards
        data={report({
          totals: { ...amounts({ currency_mixed: true, goods_amount: 0 }), order_count: 2 },
        })}
      />,
    )

    const totalCard = screen.getByText('TỔNG (1 lô)').parentElement as HTMLElement
    expect(within(totalCard).getByText('Nhiều loại')).toBeInTheDocument()
    expect(within(totalCard).queryByText(/Tiền hàng \(USD\)/)).not.toBeInTheDocument()
  })

  it('says the scope is empty instead of drawing an empty list', () => {
    render(<LandedCostOrderCards data={report({ orders: [] })} />)

    expect(
      screen.getByText('Không có đơn nhập khẩu nào trong phạm vi đã chọn.'),
    ).toBeInTheDocument()
    expect(screen.queryByText(/TỔNG/)).not.toBeInTheDocument()
  })
})

describe('LandedCostItemCards', () => {
  it('shows cost per unit on item cards but never on the totals card', () => {
    render(<LandedCostItemCards data={report()} />)

    expect(screen.getByText('Glyphosate 95% TC')).toBeInTheDocument()
    expect(screen.getByText('NL-GLY-95')).toBeInTheDocument()
    expect(screen.getByText('Số lượng (kg)')).toBeInTheDocument()
    //  Mỗi dòng một đơn vị tính, cộng giá vốn/ĐVT lại là vô nghĩa (bảng cũng để trống).
    expect(screen.getAllByText('Giá vốn/ĐVT (vnd)')).toHaveLength(1)
    expect(screen.getByText('TỔNG (1 dòng)')).toBeInTheDocument()
  })

  it('falls back to the product code when the name is missing', () => {
    render(<LandedCostItemCards data={report({ items: [item({ product_name: '' })] })} />)

    expect(screen.getAllByText('NL-GLY-95')).toHaveLength(2)
  })

  it('says there are no lines instead of drawing an empty list', () => {
    render(<LandedCostItemCards data={report({ items: [] })} />)

    expect(screen.getByText('Không có dòng hàng nào trong phạm vi đã chọn.')).toBeInTheDocument()
  })
})
