// duoc-CR-612 — khối Báo cáo thực hiện, dạng «Bảng» sửa ngay trên hàng. Chạy qua NGUYÊN
// `SurveyReportCard` (hook + cache thật, chỉ giả tầng `@/core/api`) để bắt đúng thứ gửi lên
// backend: PATCH thừa trường là ghi đè trường người khác vừa sửa; PATCH nhầm id là sửa nhầm hồ sơ.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { SurveyReportDoc, SurveyRequestReport } from '../../types/survey-request-report'
import { SurveyReportCard } from './survey-report-card'

const apiGet = vi.fn()
const apiPost = vi.fn()
const apiPatch = vi.fn()
vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: (...args: unknown[]) => apiPost(...args),
  apiPatch: (...args: unknown[]) => apiPatch(...args),
  apiDelete: vi.fn(),
}))
vi.mock('@/core/auth/use-auth', () => ({ useAuth: () => ({ user: { employee_id: 42 } }) }))
vi.mock('@/shared/ui/confirm-dialog', () => ({ confirm: vi.fn().mockResolvedValue(true) }))

const PHASE_LEGAL = 10
const PHASE_ORDER = 20
const ITEM_CAP = 5
const BASE = '/api/execution-report/survey_request/7'

function makeDoc(id: number, phaseId: number, itemId: number, title: string): SurveyReportDoc {
  return {
    id,
    phase_id: phaseId,
    item_id: itemId,
    title,
    description: '',
    required: false,
    status: 0,
    status_label: 'Chưa bắt đầu',
    file_note: '',
    result: '',
    depends: [],
    start_date: '',
    expires_at: '',
    planned_date: '',
    assignee_id: 0,
    assignee_name: '',
    sort_order: id,
  }
}

function makeReport(docs: SurveyReportDoc[]): SurveyRequestReport {
  return {
    items: [{ id: ITEM_CAP, name: 'Nắp 50 75ml', line_id: 0, sort_order: 0 }],
    phases: [
      { id: PHASE_LEGAL, name: 'Pháp lý & Giấy phép', location: '', sort_order: 0 },
      { id: PHASE_ORDER, name: 'Đặt hàng & Hợp đồng', location: '', sort_order: 1 },
    ],
    docs,
    restorable: false,
    restorable_audit_id: 0,
  }
}

const REPORT = makeReport([
  //  Cố ý đứng TRƯỚC trong mảng nhưng thuộc giai đoạn 2 — bảng phải xếp nó xuống dưới.
  makeDoc(3, PHASE_ORDER, ITEM_CAP, 'Hợp đồng nắp'),
  makeDoc(1, PHASE_LEGAL, 0, 'Giấy phép nhập khẩu'),
  {
    ...makeDoc(2, PHASE_LEGAL, ITEM_CAP, 'Giấy CN lưu hành'),
    //  Chờ hồ sơ 1 (chưa xong) → khóa.
    depends: [1],
    //  Nhân sự đã nghỉ: không có trong danh bạ đang hoạt động.
    assignee_id: 99,
    assignee_name: 'Trần Văn Nghỉ',
  },
])

function mockApi(report: SurveyRequestReport) {
  apiGet.mockReset().mockImplementation((url: string) =>
    Promise.resolve(
      url.startsWith('/api/employees')
        ? { items: [{ id: 42, full_name: 'Nguyễn An', code: 'NV042' }], total: 1 }
        : report,
    ),
  )
}

function renderCard(canEdit = true) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <SurveyReportCard ownerId={7} canEdit={canEdit} />
    </QueryClientProvider>,
  )
}

async function openCard() {
  fireEvent.click(await screen.findByRole('button', { name: /Báo cáo thực hiện/ }))
  return screen.findByRole('table')
}

function bodyRows(table: HTMLElement) {
  return within(table).getAllByRole('row').slice(1)
}

describe('SurveyReportCard — table view with inline editing', () => {
  beforeEach(() => {
    localStorage.clear()
    mockApi(REPORT)
    apiPost.mockReset().mockResolvedValue(REPORT)
    apiPatch.mockReset().mockResolvedValue(REPORT)
  })

  it('opens in table view for someone who never picked a view, but keeps an earlier choice', async () => {
    renderCard()
    await openCard()
    expect(screen.getByRole('button', { name: 'Bảng' })).toHaveAttribute('aria-pressed', 'true')
    //  Dạng bảng không có gì để gấp — nút «Mở tất cả» chỉ gây hiểu nhầm.
    expect(screen.queryByRole('button', { name: /Mở tất cả|Thu gọn/ })).not.toBeInTheDocument()
  })

  it('respects a stored by-line preference instead of forcing the new table', async () => {
    localStorage.setItem('erp.survey-report.view', 'item')
    renderCard()
    fireEvent.click(await screen.findByRole('button', { name: /Báo cáo thực hiện/ }))
    expect(await screen.findByRole('button', { name: 'Theo dòng hàng' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
  })

  it('orders rows by phase sequence, not by the order the API returned them', async () => {
    renderCard()
    const table = await openCard()
    const titles = bodyRows(table)
      .slice(0, 3)
      .map((row) => within(row).getByRole('button', { name: /Sửa tên hồ sơ/ }).textContent)
    expect(titles).toEqual(['Giấy phép nhập khẩu', 'Giấy CN lưu hành', 'Hợp đồng nắp'])
  })

  it('patches ONLY the edited title of the right doc', async () => {
    renderCard()
    await openCard()
    fireEvent.click(screen.getByRole('button', { name: /^Sửa tên hồ sơ "Hợp đồng nắp"/ }))
    const input = screen.getByRole('textbox', { name: 'tên hồ sơ "Hợp đồng nắp"' })
    fireEvent.change(input, { target: { value: 'Hợp đồng nắp v2' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    await waitFor(() => expect(apiPatch).toHaveBeenCalledTimes(1))
    expect(apiPatch).toHaveBeenCalledWith(`${BASE}/docs/3`, { title: 'Hợp đồng nắp v2' })
  })

  it('patches the result note and allows wiping it to an empty string', async () => {
    mockApi(makeReport([{ ...makeDoc(1, PHASE_LEGAL, 0, 'A'), result: 'đã nộp' }]))
    renderCard()
    await openCard()
    fireEvent.click(screen.getByRole('button', { name: /^Sửa kết quả hồ sơ "A"/ }))
    const input = screen.getByRole('textbox', { name: 'kết quả hồ sơ "A"' })
    fireEvent.change(input, { target: { value: '' } })
    fireEvent.blur(input)
    await waitFor(() => expect(apiPatch).toHaveBeenCalledWith(`${BASE}/docs/1`, { result: '' }))
  })

  it('toggles the required flag straight from the checkbox', async () => {
    renderCard()
    await openCard()
    fireEvent.click(screen.getByRole('checkbox', { name: 'Hồ sơ "Hợp đồng nắp" bắt buộc' }))
    await waitFor(() =>
      expect(apiPatch).toHaveBeenCalledWith(`${BASE}/docs/3`, { required: true }),
    )
  })

  it('sends edits one after another so an older response cannot overwrite a newer one', async () => {
    let releaseFirst: (value: SurveyRequestReport) => void = () => {}
    apiPatch
      .mockReset()
      .mockImplementationOnce(
        () => new Promise<SurveyRequestReport>((resolve) => (releaseFirst = resolve)),
      )
      .mockResolvedValue(REPORT)
    renderCard()
    await openCard()
    fireEvent.click(screen.getByRole('checkbox', { name: 'Hồ sơ "Hợp đồng nắp" bắt buộc' }))
    fireEvent.click(screen.getByRole('checkbox', { name: 'Hồ sơ "Giấy phép nhập khẩu" bắt buộc' }))
    await waitFor(() => expect(apiPatch).toHaveBeenCalledTimes(1))
    //  Lượt hai phải CHỜ lượt một về rồi mới đi.
    await new Promise((resolve) => setTimeout(resolve, 20))
    expect(apiPatch).toHaveBeenCalledTimes(1)
    releaseFirst(REPORT)
    await waitFor(() => expect(apiPatch).toHaveBeenCalledTimes(2))
    expect(apiPatch.mock.calls[1]).toEqual([`${BASE}/docs/1`, { required: true }])
  })

  it('blocks ticking a locked doc as done and shows what it waits for', async () => {
    renderCard()
    await openCard()
    expect(
      screen.getByRole('button', { name: 'Đánh dấu hoàn thành "Giấy CN lưu hành"' }),
    ).toBeDisabled()
    expect(screen.getByTitle('Chờ hồ sơ tiên quyết: Giấy phép nhập khẩu')).toBeInTheDocument()
  })

  it('still shows the name of an assignee who left the company', async () => {
    renderCard()
    const table = await openCard()
    await waitFor(() => expect(within(table).getByText('Trần Văn Nghỉ')).toBeInTheDocument())
  })

  it('adds a doc from the last row with the current user as assignee, ignoring blank names', async () => {
    renderCard()
    const table = await openCard()
    const input = within(table).getByRole('textbox', { name: 'Tên hồ sơ mới' })
    fireEvent.change(input, { target: { value: '    ' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(within(table).getByRole('button', { name: 'Thêm hồ sơ' })).toBeDisabled()
    expect(apiPost).not.toHaveBeenCalled()

    fireEvent.change(input, { target: { value: '  C/O form E  ' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    //  Enter lần hai trong lúc lượt đầu chưa về không được đẻ hồ sơ trùng.
    fireEvent.keyDown(input, { key: 'Enter' })
    await waitFor(() => expect(apiPost).toHaveBeenCalledTimes(1))
    expect(apiPost).toHaveBeenCalledWith(
      `${BASE}/docs`,
      expect.objectContaining({
        title: 'C/O form E',
        phase_id: PHASE_LEGAL,
        item_id: 0,
        assignee_id: 42,
        depends: [],
      }),
    )
    await waitFor(() => expect(input).toHaveValue(''))
  })

  it('tells "no match for the filter" apart from "no docs yet"', async () => {
    renderCard()
    await openCard()
    fireEvent.change(screen.getByLabelText('Tìm hồ sơ trong báo cáo'), {
      target: { value: 'không có hồ sơ nào tên thế này' },
    })
    expect(await screen.findByText('Không có hồ sơ nào khớp bộ lọc hiện tại.')).toBeInTheDocument()
  })

  it('invites typing in the last row when phases exist but no doc yet', async () => {
    mockApi(makeReport([]))
    renderCard()
    await openCard()
    expect(screen.getByText('Chưa có hồ sơ nào — gõ tên ở hàng cuối để thêm.')).toBeInTheDocument()
  })

  it('gives a read-only user plain text: no edit buttons, no add row, no checkboxes to tick', async () => {
    renderCard(false)
    const table = await openCard()
    expect(within(table).getByText('Hợp đồng nắp')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Sửa tên hồ sơ/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('textbox', { name: 'Tên hồ sơ mới' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Xóa hồ sơ/ })).not.toBeInTheDocument()
    //  «Bắt buộc» là chữ, không phải ô tick mờ `disabled` (luật ô chỉ xem).
    expect(within(table).queryAllByRole('checkbox')).toHaveLength(0)
    expect(screen.getByRole('button', { name: 'Đánh dấu hoàn thành "Hợp đồng nắp"' })).toBeDisabled()
    //  Người chỉ xem không cần danh bạ — gọi là ăn 403 khi thiếu quyền nhân sự.
    expect(apiGet.mock.calls.some(([url]) => String(url).startsWith('/api/employees'))).toBe(false)
  })

  //  Lỗi rà soát C1: sửa Mô tả trên hàng rồi bấm ✎ ngay — hộp sửa nạp ảnh CŨ, lưu hộp
  //  mà gửi NGUYÊN ảnh là đè mất mô tả vừa sửa. Hộp chỉ được gửi trường đổi trong hộp.
  it('saving the full edit dialog sends only fields changed there, not a stale snapshot', async () => {
    renderCard()
    await openCard()
    fireEvent.click(screen.getByRole('button', { name: /^Sửa mô tả hồ sơ "Hợp đồng nắp"/ }))
    fireEvent.change(screen.getByRole('textbox', { name: 'mô tả hồ sơ "Hợp đồng nắp"' }), {
      target: { value: 'Mô tả mới' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Sửa đầy đủ hồ sơ "Hợp đồng nắp"' }))
    const dialog = await screen.findByRole('dialog')
    fireEvent.change(within(dialog).getByPlaceholderText('VD: GP-tienchat.pdf · hoặc dán link Drive'), {
      target: { value: 'hd.pdf' },
    })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(apiPatch).toHaveBeenCalledTimes(2))
    expect(apiPatch.mock.calls[0]).toEqual([`${BASE}/docs/3`, { description: 'Mô tả mới' }])
    expect(apiPatch.mock.calls[1]).toEqual([`${BASE}/docs/3`, { file_note: 'hd.pdf' }])
  })

  //  Lỗi rà soát H2: ✓ đi đường mutation KHÁC ô sửa — trước đây không xếp hàng chung.
  it('queues the done tick behind a pending inline edit', async () => {
    let releaseFirst: (value: SurveyRequestReport) => void = () => {}
    apiPatch
      .mockReset()
      .mockImplementationOnce(
        () => new Promise<SurveyRequestReport>((resolve) => (releaseFirst = resolve)),
      )
      .mockResolvedValue(REPORT)
    renderCard()
    await openCard()
    fireEvent.click(screen.getByRole('checkbox', { name: 'Hồ sơ "Hợp đồng nắp" bắt buộc' }))
    fireEvent.click(screen.getByRole('button', { name: 'Đánh dấu hoàn thành "Giấy phép nhập khẩu"' }))
    await waitFor(() => expect(apiPatch).toHaveBeenCalledTimes(1))
    await new Promise((resolve) => setTimeout(resolve, 20))
    expect(apiPatch).toHaveBeenCalledTimes(1)
    releaseFirst(REPORT)
    await waitFor(() => expect(apiPatch).toHaveBeenCalledTimes(2))
    expect(apiPatch.mock.calls[1]).toEqual([`${BASE}/docs/1`, { status: 3 }])
  })

  //  Lỗi rà soát H3: ô vừa lưu nhảy về giá trị cũ tới khi máy chủ trả lời → người dùng
  //  tưởng mất, gõ lại / bấm lại lần nữa.
  it('shows the new value immediately while the save is still in flight', async () => {
    apiPatch.mockReset().mockImplementation(() => new Promise(() => {}))
    renderCard()
    await openCard()
    const checkbox = screen.getByRole('checkbox', { name: 'Hồ sơ "Hợp đồng nắp" bắt buộc' })
    fireEvent.click(checkbox)
    await waitFor(() => expect(checkbox).toBeChecked())
  })

  it('reopens the cell with the typed text when the save fails, and rolls the cache back', async () => {
    apiPatch.mockReset().mockRejectedValue(new Error('mất mạng'))
    renderCard()
    await openCard()
    fireEvent.click(screen.getByRole('button', { name: /^Sửa kết quả hồ sơ "Hợp đồng nắp"/ }))
    const input = screen.getByRole('textbox', { name: 'kết quả hồ sơ "Hợp đồng nắp"' })
    fireEvent.change(input, { target: { value: 'Bốn nghìn ký tự quý giá' } })
    fireEvent.keyDown(input, { key: 'Enter' })
    expect(
      await screen.findByRole('textbox', { name: 'kết quả hồ sơ "Hợp đồng nắp"' }),
    ).toHaveValue('Bốn nghìn ký tự quý giá')
  })

  it('opens in the phase view on a narrow screen, where a 2100px table is unusable', async () => {
    const original = window.matchMedia
    window.matchMedia = ((query: string) =>
      ({ ...original(query), matches: query === '(max-width: 1023px)' }) as MediaQueryList)
    try {
      renderCard()
      fireEvent.click(await screen.findByRole('button', { name: /Báo cáo thực hiện/ }))
      expect(await screen.findByRole('button', { name: 'Xem tổng' })).toHaveAttribute(
        'aria-pressed',
        'true',
      )
    } finally {
      window.matchMedia = original
    }
  })
})
