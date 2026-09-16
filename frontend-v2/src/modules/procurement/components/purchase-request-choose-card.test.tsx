import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type {
  PurchaseRequestDetail,
  PurchaseRequestItem,
} from '../types/purchase-request-detail'
import type { PurchaseRequestOption } from '../types/purchase-request-options'
import { PurchaseRequestChooseCard } from './purchase-request-choose-card'

/**
 * Thẻ Phương án trên màn CHI TIẾT YCMH (bao-CR-310 đợt 3b + đợt 2 MỞ RỘNG):
 * chỉ hiện dòng NSTM đã chốt hoàn thành; người yêu cầu / người giữ quyền duyệt
 * CHỌN phương án (lưới thẻ radio y khuôn YCBG CR-222); tầng THU MUA (write +
 * supplier:read) sửa giá / điền NCC ngay trên từng thẻ và có khu "Áp 1 NCC cho
 * nhiều dòng" (H.10.5). Dòng chốt rỗng nay vẫn có Phương án 0 chọn được. Test
 * vặn vai qua mockUser + grantedPermissions như bộ test của màn xử lý.
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

const chooseMutate = vi.fn()
const reopenMutate = vi.fn()
const setSupplierMutate = vi.fn()
const updateOptionMutate = vi.fn()
const assignBulkMutate = vi.fn()
vi.mock('../hooks/use-purchase-request-options', () => ({
  usePurchaseRequestItemOptions: (_prId: number, itemId: number) => ({
    // Khớp `enabled: itemId > 0` của hook thật. Đợt 2 mở rộng bỏ chiêu tắt
    // query bằng itemId=0 cho dòng chốt rỗng — mock giữ guard này để ai lỡ đưa
    // chiêu đó quay lại là test Phương án 0 của dòng chốt rỗng đỏ ngay.
    data: itemId > 0 ? { items: mockOptions } : undefined,
    isLoading: false,
  }),
  useChooseOption: () => ({ mutate: chooseMutate, isPending: false }),
  useReopenPrOptionsLine: () => ({ mutate: reopenMutate, isPending: false }),
  useSetPrOptionSupplier: () => ({ mutate: setSupplierMutate, isPending: false }),
  useUpdateOption: () => ({ mutate: updateOptionMutate, isPending: false }),
  useAssignPrSupplierBulk: () => ({ mutate: assignBulkMutate, isPending: false }),
}))

vi.mock('@/modules/production/hooks/use-suppliers', () => ({
  useSuppliers: () => ({
    data: { items: [{ code: 'NCC-A', name: 'CÔNG TY A' }] },
    isLoading: false,
  }),
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

/** Phương án 0 — hệ sinh từ dòng yêu cầu gốc, chưa có NCC (H.10.1). */
function buildOptionZero(overrides: Partial<PurchaseRequestOption> = {}): PurchaseRequestOption {
  return buildOption({
    id: 70,
    source: 3,
    source_label: 'Yêu cầu gốc',
    product_survey_line_id: null,
    public_id: 0,
    display_label: 'Phương án 0',
    supplier_code: '',
    supplier_name: '',
    supplier_survey_id: 0,
    snap_internal_code: '',
    snap_price_by_volume: 11500,
    ...overrides,
  })
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
    option_count: 1,
    options_done: true,
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
  chooseMutate.mockClear()
  reopenMutate.mockClear()
  setSupplierMutate.mockClear()
  updateOptionMutate.mockClear()
  assignBulkMutate.mockClear()
  window.localStorage.clear()
})

/** DataTable bên trong tự gọi useQueryClient nên phải có provider dù hook dữ liệu đã mock. */
function renderCard(purchaseRequest: PurchaseRequestDetail) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <PurchaseRequestChooseCard purchaseRequest={purchaseRequest} />
    </QueryClientProvider>,
  )
}

/** Vai THU MUA phụ trách dòng mẫu (assignee NSTM01) — tầng sửa giá / NCC của H.10.5. */
function actAsPurchasingAssignee() {
  mockUser = { employee_id: 77, emp_code: 'NSTM01' }
  grantedPermissions = ['purchase_request:read', 'purchase_request:write', 'supplier:read']
}

describe('PurchaseRequestChooseCard', () => {
  it('renders nothing while no line has been completed by the NSTM', () => {
    // Phiếu chưa tới nhịp chọn: thẻ tự ẩn, không bày khung rỗng gây hiểu lầm.
    mockUser = { employee_id: 44, emp_code: 'REQ01' }
    grantedPermissions = ['purchase_request:read']

    renderCard(buildPurchaseRequest({ items: [buildItem({ options_done: false })] }))

    expect(screen.queryByText(/Phương án — NSTM đã xử lý xong/)).toBeNull()
  })

  it('lets the requester choose and reopen even without write permission', () => {
    // Người yêu cầu thường KHÔNG có purchase_request:write — quyền chọn đến từ
    // việc họ đứng tên phiếu, khớp gác ensure_can_choose của backend.
    mockUser = { employee_id: 44, emp_code: 'REQ01' }
    grantedPermissions = ['purchase_request:read']

    renderCard(buildPurchaseRequest())

    expect(screen.getByText(/Phương án — NSTM đã xử lý xong/)).toBeInTheDocument()
    // Cả thẻ phương án là vùng bấm chọn — lọc theo tên vì ô radio trang trí
    // bên trong thẻ không có accessible name.
    expect(screen.getByRole('radio', { name: /Phương án 1/ })).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Mở lại cho NSTM xử lý' }),
    ).toBeInTheDocument()
    // Tầng thu mua KHÔNG mở cho người yêu cầu thiếu write + supplier:read.
    expect(screen.queryByRole('button', { name: /Sửa giá \/ NCC/ })).toBeNull()
    expect(screen.queryByText('Áp 1 NCC cho nhiều dòng')).toBeNull()

    fireEvent.click(screen.getByRole('radio', { name: /Phương án 1/ }))
    expect(chooseMutate).toHaveBeenCalledWith(
      { itemId: 5, optionId: 71, wasChosen: false },
      expect.anything(),
    )

    fireEvent.click(screen.getByRole('button', { name: 'Mở lại cho NSTM xử lý' }))
    expect(reopenMutate).toHaveBeenCalledWith(5)
  })

  it('keeps a purchasing bystander off choose/reopen but lets them edit price and supplier', () => {
    // NSTM phụ trách dòng (không phải người yêu cầu, không quyền duyệt): không
    // chọn / mở lại được (backend trả 403), nhưng đợt 2 mở rộng cho tầng thu mua
    // sửa giá / NCC ngay trên thẻ (khe H.10.4).
    actAsPurchasingAssignee()
    mockOptions = [buildOption({ is_chosen: true })]

    renderCard(buildPurchaseRequest())

    expect(screen.getByText(/bạn đang xem/)).toBeInTheDocument()
    expect(screen.queryByRole('radio', { name: /Phương án 1/ })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Mở lại cho NSTM xử lý' })).toBeNull()
    expect(screen.getByText('Đã chọn')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Sửa giá / NCC của Phương án 1' }),
    ).toBeInTheDocument()
  })

  it('hides both the edit button and the bulk zone for a line assigned to someone else', () => {
    // Cùng luật ensure_own_line của backend: thu mua thường chỉ đụng dòng MÌNH
    // phụ trách — dòng của người khác thì tầng sửa phải tắt kẻo mời bấm ăn 403.
    actAsPurchasingAssignee()
    mockOptions = [buildOptionZero({ is_chosen: true })]

    renderCard(
      buildPurchaseRequest({
        items: [buildItem({ assignee: 'NSTM99', chosen_option: buildOptionZero({ is_chosen: true }) })],
      }),
    )

    expect(screen.queryByRole('button', { name: /Sửa giá \/ NCC/ })).toBeNull()
    expect(screen.queryByText('Áp 1 NCC cho nhiều dòng')).toBeNull()
  })

  it('hides the supplier column without supplier read permission', () => {
    mockUser = { employee_id: 44, emp_code: 'REQ01' }
    grantedPermissions = ['purchase_request:read']
    mockOptions = [buildOption({ supplier_code: '', supplier_name: '', snap_internal_code: '' })]

    renderCard(buildPurchaseRequest())

    // Trường "NCC:" trên thẻ chỉ hiện khi có supplier:read — neo dấu hai chấm
    // để khỏi dính chữ NCC trong câu khác.
    expect(screen.queryByText(/^NCC:/)).toBeNull()

    grantedPermissions = ['purchase_request:read', 'supplier:read']
    mockOptions = [buildOption()]
    renderCard(buildPurchaseRequest())
    expect(screen.getByText(/^NCC:/)).toBeInTheDocument()
  })

  it('shows the empty-completion notice AND a choosable option zero for a no_option line', () => {
    // Đợt 2 mở rộng (H.10.3): chốt rỗng = không có phương án NSTM, nhưng dòng
    // vẫn mua được theo Phương án 0 — bản cũ tắt query bằng itemId=0 là luật cũ.
    mockUser = { employee_id: 44, emp_code: 'REQ01' }
    grantedPermissions = ['purchase_request:read']
    mockOptions = [buildOptionZero()]

    renderCard(
      buildPurchaseRequest({
        items: [buildItem({ option_count: 0, no_option: true })],
      }),
    )

    expect(screen.getByText(/NSTM chốt rỗng/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('radio', { name: /Phương án 0/ }))
    expect(chooseMutate).toHaveBeenCalledWith(
      { itemId: 5, optionId: 70, wasChosen: false },
      expect.anything(),
    )
    // Vẫn mở lại được để NSTM tìm tiếp NCC.
    expect(
      screen.getByRole('button', { name: 'Mở lại cho NSTM xử lý' }),
    ).toBeInTheDocument()
  })

  it('sends the supplier assignment (not a plain update) when the edit dialog saves an NCC', () => {
    // Phương án 0: điền NCC phải đi đường PATCH .../supplier — PATCH thường bị
    // backend cấm đổi NCC. Giá không đổi thì payload không đèo snap_price_by_volume.
    actAsPurchasingAssignee()
    mockOptions = [buildOptionZero()]

    renderCard(buildPurchaseRequest())

    fireEvent.click(screen.getByRole('button', { name: 'Sửa giá / NCC của Phương án 0' }))
    fireEvent.change(screen.getByPlaceholderText('Hoặc gõ tên NCC ngoài danh mục'), {
      target: { value: 'CÔNG TY MỚI' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Lưu' }))

    expect(setSupplierMutate).toHaveBeenCalledWith(
      {
        itemId: 5,
        optionId: 70,
        payload: { supplier_code: '', supplier_name: 'CÔNG TY MỚI' },
      },
      expect.anything(),
    )
    expect(updateOptionMutate).not.toHaveBeenCalled()
  })

  it('only offers a price edit for a survey-sourced option', () => {
    // Phương án từ khảo sát: NCC là danh tính của kết quả khảo sát (H.10.4) —
    // hộp sửa không bày ô NCC và lưu giá đi đường PATCH thường (price-only).
    actAsPurchasingAssignee()
    mockOptions = [buildOption()]

    renderCard(buildPurchaseRequest())

    fireEvent.click(screen.getByRole('button', { name: 'Sửa giá / NCC của Phương án 1' }))
    expect(screen.queryByPlaceholderText('Hoặc gõ tên NCC ngoài danh mục')).toBeNull()
    fireEvent.change(screen.getByRole('spinbutton'), { target: { value: '15000' } })
    fireEvent.click(screen.getByRole('button', { name: 'Lưu' }))

    expect(updateOptionMutate).toHaveBeenCalledWith(
      { itemId: 5, optionId: 71, payload: { snap_price_by_volume: 15000 } },
      expect.anything(),
    )
    expect(setSupplierMutate).not.toHaveBeenCalled()
  })

  it('bulk-assigns one supplier to the ticked lines whose chosen option lacks an NCC', () => {
    // H.10.5: dòng đang chọn phương án chưa có NCC mới vào khu áp hàng loạt;
    // tick dòng + gõ tên NCC là đủ gửi — mã để rỗng khi chọn NCC ngoài danh mục.
    actAsPurchasingAssignee()
    mockOptions = [buildOptionZero({ is_chosen: true })]

    renderCard(
      buildPurchaseRequest({
        items: [buildItem({ chosen_option: buildOptionZero({ is_chosen: true }) })],
      }),
    )

    expect(screen.getByText('Áp 1 NCC cho nhiều dòng')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('checkbox'))
    fireEvent.change(screen.getByPlaceholderText('Hoặc gõ tên NCC ngoài danh mục'), {
      target: { value: 'CÔNG TY B' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Áp NCC cho các dòng đã tick' }))

    expect(assignBulkMutate).toHaveBeenCalledWith(
      { supplier_code: '', supplier_name: 'CÔNG TY B', items: [{ item_id: 5 }] },
      expect.anything(),
    )
  })

  it('keeps the bulk zone away when the chosen option already has a supplier or came from a survey', () => {
    // Đã có NCC thì không còn gì để áp; phương án khảo sát thì backend từ chối
    // cả lô — hai loại dòng này không được phép lọt vào danh sách tick.
    actAsPurchasingAssignee()
    mockOptions = [buildOption({ is_chosen: true })]

    renderCard(
      buildPurchaseRequest({
        items: [
          buildItem({ chosen_option: buildOption({ is_chosen: true }) }),
          buildItem({
            id: 6,
            chosen_option: buildOptionZero({ is_chosen: true, supplier_name: 'CÔNG TY A' }),
          }),
        ],
      }),
    )

    expect(screen.queryByText('Áp 1 NCC cho nhiều dòng')).toBeNull()
  })

  // Hai bài "gom đơn theo phương án (H.10.6)" từng đứng ở đây đã BỎ: bao-CR-310 đợt 4
  // dời nút đó lên đầu trang chi tiết, nhập vào nút "Tạo đơn mua hàng" sổ xuống, nên
  // thẻ này không còn dựng nút nào tên như vậy. Cổng quyền `purchase_order:create` vẫn
  // y nguyên, nay nằm ở `canGenerateFromOptions` của `purchase-request-detail-page.tsx`
  // — chỗ đó CHƯA có bài kiểm nào, đây là khoảng trống đã biết.

  it('turns fully read-only once the request is closed', () => {
    // Phiếu đóng: xem lại phương án đã chọn được, nhưng chốt / mở lại / sửa giá
    // NCC phải biến mất (khớp ensure_stage của backend).
    mockUser = { employee_id: 44, emp_code: 'REQ01' }
    grantedPermissions = ['purchase_request:read', 'purchase_request:write', 'supplier:read']
    mockOptions = [buildOption({ is_chosen: true })]

    renderCard(buildPurchaseRequest({ status: 'completed' }))

    expect(screen.getByText(/Phương án — NSTM đã xử lý xong/)).toBeInTheDocument()
    expect(screen.getByText('Đã chọn')).toBeInTheDocument()
    expect(screen.queryByRole('radio', { name: /Phương án 1/ })).toBeNull()
    expect(screen.queryByRole('button', { name: 'Mở lại cho NSTM xử lý' })).toBeNull()
    expect(screen.queryByRole('button', { name: /Sửa giá \/ NCC/ })).toBeNull()
  })
})
