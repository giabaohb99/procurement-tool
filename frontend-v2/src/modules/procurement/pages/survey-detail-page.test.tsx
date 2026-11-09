import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ConfirmDialogHost } from '@/shared/ui/confirm-dialog'
import type { SurveyDetail } from '../types/survey-detail'
import { SurveyDetailPage } from './survey-detail-page'

/**
 * duoc-CR-741 — chữ trên nút / hộp xác nhận của chi tiết Phiếu khảo sát phải khớp TỪNG CHỮ
 * bản v1 (`frontend/src/pages/SurveyDetail.tsx`), và các hộp hỏi lại v1 có thì v2 cũng có.
 *
 * Chặn ở tầng HOOK dữ liệu; hộp xác nhận dùng hàng thật (`ConfirmDialogHost`).
 */
const runAction = vi.fn()
const deleteSurvey = vi.fn()

//  ⚠️ PHẢI là MỘT tham chiếu cố định cho mỗi bài: trang so `serverData` bằng `Object.is`
//  để biết lúc nào nạp lại bản nháp — trả object mới mỗi lượt render là vòng lặp vô tận.
let currentSurvey: SurveyDetail

vi.mock('../hooks/use-survey', () => ({
  useSurvey: () => ({ data: currentSurvey, isLoading: false, isError: false }),
  useSaveSurvey: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useSurveyAction: () => ({ mutateAsync: runAction, isPending: false }),
  useDeleteSurvey: () => ({ mutateAsync: deleteSurvey, isPending: false }),
  useSurveyLineApprove: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useFillSurveyLine: () => ({ mutateAsync: vi.fn(), isPending: false }),
}))

const EMPTY_LIST = { data: { total: 0, items: [] } }
vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestUnits: () => EMPTY_LIST,
  usePurchaseRequestItemGroups: () => EMPTY_LIST,
  usePurchaseRequestProducts: () => EMPTY_LIST,
  usePurchaseRequestAttachments: () => ({ data: [], isLoading: false }),
  useUploadPurchaseRequestAttachments: () => ({ mutateAsync: vi.fn(), isPending: false }),
  useDeletePurchaseRequestAttachment: () => ({ mutateAsync: vi.fn(), isPending: false }),
}))
vi.mock('../hooks/use-purchase-documents', () => ({
  useSurveyRequests: () => EMPTY_LIST,
}))
vi.mock('@/modules/production/hooks/use-suppliers', () => ({
  useSuppliers: () => EMPTY_LIST,
}))
//  Người dùng cũng phải là MỘT tham chiếu: trang nạp lại bản nháp mỗi khi `user` đổi.
const AUTH = { user: { id: 1, full_name: 'Người khảo sát' } }
vi.mock('@/core/auth/use-auth', () => ({
  useAuth: () => AUTH,
}))
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAccess: () => true }),
}))

//  Bốn khối chân trang tự gọi API riêng, không phải thứ bài này soi.
vi.mock('../components/document-attachments-card', () => ({ DocumentAttachmentsCard: () => null }))
vi.mock('../components/document-comments', () => ({ DocumentComments: () => null }))
vi.mock('@/shared/audit', () => ({ AuditTimeline: () => null }))
vi.mock('@/modules/dossier/components/required-dossiers-card', () => ({
  RequiredDossiersCard: () => null,
}))

function makeSurvey(changes: Partial<SurveyDetail> = {}): SurveyDetail {
  return {
    id: 5,
    code: 'PKS-0005',
    survey_type: 'supplier',
    pr_code: '',
    survey_request_id: 0,
    sr_code: '',
    received_date: '2026-11-01',
    result_due_date: '',
    item_group: '',
    main_content: 'Khảo sát bao bì',
    requirement_detail: '',
    request_qty: 0,
    nspt: 'Người khảo sát',
    has_product_code: false,
    item_code: '',
    item_name: '',
    uom: '',
    proposed_rate: 0,
    approve_note: '',
    status: 'draft',
    created_at: '2026-11-01T08:00:00',
    created_by: 1,
    supplier_lines: [
      { id: 11, supplier_code: 'NCC-A', supplier_name: 'CÔNG TY A' },
      { id: 12, supplier_code: 'NCC-B', supplier_name: 'CÔNG TY B' },
    ],
    product_lines: [],
    supplier_count: 2,
    product_count: 0,
    subtotal: 0,
    main: '',
    ...changes,
  }
}

function build(survey: SurveyDetail) {
  currentSurvey = survey
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/procurement/surveys/5']}>
        <Routes>
          <Route path="/procurement/surveys/:id" element={<SurveyDetailPage />} />
          <Route path="/procurement/surveys" element={<p>Danh sách phiếu khảo sát</p>} />
        </Routes>
        <ConfirmDialogHost />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

/** Số dòng NCC đang hiện trên bảng — đọc từ tiêu đề "<n> dòng" của bảng. */
function supplierRowCount() {
  return screen.getAllByText(/^\d+ dòng$/)[0].textContent
}

beforeEach(() => {
  runAction.mockReset().mockResolvedValue(undefined)
  deleteSurvey.mockReset().mockResolvedValue(undefined)
  localStorage.clear()
})

describe('SurveyDetailPage — nút đầu trang theo chữ bản v1', () => {
  it('shows the PYC code badge next to the title like v1', () => {
    build(makeSurvey({ pr_code: 'PYC-0099' }))

    expect(screen.getByTitle('Mã yêu cầu khảo sát')).toHaveTextContent('PYC-0099')
  })

  it('shows no code badge when the survey has no PYC code', () => {
    build(makeSurvey())

    expect(screen.queryByTitle('Mã yêu cầu khảo sát')).toBeNull()
  })

  it('Xóa phiếu asks Xác nhận / Xóa phiếu khảo sát này? with Đồng ý / Hủy, and Hủy keeps the survey', async () => {
    const user = userEvent.setup()
    build(makeSurvey())

    await user.click(screen.getByRole('button', { name: 'Xóa phiếu' }))
    //  Hộp `askConfirm` của v1: tiêu đề *Xác nhận*, thân đúng một câu hỏi.
    const dialog = await screen.findByRole('alertdialog', { name: 'Xác nhận' })
    expect(dialog).toHaveAccessibleDescription('Xóa phiếu khảo sát này?')
    expect(within(dialog).getByRole('button', { name: 'Đồng ý' })).toBeInTheDocument()

    await user.click(within(dialog).getByRole('button', { name: 'Hủy' }))
    expect(deleteSurvey).not.toHaveBeenCalled()
  })

  it('Đồng ý in the delete box deletes and goes back to the list', async () => {
    const user = userEvent.setup()
    build(makeSurvey())

    await user.click(screen.getByRole('button', { name: 'Xóa phiếu' }))
    await user.click(await screen.findByRole('button', { name: 'Đồng ý' }))

    expect(deleteSurvey).toHaveBeenCalledWith(5)
    expect(await screen.findByText('Danh sách phiếu khảo sát')).toBeInTheDocument()
  })

  it('Duyệt asks Duyệt cả phiếu khảo sát này? first — Hủy approves nothing', async () => {
    const user = userEvent.setup()
    build(makeSurvey({ status: 'submitted' }))

    await user.click(screen.getByRole('button', { name: 'Duyệt' }))
    expect(await screen.findByText('Duyệt cả phiếu khảo sát này?')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Hủy' }))

    expect(runAction).not.toHaveBeenCalled()
  })

  it('Duyệt phiếu in the confirm box approves the whole survey', async () => {
    const user = userEvent.setup()
    build(makeSurvey({ status: 'submitted' }))

    await user.click(screen.getByRole('button', { name: 'Duyệt' }))
    await user.click(await screen.findByRole('button', { name: 'Duyệt phiếu' }))

    expect(runAction).toHaveBeenCalledWith({ action: 'approve' })
  })

  it('Trả về carries the v1 tooltip and opens a box titled Trả về with Trả về / Hủy', async () => {
    const user = userEvent.setup()
    build(makeSurvey({ status: 'submitted' }))

    const back = screen.getByRole('button', { name: 'Trả về' })
    expect(back).toHaveAttribute('title', 'Trả về để người khảo sát sửa & gửi lại')

    await user.click(back)
    const dialog = await screen.findByRole('dialog', { name: 'Trả về' })
    const confirmButton = within(dialog).getByRole('button', { name: 'Trả về' })
    expect(within(dialog).getByRole('button', { name: 'Hủy' })).toBeInTheDocument()
    //  Lý do vẫn bắt buộc — backend chặn reject / cancel không có lý do.
    expect(confirmButton).toBeDisabled()

    await user.type(within(dialog).getByRole('textbox', { name: 'Lý do' }), 'Thiếu báo giá')
    await user.click(confirmButton)
    expect(runAction).toHaveBeenCalledWith({ action: 'reject', reason: 'Thiếu báo giá' })
  })

  it('an approved survey offers Trả về as Hủy duyệt in the tooltip', () => {
    build(makeSurvey({ status: 'approved' }))

    expect(screen.getByRole('button', { name: 'Trả về' })).toHaveAttribute(
      'title',
      'Hủy duyệt — trả về để người khảo sát sửa & gửi lại',
    )
  })

  it('Từ chối carries the v1 tooltip and opens Từ chối phiếu with Từ chối / Hủy', async () => {
    const user = userEvent.setup()
    build(makeSurvey({ status: 'submitted' }))

    const reject = screen.getByRole('button', { name: 'Từ chối' })
    expect(reject).toHaveAttribute('title', 'Khóa phiếu — không sửa lại được')

    await user.click(reject)
    const dialog = await screen.findByRole('dialog', { name: 'Từ chối phiếu' })
    expect(within(dialog).getByText('Lý do từ chối (khóa phiếu):')).toBeInTheDocument()
    await user.type(within(dialog).getByRole('textbox', { name: 'Lý do' }), 'Sai NCC')
    await user.click(within(dialog).getByRole('button', { name: 'Từ chối' }))

    expect(runAction).toHaveBeenCalledWith({ action: 'cancel', reason: 'Sai NCC' })
  })
})

describe('SurveyDetailPage — bảng dòng hỏi lại như bản v1', () => {
  it('Thêm nhiều opens the v1 prompt Nhập thông tin with Xác nhận / Hủy', async () => {
    const user = userEvent.setup()
    build(makeSurvey())

    await user.click(screen.getAllByRole('button', { name: 'Thêm nhiều' })[0])
    const dialog = await screen.findByRole('dialog', { name: 'Nhập thông tin' })
    expect(within(dialog).getByText('Thêm bao nhiêu dòng?')).toBeInTheDocument()
    expect(within(dialog).getByRole('button', { name: 'Hủy' })).toBeInTheDocument()

    await user.click(within(dialog).getByRole('button', { name: 'Xác nhận' }))
    //  Mặc định 3 dòng như v1: 2 dòng sẵn + 3 dòng mới.
    expect(supplierRowCount()).toBe('5 dòng')
  })

  it('Enter in the Thêm nhiều box confirms, and a nonsense number adds nothing', async () => {
    const user = userEvent.setup()
    build(makeSurvey())

    await user.click(screen.getAllByRole('button', { name: 'Thêm nhiều' })[0])
    const input = await screen.findByRole('spinbutton', { name: 'Số dòng cần thêm' })
    await user.clear(input)
    await user.type(input, '-4{Enter}')

    expect(screen.queryByRole('dialog', { name: 'Nhập thông tin' })).toBeNull()
    expect(supplierRowCount()).toBe('2 dòng')
  })

  it('deleting one row asks Xóa dòng này? — Hủy keeps the row', async () => {
    const user = userEvent.setup()
    build(makeSurvey())

    await user.click(screen.getAllByRole('button', { name: 'Xóa dòng' })[0])
    expect(await screen.findByText('Xóa dòng này?')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Hủy' }))

    expect(supplierRowCount()).toBe('2 dòng')
  })

  it('Đồng ý removes exactly that row', async () => {
    const user = userEvent.setup()
    build(makeSurvey())

    await user.click(screen.getAllByRole('button', { name: 'Xóa dòng' })[0])
    await user.click(await screen.findByRole('button', { name: 'Đồng ý' }))

    expect(supplierRowCount()).toBe('1 dòng')
  })

  it('Xóa dòng đã chọn (n) asks Xóa các dòng đã chọn? before removing the ticked rows', async () => {
    const user = userEvent.setup()
    build(makeSurvey())

    await user.click(screen.getAllByRole('checkbox', { name: 'Chọn dòng 1' })[0])
    await user.click(screen.getByRole('button', { name: 'Xóa dòng đã chọn (1)' }))
    expect(await screen.findByText('Xóa các dòng đã chọn?')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Hủy' }))
    expect(supplierRowCount()).toBe('2 dòng')

    await user.click(screen.getByRole('button', { name: 'Xóa dòng đã chọn (1)' }))
    await user.click(await screen.findByRole('button', { name: 'Đồng ý' }))
    expect(supplierRowCount()).toBe('1 dòng')
  })
})
