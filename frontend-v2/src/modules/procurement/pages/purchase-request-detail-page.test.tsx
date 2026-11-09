import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type {
  PurchaseRequestDetail,
  PurchaseRequestItem,
} from '../types/purchase-request-detail'
import { PurchaseRequestDetailPage } from './purchase-request-detail-page'

/**
 * duoc-CR-741 — trang chi tiết YCMH phải nói ĐÚNG CHỮ bản v1 ở các nút đầu trang và các hộp
 * hỏi lại, và có đủ các hành vi v1 có mà v2 từng thiếu. Chặn ở tầng HOOK dữ liệu (cùng cách
 * `purchase-request-list-page.test.tsx`) và thay các thẻ con nặng bằng bản rỗng: bài này nói
 * về nút + hộp thoại của TRANG, không nói về từng thẻ.
 */

const state = vi.hoisted(() => ({
  data: null as unknown,
  progress: { ordered: {}, pending: {}, orders: {} } as Record<string, unknown>,
  runAction: vi.fn(async () => ({})),
  updateItemStatus: vi.fn(async () => ({})),
  /** Dòng + ngày mà bảng giả sẽ báo lên khi bấm nút đổi ngày. */
  saveOperationalResult: undefined as unknown,
}))

const mutation = (fn?: (...args: never[]) => unknown) => ({
  mutateAsync: fn ?? vi.fn(async () => ({})),
  mutate: vi.fn(),
  isPending: false,
})

vi.mock('../hooks/use-purchase-request', () => ({
  usePurchaseRequest: () => ({ data: state.data, isLoading: false, isError: false }),
  useOrderProgress: () => ({ data: state.progress }),
  usePurchaseRequestAssignableStaff: () => ({ data: { items: [] } }),
  useSavePurchaseRequest: () => mutation(),
  usePurchaseRequestAction: () => mutation(state.runAction),
  useDeletePurchaseRequest: () => mutation(),
  useAssignPurchaser: () => mutation(),
  useUpdateItemStatus: () => mutation(state.updateItemStatus),
  useSetUrgent: () => mutation(),
  useTransferPurchaseRequestDept: () => mutation(),
  useDeptHeadCandidates: () => ({ data: { items: [] } }),
  useDefaultDeptHead: () => ({ data: undefined }),
}))
vi.mock('../hooks/use-purchase-request-options', () => ({
  useGeneratePrOrders: () => mutation(),
}))
vi.mock('../hooks/use-purchase-request-support', () => ({
  useRelatedPurchaseOrders: () => ({ data: { items: [] } }),
}))
vi.mock('../hooks/use-approver-candidates', () => ({
  useApproverCandidates: () => ({ data: { items: [] } }),
}))
vi.mock('@/modules/hr/hooks/use-companies', () => ({
  useCompanies: () => ({ data: { total: 0, items: [] } }),
}))
vi.mock('@/modules/hr/hooks/use-departments', () => ({
  useDepartments: () => ({ data: { total: 0, items: [] } }),
}))
vi.mock('@/modules/hr/hooks/use-employees', () => ({
  useEmployees: () => ({ data: { total: 0, items: [] } }),
}))
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAccess: () => true }),
}))

//  Thẻ con nặng (mỗi thẻ tự gọi mạng) — không phải đối tượng của bài này.
vi.mock('../components/purchase-request-info-card', () => ({ PurchaseRequestInfoCard: () => null }))
vi.mock('../components/purchase-request-supplier-card', () => ({
  PurchaseRequestSupplierCard: () => null,
}))
vi.mock('../components/purchase-request-choose-card', () => ({
  PurchaseRequestChooseCard: () => null,
}))
vi.mock('../components/purchase-request-linked-documents-card', () => ({
  PurchaseRequestLinkedDocumentsCard: () => null,
}))
vi.mock('../components/document-attachments-card', () => ({ DocumentAttachmentsCard: () => null }))
vi.mock('../components/document-comments', () => ({ DocumentComments: () => null }))
vi.mock('@/shared/audit', () => ({ AuditTimeline: () => null }))
vi.mock('@/modules/dossier/components/required-dossiers-card', () => ({
  RequiredDossiersCard: () => null,
}))

//  Bảng + popup dòng giả: chỉ để bấm vào hai đường báo đổi ngày dự kiến lên trang.
vi.mock('../components/purchase-request-items-table', () => ({
  EMPTY_PURCHASE_REQUEST_ITEM: {},
  PurchaseRequestItemsTable: ({
    items,
    onExpectedDateCommit,
  }: {
    items: PurchaseRequestItem[]
    onExpectedDateCommit?: (item: PurchaseRequestItem, next: string, original: string) => void
  }) => (
    <button
      type="button"
      onClick={() => onExpectedDateCommit?.(items[0], '2026-06-01', items[0].expected_date)}
    >
      Đổi ngày trên bảng
    </button>
  ),
}))
vi.mock('../components/purchase-request-line-detail-dialog', () => ({
  PurchaseRequestLineDetailDialog: ({
    onSaveOperational,
  }: {
    onSaveOperational: (item: PurchaseRequestItem) => Promise<boolean | void>
  }) => (
    <button
      type="button"
      onClick={async () => {
        const data = state.data as PurchaseRequestDetail
        state.saveOperationalResult = await onSaveOperational({
          ...data.items[0],
          expected_date: '2026-06-01',
        })
      }}
    >
      Lưu dòng giả
    </button>
  ),
}))

const LINE: PurchaseRequestItem = {
  id: 7,
  product_code: 'NAP0029',
  product_name: 'Nắp nhựa phi 28',
  item_group: 'Bao bì',
  group_desc: '',
  qty: 1000,
  unit: 'Cái',
  price: 900,
  vat_pct: 8,
  amount: 972000,
  warehouse: 'Kho HCM',
  required_date: '2026-05-20',
  assignee: '',
  expected_date: '2026-05-25',
  line_status: 'no_po',
  progress_note: '',
  note: 'Ghi chú dòng',
  qty_ordered: 0,
  qty_received: 0,
  product_id: 3,
  product_thumbnail_url: '',
}

function buildRequest(overrides: Partial<PurchaseRequestDetail> = {}): PurchaseRequestDetail {
  return {
    id: 12,
    code: 'PYC09112601',
    company_id: 2,
    company_name: 'DEGO',
    requester: 'Trần Bảo',
    requester_id: 9,
    requester_position: 'Nhân viên',
    department: 'Kế toán',
    head_of_dept: 'Lê Hà',
    head_of_dept_id: 0,
    handler_dept_id: 0,
    purpose: 'Mua nắp chai',
    request_date: '2026-05-01',
    received_date: '',
    need_date: '',
    status: 'draft',
    is_urgent: false,
    vat_rate: 0.08,
    assignee_id: 0,
    note: 'Gấp trong tuần',
    show_code_on_print: true,
    supplier_req: { name: '', tax_code: '', contact: '' },
    supplier_pur: { name: '', tax_code: '', contact: '' },
    supplier_from_survey: false,
    can_edit_supplier_pur: false,
    suggested_supplier: '',
    suggested_supplier_tax_code: '',
    suggested_supplier_contact: '',
    quote_filename: '',
    quote_file_url: '',
    dispatch_enabled: true,
    can_dispatch: false,
    can_approve: false,
    created_at: '2026-05-01T08:00:00',
    created_by_name: 'Trần Bảo',
    requester_signature: '',
    approver_name: '',
    approver_signature: '',
    dispatcher_name: '',
    dispatcher_signature: '',
    purchasing_head_name: '',
    purchasing_head_signature: '',
    options_chosen_at: null,
    options_chosen_by_name: '',
    items: [LINE],
    subtotal: 0,
    vat: 0,
    total: 0,
    ...overrides,
  }
}

/** Màn đích của điều hướng: in đường dẫn + `state` ra để bài kiểm đọc. */
function LocationProbe() {
  const location = useLocation()
  return (
    <pre data-testid="location">
      {location.pathname}
      {'\n'}
      {JSON.stringify(location.state)}
    </pre>
  )
}

function build(data: PurchaseRequestDetail) {
  state.data = data
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/procurement/purchase-requests/${data.id}`]}>
        <Routes>
          <Route path="/procurement/purchase-requests/:id" element={<PurchaseRequestDetailPage />} />
          <Route path="*" element={<LocationProbe />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  localStorage.clear()
  state.progress = { ordered: {}, pending: {}, orders: {} }
  state.runAction.mockClear()
  state.updateItemStatus.mockClear()
  state.saveOperationalResult = undefined
  useAuthStore.setState({ user: null })
})

describe('PurchaseRequestDetailPage — chữ nút theo v1 (duoc-CR-741)', () => {
  it('a draft shows "Xóa phiếu" and "Gửi duyệt", never the old "Lưu & gửi duyệt"', () => {
    build(buildRequest({ status: 'draft' }))

    expect(screen.getByRole('button', { name: 'Xóa phiếu' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Gửi duyệt' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Lưu & gửi duyệt/ })).toBeNull()
  })

  it('the delete confirm reads like v1: "Xác nhận xóa", buttons Xóa / Hủy', async () => {
    build(buildRequest({ status: 'draft' }))

    await userEvent.click(screen.getByRole('button', { name: 'Xóa phiếu' }))
    const dialog = screen.getByRole('alertdialog')
    expect(within(dialog).getByText('Xác nhận xóa')).toBeInTheDocument()
    expect(
      within(dialog).getByText(/Bạn có chắc chắn muốn xóa phiếu mua hàng này không\?/),
    ).toBeInTheDocument()
    expect(within(dialog).getByRole('button', { name: 'Xóa' })).toBeInTheDocument()
    expect(within(dialog).getByRole('button', { name: 'Hủy' })).toBeInTheDocument()
  })

  it('the dispatch button is "Duyệt"; its confirm says "Duyệt điều phối" with Duyệt / Đóng', async () => {
    build(buildRequest({ status: 'approved', can_dispatch: true }))

    expect(screen.queryByRole('button', { name: 'Duyệt điều phối' })).toBeNull()
    await userEvent.click(screen.getByRole('button', { name: 'Duyệt' }))

    const dialog = screen.getByRole('alertdialog')
    expect(within(dialog).getByText('Duyệt điều phối')).toBeInTheDocument()
    expect(within(dialog).getByRole('button', { name: 'Đóng' })).toBeInTheDocument()
    await userEvent.click(within(dialog).getByRole('button', { name: 'Duyệt' }))
    expect(state.runAction).toHaveBeenCalledWith({ action: 'dispatch' })
  })

  it('the create-order button reads "Tạo đơn mua hàng", not the short "Tạo đơn"', () => {
    build(buildRequest({ status: 'dispatched' }))

    expect(screen.getByRole('button', { name: 'Tạo đơn mua hàng' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Tạo đơn' })).toBeNull()
  })
})

describe('PurchaseRequestDetailPage — hộp đã đặt đủ/vượt (duoc-CR-741)', () => {
  const second: PurchaseRequestItem = {
    ...LINE,
    id: 8,
    product_code: 'NAP0030',
    product_name: 'Nắp nhựa phi 30',
  }

  /** Mã hàng trong các dòng điền sẵn cho ĐMH mới (đọc từ `state` của điều hướng). */
  function orderedCodes(): string[] {
    const text = screen.getByTestId('location').textContent ?? ''
    const stateJson = text.slice(text.indexOf('\n') + 1)
    const parsed = JSON.parse(stateJson) as {
      fromPurchaseRequest: { items: { product_code: string }[] }
    }
    return parsed.fromPurchaseRequest.items.map((item) => item.product_code)
  }

  function openWarning() {
    //  Dòng 1 đã đặt đủ, dòng 2 chưa đặt — nút còn hiện và bấm vào phải hỏi lại.
    state.progress = { ordered: { NAP0029: 1000 }, pending: {}, orders: {} }
    build(buildRequest({ status: 'dispatched', items: [LINE, second] }))
    return userEvent.click(screen.getByRole('button', { name: 'Tạo đơn mua hàng' }))
  }

  it('offers exactly the two v1 choices plus a plain close', async () => {
    await openWarning()

    const dialog = screen.getByRole('alertdialog')
    expect(within(dialog).getByText('Số lượng đã đặt đủ/vượt')).toBeInTheDocument()
    const names = within(dialog)
      .getAllByRole('button')
      .map((button) => button.getAttribute('aria-label') || button.textContent)
    expect(names).toEqual(['Đóng', 'Chỉ SP còn thiếu', 'Vẫn mua thêm'])
  })

  it('"Vẫn mua thêm" opens the new order with every line, including the fully ordered one', async () => {
    await openWarning()
    await userEvent.click(screen.getByRole('button', { name: 'Vẫn mua thêm' }))

    expect(screen.getByTestId('location').textContent).toContain('/procurement/purchase-orders/new')
    expect(orderedCodes()).toEqual(['NAP0030', 'NAP0029'])
  })

  it('"Chỉ SP còn thiếu" leaves the fully ordered line out', async () => {
    await openWarning()
    await userEvent.click(screen.getByRole('button', { name: 'Chỉ SP còn thiếu' }))

    expect(screen.getByTestId('location').textContent).toContain('/procurement/purchase-orders/new')
    expect(orderedCodes()).toEqual(['NAP0030'])
  })

  it('Esc closes the warning without navigating anywhere — same as v1 onClose', async () => {
    await openWarning()
    await userEvent.keyboard('{Escape}')

    expect(screen.queryByRole('alertdialog')).toBeNull()
    expect(screen.queryByTestId('location')).toBeNull()
  })
})

describe('PurchaseRequestDetailPage — Tạo yêu cầu báo giá (CR-026, duoc-CR-741)', () => {
  it('a rejected request offers it and carries the lines into the new quote request', async () => {
    build(buildRequest({ status: 'cancelled' }))

    await userEvent.click(screen.getByRole('button', { name: 'Tạo yêu cầu báo giá' }))

    const probe = screen.getByTestId('location').textContent ?? ''
    expect(probe).toContain('/procurement/survey-requests/new')
    //  Tên hàng gộp vào Chi tiết thông số vì YCBG không có ô tên hàng.
    expect(probe).toContain('"requirement_detail":"Nắp nhựa phi 28"')
    expect(probe).toContain('"src_pr_item_id":7')
    expect(probe).toContain('(Tạo từ YCMH PYC09112601)')
  })

  it('is not offered on a request that is still moving forward', () => {
    build(buildRequest({ status: 'dispatched' }))
    expect(screen.queryByRole('button', { name: 'Tạo yêu cầu báo giá' })).toBeNull()
  })
})

/**
 * Lỗi cũ: hai chỗ hỏi lý do đổi ngày dự kiến dùng `window.prompt` của trình duyệt — không theo
 * giao diện hệ thống, có trình duyệt chặn thẳng. Nay là hộp của v2 mang chữ `askPrompt` v1.
 */
describe('PurchaseRequestDetailPage — lý do đổi ngày dự kiến (duoc-CR-741)', () => {
  it('changing the date on the table asks for a reason, then saves it', async () => {
    build(buildRequest({ status: 'dispatched' }))

    await userEvent.click(screen.getByRole('button', { name: 'Đổi ngày trên bảng' }))
    const dialog = screen.getByRole('dialog', { name: 'Đổi ngày dự kiến có hàng' })
    expect(within(dialog).getByText(/nhập lý do \(bắt buộc\)/)).toBeInTheDocument()
    //  Chưa gõ lý do thì chưa lưu được.
    expect(within(dialog).getByRole('button', { name: 'Lưu' })).toBeDisabled()

    await userEvent.type(within(dialog).getByRole('textbox'), 'NCC báo trễ')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Lưu' }))

    expect(state.updateItemStatus).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 7,
        expected_date: '2026-06-01',
        expected_date_reason: 'NCC báo trễ',
      }),
    )
  })

  it('cancelling the reason saves nothing', async () => {
    build(buildRequest({ status: 'dispatched' }))

    await userEvent.click(screen.getByRole('button', { name: 'Đổi ngày trên bảng' }))
    await userEvent.click(screen.getByRole('button', { name: 'Hủy' }))

    expect(screen.queryByRole('dialog', { name: 'Đổi ngày dự kiến có hàng' })).toBeNull()
    expect(state.updateItemStatus).not.toHaveBeenCalled()
  })

  it('the line popup asks "Đổi thời gian dự kiến có hàng" and stays open when cancelled', async () => {
    build(buildRequest({ status: 'dispatched' }))

    await userEvent.click(screen.getByRole('button', { name: 'Lưu dòng giả' }))
    expect(
      screen.getByRole('dialog', { name: 'Đổi thời gian dự kiến có hàng' }),
    ).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Hủy' }))

    //  `false` = popup dòng giữ nguyên, như v1 `if (r === null) return`.
    await vi.waitFor(() => expect(state.saveOperationalResult).toBe(false))
    expect(state.updateItemStatus).not.toHaveBeenCalled()
  })
})
