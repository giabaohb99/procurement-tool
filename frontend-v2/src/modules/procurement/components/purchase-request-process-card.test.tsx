import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type {
  PurchaseRequestDetail,
  PurchaseRequestItem,
} from '../types/purchase-request-detail'
import type { PurchaseRequestOption } from '../types/purchase-request-options'
import { PurchaseRequestProcessCard } from './purchase-request-process-card'

/**
 * Thẻ này nói về QUYỀN AI THẤY GÌ, không nói về mạng — thay tầng hook bằng dữ
 * liệu tĩnh và vặn từng vai (người yêu cầu / NSTM / người ngoài) qua hai biến
 * mockUser + grantedPermissions. Đợt 3b: màn này là bàn làm việc của NSTM —
 * nút CHỌN phương án đã dời sang thẻ Phương án của màn chi tiết, ở đây chỉ còn
 * gắn/gỡ phương án + nút "Chốt hoàn thành xử lý" (kèm hộp chốt rỗng).
 */

let mockUser: { employee_id?: number; emp_code?: string } | null = null
let grantedPermissions: string[] = []
let mockOptions: PurchaseRequestOption[] = []

vi.mock('@/core/auth/use-auth', () => ({
  useAuth: () => ({ user: mockUser }),
}))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) => grantedPermissions.includes(`${entity}:${action}`),
  }),
}))

vi.mock('@/modules/production/hooks/use-suppliers', () => ({
  useSuppliers: () => ({ data: { items: [] } }),
}))

vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestItemGroups: () => ({ data: { items: [] } }),
}))

const noopMutation = { mutate: vi.fn(), isPending: false }
const completeMutate = vi.fn()

vi.mock('../hooks/use-purchase-request-options', () => ({
  usePurchaseRequestItemOptions: () => ({
    data: { items: mockOptions },
    isLoading: false,
  }),
  usePrAvailableSurveyLines: () => ({ data: { items: [], total: 0 }, isLoading: false }),
  useAttachSurveyOption: () => noopMutation,
  useAddManualOption: () => noopMutation,
  useUpdateOption: () => noopMutation,
  useRemoveOption: () => noopMutation,
  useCompletePrOptions: () => ({ mutate: completeMutate, isPending: false }),
}))

function buildOption(overrides: Partial<PurchaseRequestOption> = {}): PurchaseRequestOption {
  return {
    id: 71,
    pr_item_id: 5,
    source: 1,
    source_label: 'Từ khảo sát',
    product_survey_line_id: 900,
    public_id: 1,
    display_label: 'Phương án 1',
    is_chosen: false,
    snap_product_name: 'Thùng carton 5 lớp',
    snap_spec: '60x40x40',
    snap_origin: 'VN',
    snap_quote_unit: 'Cái',
    snap_moq: 100,
    snap_price_by_volume: 12000,
    snap_volume_range: '',
    snap_vat: 8,
    snap_delivery_time: '7 ngày',
    snap_delivery_place: 'Kho HCM',
    snap_shipping_cost: '',
    snap_sample_ready: '',
    snap_lab_result: '',
    nstm_note: '',
    created_at: '2026-09-01T00:00:00',
    supplier_code: 'NCC-A',
    supplier_name: 'CÔNG TY A',
    supplier_survey_id: 31,
    snap_internal_code: 'A-01',
    ...overrides,
  }
}

function buildItem(overrides: Partial<PurchaseRequestItem> = {}): PurchaseRequestItem {
  return {
    id: 5,
    product_code: 'SP-001',
    product_name: 'Thùng carton 5 lớp',
    item_group: 'Bao bì',
    group_desc: '',
    qty: 500,
    unit: 'Cái',
    price: 11500,
    vat_pct: 8,
    amount: 0,
    warehouse: '',
    required_date: '',
    assignee: 'NSTM01',
    expected_date: '',
    line_status: 'Chưa đặt hàng',
    progress_note: '',
    note: '',
    qty_ordered: 0,
    qty_received: 0,
    product_id: 9,
    product_thumbnail_url: '',
    // Cờ đợt 3b: mặc định dòng đã có 1 phương án và chưa chốt hoàn thành.
    option_count: 1,
    options_done: false,
    no_option: false,
    ...overrides,
  }
}

function buildPurchaseRequest(
  overrides: Partial<PurchaseRequestDetail> = {},
): PurchaseRequestDetail {
  return {
    id: 12,
    code: 'PR-2026-012',
    company_id: 1,
    company_name: 'DEGO',
    requester: 'Nguyễn Văn A',
    requester_id: 44,
    requester_position: '',
    department: 'Marketing',
    head_of_dept: '',
    head_of_dept_id: 0,
    handler_dept_id: 0,
    purpose: '',
    request_date: '2026-09-01',
    received_date: '2026-09-02',
    need_date: '',
    status: 'processing',
    is_urgent: false,
    vat_rate: 8,
    assignee_id: 0,
    note: '',
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
    created_at: '2026-09-01T00:00:00',
    created_by_name: '',
    requester_signature: '',
    approver_name: '',
    approver_signature: '',
    dispatcher_name: '',
    dispatcher_signature: '',
    purchasing_head_name: '',
    purchasing_head_signature: '',
    options_chosen_at: null,
    options_chosen_by_name: '',
    items: [buildItem()],
    subtotal: 0,
    vat: 0,
    total: 0,
    ...overrides,
  }
}

beforeEach(() => {
  mockUser = null
  grantedPermissions = []
  mockOptions = [buildOption()]
  completeMutate.mockClear()
  window.localStorage.clear()
})

/** DataTable bên trong tự gọi useQueryClient nên phải có provider dù hook dữ liệu đã mock. */
function renderCard(purchaseRequest: PurchaseRequestDetail) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <PurchaseRequestProcessCard purchaseRequest={purchaseRequest} />
    </QueryClientProvider>,
  )
}

describe('PurchaseRequestProcessCard', () => {
  it('keeps the requester read-only: no choose button here anymore, no complete button', () => {
    // Người yêu cầu (không quyền ghi, không quyền xem NCC): đợt 3b họ CHỌN ở màn
    // chi tiết, màn xử lý chỉ để xem — backend đã che supplier_* thành rỗng,
    // giao diện phải giấu luôn cột NCC.
    mockUser = { employee_id: 44, emp_code: 'REQ01' }
    grantedPermissions = ['purchase_request:read']
    mockOptions = [buildOption({ supplier_code: '', supplier_name: '', snap_internal_code: '' })]

    renderCard(buildPurchaseRequest())

    expect(screen.getByText('Phương án 1')).toBeInTheDocument()
    // Header DataTable kèm tay nắm kéo cột nên accessible name không thuần "NCC";
    // neo ^NCC để khỏi dính cột "Tên SP theo NCC" luôn hiện.
    expect(screen.queryAllByRole('columnheader', { name: /^NCC/ })).toHaveLength(0)
    // Nút chọn đã dời sang màn chi tiết — ở đây tuyệt đối không còn.
    expect(screen.queryByRole('button', { name: 'Chốt' })).toBeNull()
    expect(screen.queryByRole('button', { name: /Chốt hoàn thành xử lý/ })).toBeNull()
    expect(screen.getByText('Chưa chọn')).toBeInTheDocument()
    // Không có quyền ghi thì không có khối gắn phương án.
    expect(screen.queryByText(/Thêm phương án từ kết quả khảo sát/)).toBeNull()
  })

  it('lets the assigned NSTM attach, remove and complete their own lines', () => {
    mockUser = { employee_id: 77, emp_code: 'NSTM01' }
    grantedPermissions = ['purchase_request:read', 'purchase_request:write', 'supplier:read']

    renderCard(buildPurchaseRequest())

    // Cả bảng phương án lẫn bảng picker đều có cột NCC nên phải dùng getAllByRole.
    expect(screen.getAllByRole('columnheader', { name: /^NCC/ }).length).toBeGreaterThan(0)
    expect(screen.getByText(/Thêm phương án từ kết quả khảo sát/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Nhập tay' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Gỡ phương án' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Chốt hoàn thành xử lý/ })).toBeInTheDocument()
    // Chọn phương án là việc của người yêu cầu ở màn chi tiết.
    expect(screen.queryByRole('button', { name: 'Chốt' })).toBeNull()
  })

  it('completes directly when every line of mine already has options', () => {
    mockUser = { employee_id: 77, emp_code: 'NSTM01' }
    grantedPermissions = ['purchase_request:read', 'purchase_request:write', 'supplier:read']

    renderCard(buildPurchaseRequest())

    fireEvent.click(screen.getByRole('button', { name: /Chốt hoàn thành xử lý/ }))

    // Không dòng trống -> không mở hộp thoại, gọi thẳng API với danh sách rỗng.
    expect(completeMutate).toHaveBeenCalledWith([])
    expect(screen.queryByText('Dòng chưa có phương án')).toBeNull()
  })

  it('forces ticking every empty line in the dialog before completing', () => {
    mockUser = { employee_id: 77, emp_code: 'NSTM01' }
    grantedPermissions = ['purchase_request:read', 'purchase_request:write', 'supplier:read']
    // Dòng 5 có phương án, dòng 6 trống (option_count = 0) — phải tick chốt rỗng.
    mockOptions = []

    renderCard(
      buildPurchaseRequest({
        items: [
          buildItem(),
          buildItem({ id: 6, product_code: 'SP-002', product_name: 'Băng keo', option_count: 0 }),
        ],
      }),
    )

    fireEvent.click(screen.getByRole('button', { name: /Chốt hoàn thành xử lý/ }))

    expect(screen.getByText('Dòng chưa có phương án')).toBeInTheDocument()
    expect(completeMutate).not.toHaveBeenCalled()
    // Chưa tick đủ thì nút xác nhận phải khóa — bấm cũng không được gì.
    const confirmButton = screen.getByRole('button', { name: 'Chốt hoàn thành' })
    expect(confirmButton).toBeDisabled()

    fireEvent.click(screen.getByRole('checkbox'))
    expect(confirmButton).toBeEnabled()
    fireEvent.click(confirmButton)

    expect(completeMutate).toHaveBeenCalledWith([6], expect.anything())
  })

  it('locks a completed line and shows its badges instead of edit controls', () => {
    mockUser = { employee_id: 77, emp_code: 'NSTM01' }
    grantedPermissions = ['purchase_request:read', 'purchase_request:write', 'supplier:read']

    renderCard(
      buildPurchaseRequest({
        items: [
          buildItem({ options_done: true }),
          buildItem({
            id: 6,
            product_code: 'SP-002',
            product_name: 'Băng keo',
            option_count: 0,
            options_done: true,
            no_option: true,
          }),
        ],
      }),
    )

    expect(screen.getByText('Đã chốt hoàn thành xử lý')).toBeInTheDocument()
    expect(screen.getByText('Chốt rỗng — không có NCC phù hợp')).toBeInTheDocument()
    // Mọi dòng của mình đã chốt: hết đường sửa, thay nút bằng câu báo đã xong.
    expect(screen.queryByRole('button', { name: 'Gỡ phương án' })).toBeNull()
    expect(screen.queryByText(/Thêm phương án từ kết quả khảo sát/)).toBeNull()
    expect(screen.queryByRole('button', { name: /Chốt hoàn thành xử lý/ })).toBeNull()
    expect(
      screen.getByText('Bạn đã chốt hoàn thành phần xử lý của mình.'),
    ).toBeInTheDocument()
  })

  it('locks lines assigned to another NSTM down to read-only', () => {
    mockUser = { employee_id: 78, emp_code: 'NSTM02' }
    grantedPermissions = ['purchase_request:read', 'purchase_request:write', 'supplier:read']

    renderCard(buildPurchaseRequest())

    expect(screen.getByText('Dòng của NSTM khác — chỉ xem')).toBeInTheDocument()
    expect(screen.queryByText(/Thêm phương án từ kết quả khảo sát/)).toBeNull()
    expect(screen.queryByRole('button', { name: 'Gỡ phương án' })).toBeNull()
    // Không có dòng nào của mình -> cũng không có nút chốt hoàn thành.
    expect(screen.queryByRole('button', { name: /Chốt hoàn thành xử lý/ })).toBeNull()
  })

  it('tells the NSTM why attaching is unavailable without supplier read', () => {
    // Có quyền ghi nhưng thiếu supplier:read — backend chặn cả hai đường gắn,
    // giao diện phải NÓI lý do chứ không để trống (trống đọc thành "hết chỗ gắn").
    mockUser = { employee_id: 77, emp_code: 'NSTM01' }
    grantedPermissions = ['purchase_request:read', 'purchase_request:write']

    renderCard(buildPurchaseRequest())

    expect(
      screen.getByText(/Cần quyền xem nhà cung cấp để tra kho khảo sát/),
    ).toBeInTheDocument()
    expect(screen.queryByText(/Thêm phương án từ kết quả khảo sát/)).toBeNull()
  })

  it('turns fully read-only once the request is closed', () => {
    // Phiếu hoàn thành: vẫn xem lại được phương án nhưng mọi đường ghi
    // (gắn / gỡ / chốt hoàn thành) phải biến mất.
    mockUser = { employee_id: 77, emp_code: 'NSTM01' }
    grantedPermissions = ['purchase_request:read', 'purchase_request:write', 'supplier:read']
    mockOptions = [buildOption({ is_chosen: true })]

    renderCard(buildPurchaseRequest({ status: 'completed', items: [buildItem({ options_done: true })] }))

    expect(screen.getByText('Người YC đã chọn')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Chốt hoàn thành xử lý/ })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Gỡ phương án' })).toBeNull()
    expect(screen.queryByText(/Thêm phương án từ kết quả khảo sát/)).toBeNull()
  })

  it('caps a line at five options and says so instead of showing the picker', () => {
    mockUser = { employee_id: 77, emp_code: 'NSTM01' }
    grantedPermissions = ['purchase_request:read', 'purchase_request:write', 'supplier:read']
    mockOptions = [1, 2, 3, 4, 5].map((n) =>
      buildOption({ id: 70 + n, public_id: n, display_label: `Phương án ${n}` }),
    )

    renderCard(buildPurchaseRequest({ items: [buildItem({ option_count: 5 })] }))

    expect(screen.getByText(/Dòng đã đủ 5 phương án/)).toBeInTheDocument()
    expect(screen.queryByText(/Thêm phương án từ kết quả khảo sát/)).toBeNull()
  })
})
