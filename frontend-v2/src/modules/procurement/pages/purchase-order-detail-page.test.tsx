import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { forwardRef } from 'react'
import { createMemoryRouter, RouterProvider } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { PurchaseOrderPayload } from '../api/purchase-order-api'
import type { PurchaseOrderDetail, PurchaseOrderItem } from '../types/purchase-order-detail'
import { createEmptyPurchaseOrder, type PurchaseOrderDraftFromRequest } from '../utils/purchase-order-draft'
import { PurchaseOrderDetailPage } from './purchase-order-detail-page'

/**
 * bao-CR-758 — chuỗi tạo ĐMH từ YCMH rồi lưu trên màn chi tiết v2. Máy chủ giả giữ đơn
 * trong bộ nhớ: POST/PATCH ghi đúng thứ gửi lên, GET trả lại bản đã ghi — y như máy chủ thật,
 * để bài kiểm thấy được chỗ màn hình gửi lên giá trị khác với thứ đang hiện.
 */

const server = vi.hoisted(() => ({
  order: null as PurchaseOrderDetail | null,
  payloads: [] as { method: 'create' | 'update'; payload: PurchaseOrderPayload }[],
}))

function applyPayload(base: PurchaseOrderDetail, payload: PurchaseOrderPayload): PurchaseOrderDetail {
  return {
    ...base,
    ...payload,
    items: payload.items.map((item, index) => ({
      ...item,
      id: item.id ?? 900 + index,
      deliveries: [],
      qty_received: 0,
      qty_remaining: item.qty_order,
      progress_status: 'not_ordered',
    })) as PurchaseOrderItem[],
    import_costs: [],
  } as PurchaseOrderDetail
}

vi.mock('../api/purchase-order-api', () => ({
  purchaseOrderApi: {
    getById: vi.fn(async () => structuredClone(server.order)),
    create: vi.fn(async (payload: PurchaseOrderPayload) => {
      server.payloads.push({ method: 'create', payload })
      server.order = applyPayload(
        { ...createEmptyPurchaseOrder(), id: 1178, code: 'PO01178', status: 'draft' },
        payload,
      )
      return structuredClone(server.order)
    }),
    update: vi.fn(async (_id: number, payload: PurchaseOrderPayload) => {
      server.payloads.push({ method: 'update', payload })
      server.order = applyPayload(server.order as PurchaseOrderDetail, payload)
      return structuredClone(server.order)
    }),
  },
}))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAccess: () => true }),
}))
vi.mock('@/core/telemetry/use-form-telemetry', () => ({
  useFormTelemetry: () => ({ markSubmitted: vi.fn() }),
}))
vi.mock('@/core/telemetry/track-ui-action', () => ({ trackUiAction: vi.fn() }))
vi.mock('@/modules/finance/hooks/use-payment-requests', () => ({
  usePrepayHanging: () => ({ data: undefined }),
}))
vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: () => ({ data: { total: 0, items: [] } }),
}))
vi.mock('@/modules/hr/hooks/use-employees', () => ({
  useEmployees: () => ({ data: { total: 0, items: [] } }),
}))
vi.mock('@/modules/production/hooks/use-suppliers', () => ({
  useSuppliers: () => ({
    data: {
      total: 2,
      items: [
        { code: 'NCC01', name: 'NCC 01', supplier_type: 'goods', vat: 0.08, inspection_days: 0 },
        { code: 'NCC02', name: 'NCC 02', supplier_type: 'goods', vat: 0.1, inspection_days: 5 },
      ],
    },
  }),
}))
vi.mock('../hooks/use-purchase-documents', () => ({
  usePurchaseRequests: () => ({ data: { total: 0, items: [] } }),
}))
vi.mock('../hooks/use-approver-candidates', () => ({
  useApproverCandidates: () => ({
    data: { items: [{ employee_id: 77, code: 'NSU077', name: 'Trưởng phòng A', position: '' }] },
  }),
}))
vi.mock('../hooks/use-survey-request-report', () => ({
  useSurveyRequestReport: () => ({ data: undefined }),
}))
vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestUnits: () => ({ data: { items: [] } }),
  usePurchaseRequestItemGroups: () => ({ data: { items: [] } }),
  usePurchaseRequestWarehouses: () => ({
    data: { items: [{ id: 1, code: 'Dego Cần Thơ', name: 'CÔNG TY TNHH DEGO HOLDING' }] },
  }),
  usePurchaseRequestProducts: () => ({ data: { items: [] } }),
  useProductPurchaseHistory: () => ({ data: { total: 0, items: [] }, isLoading: false }),
  useUploadDeliveryFiles: () => ({ mutateAsync: vi.fn(async () => ({})), isPending: false }),
}))

//  Thẻ con tự gọi mạng, không phải đối tượng của bài này.
vi.mock('../components/survey-report/survey-report-card', () => ({
  SurveyReportCard: forwardRef(() => null),
}))
vi.mock('../components/purchase-order-import-costs-card', () => ({
  PurchaseOrderImportCostsCard: () => null,
}))
vi.mock('../components/purchase-order-payment-requests-card', () => ({
  PurchaseOrderPaymentRequestsCard: () => null,
}))
vi.mock('../components/purchase-order-payment-dialog', () => ({
  PurchaseOrderPaymentDialog: () => null,
}))
vi.mock('../components/document-attachments-card', () => ({ DocumentAttachmentsCard: () => null }))
vi.mock('../components/document-comments', () => ({ DocumentComments: () => null }))
vi.mock('@/shared/audit', () => ({ AuditTimeline: () => null }))
vi.mock('@/modules/dossier/components/required-dossiers-card', () => ({
  RequiredDossiersCard: () => null,
}))

function line(overrides: Partial<PurchaseOrderItem>): PurchaseOrderItem {
  return {
    product_code: 'VT01',
    product_name: 'Vật tư 01',
    invoice_name: '',
    item_group: 'Bao bì',
    spec: '',
    fg_code: '',
    fg_name: '',
    invoice_no: '',
    invoice_date: '',
    document_delivery_date: '',
    supplier_ready: true,
    required_date: '2026-11-20',
    expected_date: '2026-11-20',
    unit: 'Cái',
    qty_request: 10,
    qty_order: 10,
    price: 4250,
    vat: 8,
    warehouse_code: 'Dego Cần Thơ',
    note: '',
    currency: '',
    exchange_rate: 0,
    weight_kg: 0,
    dimension: '',
    deliveries: [],
    ...overrides,
  }
}

const DRAFT_FROM_REQUEST: PurchaseOrderDraftFromRequest = {
  pr_code: 'PYC12112604',
  company_id: 1,
  department: 'Phòng Thu mua',
  nspt: '',
  supplier_code: 'NCC01',
  supplier_name: 'NCC 01',
  vat_rate: 0.08,
  is_urgent: false,
  note: '',
  items: [
    line({ product_code: 'VT01', product_name: 'Vật tư 01', price: 4250 }),
    line({ product_code: 'VT02', product_name: 'Vật tư 02', price: 1350 }),
  ],
}

function renderPage(initialEntry: string | { pathname: string; state: unknown }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  //  Hai đường như `routes.tsx` thật: tạo mới và chi tiết là HAI route nạp lười cùng một trang.
  const lazyPage = async () => ({ Component: PurchaseOrderDetailPage })
  const router = createMemoryRouter(
    [
      { path: '/procurement/purchase-orders/new', lazy: lazyPage },
      { path: '/procurement/purchase-orders/:id', lazy: lazyPage },
    ],
    { initialEntries: [initialEntry] },
  )
  const view = render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  )
  return { ...view, queryClient }
}

function priceInputs(): HTMLInputElement[] {
  const table = screen.getByRole('table')
  return within(table)
    .getAllByRole('textbox')
    .filter((input) => (input as HTMLInputElement).inputMode === 'decimal')
    .filter((_, index) => index % 2 === 1) as HTMLInputElement[]
}

function lastPayload() {
  return server.payloads[server.payloads.length - 1]
}

beforeEach(() => {
  server.order = null
  server.payloads = []
  localStorage.clear()
})

//  Trang thật dựng đủ bảng dòng + thẻ thông tin: chạy chung cả thư mục thì mỗi bài mất vài giây.
describe('PurchaseOrderDetailPage — tạo từ YCMH rồi lưu (bao-CR-758)', { timeout: 30_000 }, () => {
  it('tạo đơn từ YCMH, mở đơn vừa tạo, bấm Lưu: đơn giá giữ nguyên', async () => {
    const user = userEvent.setup()
    renderPage({
      pathname: '/procurement/purchase-orders/new',
      state: { fromPurchaseRequest: DRAFT_FROM_REQUEST },
    })

    await user.click(await screen.findByRole('button', { name: /^Tạo$/ }))
    await waitFor(() => expect(server.payloads).toHaveLength(1))
    expect(lastPayload().payload.items.map((item) => item.price)).toEqual([4250, 1350])

    //  Màn chuyển sang đơn đã lưu — chờ bảng dòng hiện lại.
    await screen.findAllByText('PO01178')
    await user.click(await screen.findByRole('button', { name: /^Lưu$/ }))
    await waitFor(() => expect(server.payloads).toHaveLength(2))
    expect(lastPayload().method).toBe('update')
    expect(lastPayload().payload.items.map((item) => item.price)).toEqual([4250, 1350])
  })

  it('gõ đơn giá mới rồi Lưu: lần lưu mang giá mới, lần lưu kế tiếp vẫn giữ, không cần tải lại trang', async () => {
    const user = userEvent.setup()
    server.order = applyPayload(
      {
        ...createEmptyPurchaseOrder(),
        id: 1178,
        code: 'PO01178',
        status: 'draft',
        company_id: 1,
        supplier_code: 'NCC01',
      },
      { items: DRAFT_FROM_REQUEST.items } as unknown as PurchaseOrderPayload,
    )
    renderPage('/procurement/purchase-orders/1178')
    await screen.findAllByText('PO01178')

    const [first] = priceInputs()
    await user.clear(first)
    await user.type(first, '5000')
    await user.click(screen.getByRole('button', { name: /^Lưu$/ }))
    await waitFor(() => expect(server.payloads).toHaveLength(1))
    expect(lastPayload().payload.items.map((item) => item.price)).toEqual([5000, 1350])

    //  Lưu thêm lần nữa sau khi máy chủ trả bản mới: không được rơi về giá cũ hay về 0.
    await waitFor(() => expect(priceInputs()[0].value).toBe('5.000'))
    const second = priceInputs()[1]
    await user.clear(second)
    await user.type(second, '1400')
    await user.click(screen.getByRole('button', { name: /^Lưu$/ }))
    await waitFor(() => expect(server.payloads).toHaveLength(2))
    expect(lastPayload().payload.items.map((item) => item.price)).toEqual([5000, 1400])
  })
  it('bấm vào ô giá, tab qua cả hàng rồi bấm đúp Lưu, Lưu trong hộp chi tiết dòng: giá không bị đè', async () => {
    const user = userEvent.setup()
    server.order = applyPayload(
      {
        ...createEmptyPurchaseOrder(),
        id: 1178,
        code: 'PO01178',
        status: 'draft',
        company_id: 1,
        supplier_code: 'NCC01',
        pr_code: 'PYC12112604',
      },
      { items: DRAFT_FROM_REQUEST.items } as unknown as PurchaseOrderPayload,
    )
    renderPage('/procurement/purchase-orders/1178')
    await screen.findAllByText('PO01178')
    const inputs = priceInputs()
    await user.click(inputs[0])
    for (let k = 0; k < 12; k += 1) await user.tab()
    await user.click(inputs[1])
    await user.dblClick(screen.getByRole('button', { name: /^Lưu$/ }))
    await waitFor(() => expect(server.payloads.length).toBeGreaterThan(0))
    await new Promise((resolve) => setTimeout(resolve, 200))
    for (const p of server.payloads) expect(p.payload.items.map((item) => item.price)).toEqual([4250, 1350])
    //  Mở hộp chi tiết dòng rồi bấm Lưu đơn ngay trong hộp.
    await user.click(screen.getAllByTitle(/Chi tiết & giao hàng/)[0])
    await user.click(await screen.findByRole('button', { name: 'Lưu đơn' }))
    await new Promise((resolve) => setTimeout(resolve, 200))
    for (const p of server.payloads) expect(p.payload.items.map((item) => item.price)).toEqual([4250, 1350])
  })
  it('chọn trưởng phòng duyệt và đổi NCC trên đơn vừa tạo rồi Lưu: giá giữ nguyên', async () => {
    const user = userEvent.setup()
    renderPage({
      pathname: '/procurement/purchase-orders/new',
      state: { fromPurchaseRequest: DRAFT_FROM_REQUEST },
    })
    await user.click(await screen.findByRole('button', { name: /^Tạo$/ }))
    await screen.findAllByText('PO01178')
    const approver = document.getElementById('po-approver') as HTMLInputElement
    await user.click(approver)
    await user.click(await screen.findByRole('button', { name: /Trưởng phòng A/ }))
    const supplier = document.getElementById('po-supplier') as HTMLInputElement
    await user.click(supplier)
    await user.click(await screen.findByRole('button', { name: /NCC02/ }))
    await user.click(screen.getByRole('button', { name: /^Lưu$/ }))
    await waitFor(() => expect(server.payloads).toHaveLength(2))
    expect(lastPayload().payload.approver_employee_id).toBe(77)
    expect(lastPayload().payload.items.map((item) => item.price)).toEqual([4250, 1350])
  })
  it('mở chi tiết từng dòng gõ Tên trên hóa đơn rồi Lưu: giá giữ nguyên', async () => {
    const user = userEvent.setup()
    renderPage({
      pathname: '/procurement/purchase-orders/new',
      state: { fromPurchaseRequest: DRAFT_FROM_REQUEST },
    })
    await user.click(await screen.findByRole('button', { name: /^Tạo$/ }))
    await screen.findAllByText('PO01178')
    for (let row = 0; row < 2; row += 1) {
      await user.click(screen.getAllByTitle(/Chi tiết & giao hàng/)[row])
      const dialog = await screen.findByRole('dialog')
      const invoice = within(dialog).getAllByRole('textbox')[1]
      await user.type(invoice, 'Tên HĐ')
      await user.click(within(dialog).getByRole('button', { name: 'Đóng' }))
    }
    await user.click(screen.getByRole('button', { name: /^Lưu$/ }))
    await waitFor(() => expect(server.payloads).toHaveLength(2))
    expect(lastPayload().payload.items.map((item) => item.price)).toEqual([4250, 1350])
  })
  it('đang gõ giá mà dữ liệu đơn nạp lại ngầm (thao tác khác làm mới) thì giá vừa gõ không mất', async () => {
    const user = userEvent.setup()
    server.order = applyPayload(
      {
        ...createEmptyPurchaseOrder(),
        id: 1178,
        code: 'PO01178',
        status: 'draft',
        company_id: 1,
        supplier_code: 'NCC01',
      },
      { items: DRAFT_FROM_REQUEST.items } as unknown as PurchaseOrderPayload,
    )
    const { queryClient } = renderPage('/procurement/purchase-orders/1178')
    await screen.findAllByText('PO01178')

    const [first] = priceInputs()
    await user.clear(first)
    await user.type(first, '5000')
    await user.tab()

    //  Ai đó đổi tình trạng hồ sơ / đính tệp -> máy chủ trả bản mới, trang nạp lại ngầm.
    server.order = { ...(server.order as PurchaseOrderDetail), document_status: 'complete' }
    await queryClient.invalidateQueries({ queryKey: ['procurement'] })
    await new Promise((resolve) => setTimeout(resolve, 50))

    expect(priceInputs()[0].value).toBe('5.000')
    await user.click(screen.getByRole('button', { name: /^Lưu$/ }))
    await waitFor(() => expect(server.payloads).toHaveLength(1))
    expect(lastPayload().payload.items.map((item) => item.price)).toEqual([5000, 1350])
  })
})
