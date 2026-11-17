import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { PurchaseRequestDetail } from '../types/purchase-request-detail'
import type { PurchasingPrintData } from '../types/purchasing-print'
import { PurchaseRequestPrintPage } from './purchase-request-print-page'

// duoc-CR-777 — luật HIỆN hai mẫu thu mua ở cấp trang: chỉ bản in mở từ đơn, chỉ khi có
// `purchase_order.read` VÀ lệnh `purchasing-print` thành công; 403/404 thì lặng lẽ giấu.

const state = vi.hoisted(() => ({
  permissions: new Set<string>(),
  purchasing: { isSuccess: false, data: undefined as unknown },
  purchasingCalls: [] as Array<{ id: number; enabled: boolean }>,
}))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string, action: string) => state.permissions.has(`${entity}.${action}`) }),
}))

const purchaseRequest = {
  id: 5,
  code: 'PYC01',
  company_name: 'DEGO',
  request_date: '2026-11-17',
  requester: 'Nguoi Lap YCMH',
  requester_position: '',
  department: '',
  head_of_dept: 'Truong Phong YCMH',
  items: [],
  print_signature_cells: [],
  supplier_pur: { name: '', tax_code: '', contact: '' },
  supplier_req: { name: '', tax_code: '', contact: '' },
  po_lines_unmatched: 0,
} as unknown as PurchaseRequestDetail

vi.mock('../hooks/use-purchase-request', () => ({
  usePurchaseRequest: () => ({ data: purchaseRequest, isLoading: false, isError: false }),
  usePurchaseRequestOfPurchaseOrder: () => ({ data: purchaseRequest, isLoading: false, isError: false }),
}))

vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestPrintWarehouses: () => ({ data: { items: [] } }),
}))

vi.mock('../hooks/use-purchase-order', () => ({
  usePurchaseOrderPurchasingPrint: (id: number, enabled: boolean) => {
    state.purchasingCalls.push({ id, enabled })
    return enabled ? state.purchasing : { isSuccess: false, data: undefined }
  },
}))

const purchasingData: PurchasingPrintData = {
  po_id: 9,
  po_code: 'DMH01',
  order_date: '2026-11-17',
  currency: 'VND',
  proposer: { employee_id: 7, name: 'Nguyen Thu Mua', position: '', department: '', signature: '' },
  manager: { employee_id: 8, name: 'Tran Quan Ly', position: '', signature: '' },
  supplier: { code: '', name: '' },
  supplier_hidden: true,
  items: [],
  subtotal: 0,
  vat: 0,
  total: 0,
}

function renderPage({ fromPo, search = '' }: { fromPo: boolean; search?: string }) {
  render(
    <MemoryRouter initialEntries={[`/print/9${search}`]}>
      <Routes>
        <Route path="/print/:id" element={<PurchaseRequestPrintPage fromPo={fromPo} />} />
      </Routes>
    </MemoryRouter>,
  )
}

async function openPicker() {
  await userEvent.click(screen.getByRole('combobox', { name: 'Mẫu in' }))
  return screen.getAllByRole('option').map((option) => option.textContent)
}

beforeEach(() => {
  state.permissions = new Set(['purchase_order.read'])
  state.purchasing = { isSuccess: true, data: purchasingData }
  state.purchasingCalls = []
})

describe('PurchaseRequestPrintPage — purchasing templates (duoc-CR-777)', () => {
  it('from a purchase order with read permission and data: five templates', async () => {
    renderPage({ fromPo: true })
    expect(await openPicker()).toHaveLength(5)
    expect(state.purchasingCalls.at(-1)).toEqual({ id: 9, enabled: true })
  })

  it('opens on the normal signed template even when purchasing data is available (bao-CR-779)', () => {
    renderPage({ fromPo: true })
    expect(screen.getByRole('combobox', { name: 'Mẫu in' })).toHaveTextContent('Mẫu thường – có chữ ký')
  })

  it('keeps the normal signed template preselected when purchasing data is not available', () => {
    state.purchasing = { isSuccess: false, data: undefined }
    renderPage({ fromPo: true })
    expect(screen.getByRole('combobox', { name: 'Mẫu in' })).toHaveTextContent('Mẫu thường – có chữ ký')
  })

  it('without purchase_order.read the optional call never runs and only three templates show', async () => {
    state.permissions = new Set()
    renderPage({ fromPo: true })
    expect(await openPicker()).toHaveLength(3)
    expect(state.purchasingCalls.every((call) => !call.enabled)).toBe(true)
  })

  it('a failed call (403 / 404) hides the purchasing templates silently', async () => {
    state.purchasing = { isSuccess: false, data: undefined }
    renderPage({ fromPo: true })
    expect(await openPicker()).toHaveLength(3)
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('the normal request print never asks for purchasing data nor shows the templates', async () => {
    renderPage({ fromPo: false })
    expect(await openPicker()).toHaveLength(3)
    expect(state.purchasingCalls.every((call) => !call.enabled)).toBe(true)
  })

  it('?mau=purchasing-signed opens straight on the purchasing template from an order', () => {
    renderPage({ fromPo: true, search: '?mau=purchasing-signed' })
    expect(screen.getByRole('combobox', { name: 'Mẫu in' })).toHaveTextContent('Mẫu thu mua – có chữ ký')
    expect(document.body.textContent).toContain('Người đề xuất: Nguyen Thu Mua')
    expect(document.body.textContent).toContain('Trưởng phòng ban/bộ phận: Tran Quan Ly')
  })

  it('?mau=purchasing-signed on the normal request print falls back to the default template', () => {
    renderPage({ fromPo: false, search: '?mau=purchasing-signed' })
    expect(screen.getByRole('combobox', { name: 'Mẫu in' })).toHaveTextContent('Mẫu thường – có chữ ký')
    expect(document.body.textContent).toContain('Người đề xuất: Nguoi Lap YCMH')
  })

  it('?mau=purchasing-signed while the call failed prints the normal template, not a blank picker', () => {
    state.purchasing = { isSuccess: false, data: undefined }
    renderPage({ fromPo: true, search: '?mau=purchasing-signed' })
    expect(screen.getByRole('combobox', { name: 'Mẫu in' })).toHaveTextContent('Mẫu thường – có chữ ký')
    expect(document.body.textContent).toContain('Trưởng phòng ban/bộ phận: Truong Phong YCMH')
  })
})
