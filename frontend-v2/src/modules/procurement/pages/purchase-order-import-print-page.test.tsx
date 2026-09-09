import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type { PurchaseOrderPrintData } from '../api/purchase-order-api'
import type { PurchaseOrderItem } from '../types/purchase-order-detail'
import { ORDER_TYPE_IMPORT } from '../types/purchase-order-detail'
import { createEmptyImportCost, createEmptyPurchaseOrder } from '../utils/purchase-order-draft'
import { PurchaseOrderImportPrintPage } from './purchase-order-import-print-page'

// Bản in chỉ nói về CÁCH BÀY số backend đã tính — thay hook bằng một đơn tĩnh.
const printData = vi.hoisted(() => ({ current: null as unknown }))

vi.mock('../hooks/use-purchase-order', () => ({
  usePurchaseOrderPrintData: () => ({
    data: printData.current,
    isLoading: false,
    isError: printData.current === null,
  }),
}))

function item(patch: Partial<PurchaseOrderItem>): PurchaseOrderItem {
  return {
    product_code: 'SP-1',
    product_name: 'Sản phẩm 1',
    invoice_name: '',
    item_group: '',
    spec: '',
    fg_code: '',
    fg_name: '',
    invoice_no: '',
    invoice_date: '',
    document_delivery_date: '',
    supplier_ready: false,
    required_date: '',
    expected_date: '',
    unit: 'Cái',
    qty_request: 0,
    qty_order: 10,
    price: 100,
    vat: 0,
    warehouse_code: '',
    note: '',
    currency: 'USD',
    exchange_rate: 25000,
    weight_kg: 2,
    dimension: '',
    order_total: 1000,
    base_amount: 25_000_000,
    paid_total: 5_000_000,
    deliveries: [],
    ...patch,
  }
}

/** Đơn USD, 1 dòng hàng, 2 khoản chi phí (cước quốc tế + thuế NK), khoản thuế lùi về giá trị. */
function importOrder(): PurchaseOrderPrintData {
  return {
    ...createEmptyPurchaseOrder(),
    id: 360,
    code: 'PO00360',
    order_type: ORDER_TYPE_IMPORT,
    order_type_label: 'Nhập khẩu',
    currency: 'USD',
    exchange_rate: 25000,
    customs_decl_no: '105987654321',
    customs_decl_date: '2026-09-01',
    supplier_name: 'GUANGZHOU JIAXIN PACKAGING',
    nspt: 'Nguyễn Văn A',
    items: [item({ id: 1 })],
    import_costs: [
      {
        ...createEmptyImportCost(),
        id: 11,
        cost_type: 1,
        cost_type_label: 'Cước vận tải quốc tế',
        description: 'Cước biển SITC',
        supplier_code: 'SITC',
        supplier_name: 'SITC LINES',
        currency: 'USD',
        exchange_rate: 25000,
        amount: 100,
        vat: 0,
        base_amount: 2_500_000,
        allocation_method: 1,
        allocation_method_label: 'Theo giá trị',
        invoice_no: 'INV-01',
        invoice_date: '2026-09-02',
      },
      {
        ...createEmptyImportCost(),
        id: 12,
        cost_type: 5,
        cost_type_label: 'Thuế nhập khẩu',
        description: 'Thuế NK theo tờ khai',
        supplier_code: 'NSNN',
        supplier_name: 'Ngân sách nhà nước',
        currency: 'VND',
        exchange_rate: 1,
        amount: 1_000_000,
        vat: 0,
        base_amount: 1_000_000,
        allocation_method: 2,
        allocation_method_label: 'Theo khối lượng',
      },
    ],
    import_cost_summary: {
      goods_base_total: 25_000_000,
      cost_total: 3_500_000,
      paid_total: 1_000_000,
      remaining_total: 2_500_000,
      landed_total: 28_500_000,
      by_type: [],
      by_supplier: [
        {
          supplier_code: 'SITC',
          supplier_name: 'SITC LINES',
          base_amount: 2_500_000,
          paid_amount: 0,
          remaining: 2_500_000,
          count: 1,
          unpaid_payable_ids: [7],
        },
        {
          supplier_code: 'NSNN',
          supplier_name: 'Ngân sách nhà nước',
          base_amount: 1_000_000,
          paid_amount: 1_000_000,
          remaining: 0,
          count: 1,
          unpaid_payable_ids: [],
        },
      ],
    },
    import_cost_allocation: {
      lines: [
        {
          item_id: 1,
          product_code: 'SP-1',
          product_name: 'Sản phẩm 1',
          unit: 'Cái',
          qty_order: 10,
          weight_kg: 2,
          goods_base: 25_000_000,
          cost_base: 3_500_000,
          landed_base: 28_500_000,
          costs: [
            {
              cost_id: 11,
              cost_type_label: 'Cước vận tải quốc tế',
              description: 'Cước biển SITC',
              supplier_code: 'SITC',
              supplier_name: 'SITC LINES',
              allocation_method: 1,
              allocation_method_label: 'Theo giá trị',
              effective_method: 1,
              effective_method_label: 'Theo giá trị',
              ratio: 1,
              base_amount: 2_500_000,
            },
            {
              cost_id: 12,
              cost_type_label: 'Thuế nhập khẩu',
              description: 'Thuế NK theo tờ khai',
              supplier_code: 'NSNN',
              supplier_name: 'Ngân sách nhà nước',
              allocation_method: 2,
              allocation_method_label: 'Theo khối lượng',
              effective_method: 1,
              effective_method_label: 'Theo giá trị',
              ratio: 1,
              base_amount: 1_000_000,
            },
          ],
        },
      ],
      goods_base_total: 25_000_000,
      cost_total: 3_500_000,
      landed_total: 28_500_000,
      warnings: ['Khoản #12 chia theo khối lượng nhưng tổng kg = 0, lùi về theo giá trị'],
    },
    company: { name: 'CÔNG TY DEGO', address: 'Cần Thơ' },
    supplier: { name: 'GUANGZHOU JIAXIN PACKAGING', address: 'Guangzhou', tax_code: '' },
    warehouse: {},
    wh_names: {},
  }
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/print/purchase-order-import/360']}>
      <Routes>
        <Route path="/print/purchase-order-import/:id" element={<PurchaseOrderImportPrintPage />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('PurchaseOrderImportPrintPage', () => {
  it('renders all four blocks with backend totals and marks fallback allocation with (*)', () => {
    printData.current = importOrder()
    renderPage()

    expect(screen.getByRole('heading', { name: 'ĐƠN MUA HÀNG NHẬP KHẨU' })).toBeInTheDocument()
    expect(screen.getByText('A. HÀNG HÓA')).toBeInTheDocument()
    expect(screen.getByText('B. CHI PHÍ LÔ HÀNG')).toBeInTheDocument()
    expect(screen.getByText('C. PHẢI TRẢ THEO TỪNG NHÀ CUNG CẤP')).toBeInTheDocument()
    expect(screen.getByText('D. CHI PHÍ PHÂN BỔ THEO DÒNG HÀNG')).toBeInTheDocument()

    // Đầu phiếu: tỷ giá + tờ khai hải quan kèm ngày.
    expect(screen.getByText(/tỷ giá 25\.000/)).toBeInTheDocument()
    expect(screen.getByText(/105987654321 ngày 01\/09\/2026/)).toBeInTheDocument()

    // Khối B lồng theo loại: mỗi loại một dòng tổng, khoản nằm dưới.
    expect(screen.getByText('Cước vận tải quốc tế (1 khoản)')).toBeInTheDocument()
    expect(screen.getByText('Thuế nhập khẩu (1 khoản)')).toBeInTheDocument()
    // Tổng giá trị lô hàng = 28.500.000 hiện ở B, C và D (ba khối cùng số backend).
    expect(screen.getAllByText('28.500.000').length).toBeGreaterThanOrEqual(3)

    // Khối C: NCC bán hàng là dòng 1, còn lại = tiền hàng − đã trả theo dòng.
    expect(screen.getByText('Tiền hàng (USD)')).toBeInTheDocument()
    expect(screen.getByText('20.000.000')).toBeInTheDocument()

    // Khối D: khoản thuế lùi về "theo giá trị" thì phải có dấu (*) + dòng cảnh báo,
    // không được im lặng in như cách chia người dùng chọn.
    expect(screen.getByText('Theo giá trị (*)')).toBeInTheDocument()
    expect(screen.getByText(/lùi về theo giá trị/)).toBeInTheDocument()
    expect(screen.getByText(/\(\*\) Cách chia đã chọn thiếu cơ sở/)).toBeInTheDocument()
  })

  it('shows the error state instead of crashing when the order cannot be loaded', () => {
    printData.current = null
    renderPage()

    expect(screen.getByText('Không mở được bản in')).toBeInTheDocument()
    expect(screen.queryByText('A. HÀNG HÓA')).not.toBeInTheDocument()
  })

  it('renders empty-state rows when an import order has no costs and no allocation yet', () => {
    printData.current = {
      ...importOrder(),
      import_costs: [],
      import_cost_summary: undefined,
      import_cost_allocation: undefined,
    }
    renderPage()

    expect(screen.getByText('Chưa khai chi phí nào cho lô hàng này')).toBeInTheDocument()
    expect(screen.getByText('Đơn chưa có dòng hàng')).toBeInTheDocument()
    expect(screen.queryByText(/\(\*\) Cách chia đã chọn thiếu cơ sở/)).not.toBeInTheDocument()
  })
})
