import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ConfirmDialogHost } from '@/shared/ui/confirm-dialog'
import type {
  AvailableSurveyLine,
  SurveyProcessOption,
  SurveyRequestProcess,
} from '../types/survey-request-process'
import { SurveyRequestProcessCard } from './survey-request-process-card'

/**
 * duoc-CR-738 — bảng *Kết quả khảo sát đã duyệt* ở màn Xử lý khảo sát (YCBG) bấm tiêu đề cột
 * là sắp phía server như bản v1. Chặn ở tầng `@/core/api` (hook thật) để soi đúng bộ tham số
 * đi ra đường `available-survey-lines`: có `sort_by` / `sort_dir`, trang về 1, bộ lọc giữ nguyên.
 */

const availableCalls: Record<string, unknown>[] = []
let availableTotal = 20
/** Dữ liệu `/process` của từng bài — bài nào cần phương án / dòng rỗng thì tự gán. */
let processData: () => SurveyRequestProcess = () => buildProcess()
/** Kết quả khảo sát trả về bảng chọn — mặc định một dòng. */
let availableItems: () => AvailableSurveyLine[] = () => [buildAvailable()]
const apiPostMock = vi.fn((..._args: unknown[]) => Promise.resolve(buildProcess()))
const apiDeleteMock = vi.fn((..._args: unknown[]) => Promise.resolve(buildProcess()))

vi.mock('@/core/api', async (importOriginal) => ({
  ...(await importOriginal<Record<string, unknown>>()),
  apiGet: (url: string, config?: { params?: Record<string, unknown> }) => {
    if (url.endsWith('/process')) return Promise.resolve(processData())
    if (url.includes('/available-survey-lines')) {
      availableCalls.push({ ...(config?.params ?? {}) })
      return Promise.resolve({ items: availableItems(), total: availableTotal })
    }
    return Promise.resolve({ items: [], total: 0 })
  },
  apiPost: (...args: unknown[]) => apiPostMock(...args),
  apiDelete: (...args: unknown[]) => apiDeleteMock(...args),
}))

//  Soi số toast: gắn n dòng phải ra MỘT câu tổng, không n câu chồng nhau (rà mã duoc-CR-741).
const toastMock = vi.hoisted(() => ({ success: vi.fn(), error: vi.fn() }))
vi.mock('sonner', async (importOriginal) => ({
  ...(await importOriginal<Record<string, unknown>>()),
  toast: toastMock,
}))

vi.mock('@/modules/production/hooks/use-suppliers', () => ({
  useSuppliers: () => ({ data: { items: [] } }),
}))

vi.mock('../hooks/use-purchase-request-support', () => ({
  usePurchaseRequestItemGroups: () => ({ data: { items: [] } }),
  usePurchaseRequestProducts: () => ({ data: { items: [] }, isLoading: false, isError: false }),
}))

function buildProcess(): SurveyRequestProcess {
  return {
    id: 28,
    code: 'YCBG28082601',
    status: 'processing',
    request_date: '2026-08-28',
    department: 'Marketing',
    requester: 'Nguyễn Văn A',
    company_id: 1,
    lines: [
      {
        id: 301,
        internal_line_code: 'L1',
        item_group: 'Bao bì',
        requirement_detail: 'Thùng carton',
        other_requirement: '',
        request_qty: 100,
        uom: 'Cái',
        proposed_price: 0,
        assignee: 'NSTM01',
        assignee_name: 'NSTM 01',
        is_completed: false,
        no_option: false,
        options: [],
        can_process: true,
      },
    ],
  }
}

function buildAvailable(id = 900, productName = 'Thùng carton 5 lớp'): AvailableSurveyLine {
  return {
    id,
    supplier_code: 'NCC-A',
    supplier_name: 'CÔNG TY A',
    internal_code: 'A-01',
    product_name: productName,
    spec: '',
    origin: 'VN',
    quote_unit: 'Cái',
    moq: 100,
    price_by_volume: 12000,
    volume_range: '',
    vat: 8,
    delivery_time: '',
    delivery_place: '',
    shipping_cost: 0,
    sample_ready: false,
    lab_result: '',
    survey_item_group: 'Bao bì',
    survey_code: 'KS-0042',
    survey_item_code: 'VTBB-1',
    result_date: '2026-10-02',
  }
}

function renderCard() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <SurveyRequestProcessCard surveyRequestId={28} status="processing" />
      {/*  Hộp hỏi lại toàn cục — dựng thật để bấm đúng nút như người dùng. */}
      <ConfirmDialogHost />
    </QueryClientProvider>,
  )
}

const lastCall = () => availableCalls[availableCalls.length - 1]

beforeEach(() => {
  availableCalls.length = 0
  availableTotal = 20
  processData = () => buildProcess()
  availableItems = () => [buildAvailable()]
  apiPostMock.mockClear()
  apiDeleteMock.mockClear()
  toastMock.success.mockClear()
  toastMock.error.mockClear()
  window.localStorage.clear()
})

describe('SurveyRequestProcessCard — sắp xếp bảng kết quả khảo sát', () => {
  it('sends no sort params until a header is clicked, so the backend keeps newest first', async () => {
    renderCard()
    await screen.findByText('CÔNG TY A')
    expect(lastCall()).not.toHaveProperty('sort_by')
    expect(lastCall()).not.toHaveProperty('sort_dir')
  })

  it('sorts by the backend key of the clicked column and goes back to page 1, keeping filters', async () => {
    const user = userEvent.setup()
    renderCard()
    await screen.findByText('CÔNG TY A')

    //  Lật sang trang 2 trước — đổi sắp xếp mà giữ trang cũ là xem nhầm khúc giữa danh sách mới.
    await user.click(screen.getByRole('button', { name: 'Trang sau' }))
    await waitFor(() => expect(lastCall()).toMatchObject({ page: 2 }))

    await user.click(screen.getByText('Đơn giá'))
    await waitFor(() =>
      expect(lastCall()).toMatchObject({
        sort_by: 'price_by_volume',
        sort_dir: 'asc',
        page: 1,
        item_group: ['Bao bì'],
      }),
    )

    await user.click(screen.getByText('Đơn giá'))
    await waitFor(() => expect(lastCall()).toMatchObject({ sort_by: 'price_by_volume', sort_dir: 'desc' }))

    //  Nhịp thứ ba thôi sắp xếp: không gửi `sort_by` nữa, backend về mặc định.
    await user.click(screen.getByText('Đơn giá'))
    await waitFor(() => expect(lastCall()).not.toHaveProperty('sort_by'))
  })

  it('maps the NCC column to supplier_code and starts the survey date column at newest first', async () => {
    const user = userEvent.setup()
    renderCard()
    await screen.findByText('CÔNG TY A')

    await user.click(screen.getByText('NCC'))
    await waitFor(() => expect(lastCall()).toMatchObject({ sort_by: 'supplier_code', sort_dir: 'asc' }))

    await user.click(screen.getByText('Ngày KS'))
    await waitFor(() => expect(lastCall()).toMatchObject({ sort_by: 'result_date', sort_dir: 'desc' }))
  })

  it('does not sort by columns the backend cannot order (Phân loại KS, Phiếu KS)', async () => {
    const user = userEvent.setup()
    renderCard()
    await screen.findByText('CÔNG TY A')
    const callsBefore = availableCalls.length

    await user.click(screen.getByText('Phân loại KS'))
    await user.click(screen.getByText('Phiếu KS'))

    expect(availableCalls.length).toBe(callsBefore)
    expect(lastCall()).not.toHaveProperty('sort_by')
  })
})

function buildOption(overrides: Partial<SurveyProcessOption> = {}): SurveyProcessOption {
  return {
    id: 71,
    public_id: 1,
    display_label: 'Option 1',
    is_chosen: false,
    system_product_code: '',
    product_survey_line_id: 555,
    snap_product_name: 'Thùng carton 3 lớp',
    snap_spec: '',
    snap_origin: '',
    snap_quote_unit: 'Cái',
    snap_moq: 0,
    snap_price_by_volume: 9000,
    snap_volume_range: '',
    snap_vat: 0,
    snap_delivery_time: '',
    snap_delivery_place: '',
    snap_shipping_cost: 0,
    snap_sample_ready: false,
    snap_lab_result: '',
    snap_internal_code: '',
    supplier_code: 'NCC-B',
    supplier_name: 'CÔNG TY B',
    nstm_note: '',
    ...overrides,
  }
}

function processWithOption(option: SurveyProcessOption): SurveyRequestProcess {
  const base = buildProcess()
  return { ...base, lines: base.lines.map((line) => ({ ...line, options: [option] })) }
}

/**
 * duoc-CR-741 — hộp hỏi lại và nút của bản v1 (`frontend/src/pages/SurveyRequestProcess.tsx`)
 * mà v2 thiếu: xóa option phải hỏi, chốt khi không còn dòng rỗng phải hỏi, hộp chốt rỗng nói
 * đúng chữ v1, và tick nhiều kết quả để gắn một lượt.
 */
describe('SurveyRequestProcessCard — hộp hỏi lại và nút theo v1 (duoc-CR-741)', () => {
  it('asks Xóa phương án này? before removing an option, and does nothing when cancelled', async () => {
    const user = userEvent.setup()
    processData = () => processWithOption(buildOption())
    renderCard()

    const remove = await screen.findByRole('button', { name: 'Xóa option' })
    expect(remove).toHaveAttribute('title', 'Xóa option')

    await user.click(remove)
    const dialog = await screen.findByRole('alertdialog')
    expect(dialog).toHaveTextContent('Xóa phương án này?')
    await user.click(within(dialog).getByRole('button', { name: 'Hủy' }))
    expect(apiDeleteMock).not.toHaveBeenCalled()

    await user.click(screen.getByRole('button', { name: 'Xóa option' }))
    await user.click(within(await screen.findByRole('alertdialog')).getByRole('button', { name: 'Đồng ý' }))
    await waitFor(() =>
      expect(apiDeleteMock).toHaveBeenCalledWith('/api/survey-requests/28/lines/301/options/71'),
    )
  })

  it('warns in the tooltip when the requester already picked the option', async () => {
    processData = () => processWithOption(buildOption({ is_chosen: true }))
    renderCard()

    const remove = await screen.findByRole('button', { name: 'Xóa option' })
    expect(remove.getAttribute('title')).toMatch(/^Xóa option \(người YC đang chọn/)
  })

  it('asks Chốt hoàn thành khảo sát? when no line is empty, and only posts after Chốt hoàn thành', async () => {
    const user = userEvent.setup()
    processData = () => processWithOption(buildOption())
    renderCard()

    await user.click(await screen.findByRole('button', { name: 'Chốt hoàn thành khảo sát' }))
    let dialog = await screen.findByRole('alertdialog')
    expect(dialog).toHaveTextContent('Chốt hoàn thành')
    expect(dialog).toHaveTextContent('Chốt hoàn thành khảo sát?')
    await user.click(within(dialog).getByRole('button', { name: 'Hủy' }))
    expect(apiPostMock).not.toHaveBeenCalled()

    await user.click(screen.getByRole('button', { name: 'Chốt hoàn thành khảo sát' }))
    dialog = await screen.findByRole('alertdialog')
    await user.click(within(dialog).getByRole('button', { name: 'Chốt hoàn thành' }))
    await waitFor(() =>
      expect(apiPostMock).toHaveBeenCalledWith('/api/survey-requests/28/complete', { empty_line_ids: [] }),
    )
  })

  it('opens the empty-line dialog with the v1 buttons Hủy and Chốt (n chốt rỗng)', async () => {
    const user = userEvent.setup()
    renderCard()

    await user.click(await screen.findByRole('button', { name: 'Chốt hoàn thành khảo sát' }))
    const dialog = await screen.findByRole('dialog', { name: 'Chốt rỗng sản phẩm chưa có phương án' })
    //  Không đi qua hộp hỏi chung: hộp chốt rỗng đã là bước xác nhận.
    expect(screen.queryByRole('alertdialog')).toBeNull()
    expect(within(dialog).getByRole('button', { name: 'Hủy' })).toBeInTheDocument()
    const commit = within(dialog).getByRole('button', { name: 'Chốt (0 chốt rỗng)' })
    expect(commit).toBeDisabled()

    await user.click(within(dialog).getByRole('checkbox'))
    const commitOne = within(dialog).getByRole('button', { name: 'Chốt (1 chốt rỗng)' })
    expect(commitOne).toBeEnabled()
    await user.click(commitOne)
    await waitFor(() =>
      expect(apiPostMock).toHaveBeenCalledWith('/api/survey-requests/28/complete', {
        empty_line_ids: [301],
      }),
    )
  })

  it('attaches every ticked result one by one with Thêm n dòng đã chọn làm option', async () => {
    const user = userEvent.setup()
    availableItems = () => [buildAvailable(900, 'Thùng A'), buildAvailable(901, 'Thùng B'), buildAvailable(902, 'Thùng C')]
    renderCard()
    await screen.findByText('Thùng A')

    expect(screen.queryByRole('button', { name: /dòng đã chọn làm option/ })).toBeNull()
    await user.click(screen.getByRole('checkbox', { name: 'Chọn Thùng A' }))
    await user.click(screen.getByRole('checkbox', { name: 'Chọn Thùng C' }))
    await user.click(screen.getByRole('button', { name: 'Thêm 2 dòng đã chọn làm option' }))

    await waitFor(() => expect(apiPostMock).toHaveBeenCalledTimes(2))
    expect(apiPostMock.mock.calls.map((call) => call[1])).toEqual([
      { product_survey_line_id: 900 },
      { product_survey_line_id: 902 },
    ])
    expect(apiPostMock.mock.calls[0][0]).toBe('/api/survey-requests/28/lines/301/options')
    //  Xong thì bỏ hết lựa chọn, nút biến mất.
    await waitFor(() =>
      expect(screen.queryByRole('button', { name: /dòng đã chọn làm option/ })).toBeNull(),
    )
    //  Một câu tổng cho cả lượt, không phải hai câu *Đã thêm phương án*.
    expect(toastMock.success).toHaveBeenCalledTimes(1)
    expect(toastMock.success).toHaveBeenCalledWith('Đã thêm 2 phương án')
  })

  it('keeps going after one attach fails, like v1, and still clears the selection', async () => {
    const user = userEvent.setup()
    availableItems = () => [buildAvailable(900, 'Thùng A'), buildAvailable(901, 'Thùng B')]
    apiPostMock.mockImplementationOnce(() => Promise.reject(new Error('trùng')))
    renderCard()
    await screen.findByText('Thùng A')

    await user.click(screen.getByRole('checkbox', { name: 'Chọn cả trang' }))
    await user.click(screen.getByRole('button', { name: 'Thêm 2 dòng đã chọn làm option' }))

    await waitFor(() => expect(apiPostMock).toHaveBeenCalledTimes(2))
    await waitFor(() =>
      expect(screen.queryByRole('button', { name: /dòng đã chọn làm option/ })).toBeNull(),
    )
    expect(toastMock.success).toHaveBeenCalledTimes(1)
    expect(toastMock.success).toHaveBeenCalledWith('Đã thêm 1 phương án, 1 dòng không thêm được')
  })

  it('says nothing was added when every attach fails', async () => {
    const user = userEvent.setup()
    availableItems = () => [buildAvailable(900, 'Thùng A'), buildAvailable(901, 'Thùng B')]
    apiPostMock.mockImplementation(() => Promise.reject(new Error('trùng')))
    try {
      renderCard()
      await screen.findByText('Thùng A')
      await user.click(screen.getByRole('checkbox', { name: 'Chọn cả trang' }))
      await user.click(screen.getByRole('button', { name: 'Thêm 2 dòng đã chọn làm option' }))

      await waitFor(() => expect(toastMock.error).toHaveBeenCalledWith('Không thêm được 2 dòng nào'))
      expect(toastMock.success).not.toHaveBeenCalled()
    } finally {
      apiPostMock.mockImplementation(() => Promise.resolve(buildProcess()))
    }
  })

  it('a double click on the bulk button still posts each row only once', async () => {
    const user = userEvent.setup()
    availableItems = () => [buildAvailable(900, 'Thùng A'), buildAvailable(901, 'Thùng B')]
    renderCard()
    await screen.findByText('Thùng A')
    await user.click(screen.getByRole('checkbox', { name: 'Chọn cả trang' }))
    await user.dblClick(screen.getByRole('button', { name: 'Thêm 2 dòng đã chọn làm option' }))

    await waitFor(() => expect(toastMock.success).toHaveBeenCalledTimes(1))
    expect(apiPostMock).toHaveBeenCalledTimes(2)
  })

  it('drops the selection when the page changes, so ticks never carry to rows out of sight', async () => {
    const user = userEvent.setup()
    renderCard()
    await screen.findByText('CÔNG TY A')

    await user.click(screen.getByRole('checkbox', { name: 'Chọn Thùng carton 5 lớp' }))
    expect(screen.getByRole('button', { name: 'Thêm 1 dòng đã chọn làm option' })).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Trang sau' }))
    await waitFor(() =>
      expect(screen.queryByRole('button', { name: /dòng đã chọn làm option/ })).toBeNull(),
    )
  })
})
