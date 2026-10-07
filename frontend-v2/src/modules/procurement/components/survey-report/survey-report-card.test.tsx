// duoc-CR-611 — khối Báo cáo thực hiện, dạng xem THEO DÒNG HÀNG: xóa nhiều hồ sơ (chọn tay) và
// xóa cả cụm (một dòng hàng / một giai đoạn). Kiểm ĐÚNG danh sách id gửi lên backend — gửi thừa
// một id là xóa nhầm hồ sơ của dòng hàng khác, không có bước nào phía sau bắt lại.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { SurveyReportDoc, SurveyRequestReport } from '../../types/survey-request-report'
import { SurveyReportCard } from './survey-report-card'

const apiGet = vi.fn()
const apiPost = vi.fn()
vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: (...args: unknown[]) => apiPost(...args),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}))
vi.mock('@/core/auth/use-auth', () => ({ useAuth: () => ({ user: { employee_id: 1 } }) }))
const confirmMock = vi.fn()
vi.mock('@/shared/ui/confirm-dialog', () => ({
  confirm: (...args: unknown[]) => confirmMock(...args),
}))

const PHASE_LEGAL = 10
const PHASE_ORDER = 20
const ITEM_CAP = 5
const ITEM_VITAMIN = 6

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

const REPORT: SurveyRequestReport = {
  items: [
    { id: ITEM_CAP, name: 'Nắp 50 75ml', line_id: 0, sort_order: 0 },
    { id: ITEM_VITAMIN, name: 'Vitamin B1', line_id: 0, sort_order: 1 },
  ],
  phases: [
    { id: PHASE_LEGAL, name: 'Pháp lý & Giấy phép', location: '', sort_order: 0 },
    { id: PHASE_ORDER, name: 'Đặt hàng & Hợp đồng', location: '', sort_order: 1 },
  ],
  docs: [
    makeDoc(1, PHASE_LEGAL, ITEM_CAP, 'Giấy phép nhập khẩu'),
    makeDoc(2, PHASE_LEGAL, ITEM_CAP, 'Giấy CN lưu hành'),
    makeDoc(3, PHASE_ORDER, ITEM_CAP, 'Hợp đồng nắp'),
    //  Hồ sơ của dòng hàng KHÁC trong cùng giai đoạn — không được lọt vào lượt xóa của dòng Nắp.
    makeDoc(4, PHASE_LEGAL, ITEM_VITAMIN, 'Giấy phép vitamin'),
    //  Hồ sơ CHUNG.
    makeDoc(5, PHASE_LEGAL, 0, 'Hồ sơ chung'),
  ],
  restorable: false,
  restorable_audit_id: 0,
}

function renderCard(canEdit = true) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <SurveyReportCard ownerId={7} canEdit={canEdit} />
    </QueryClientProvider>,
  )
}

/** Mở khối, chuyển dạng xem theo dòng hàng (đọc từ localStorage), sổ dòng «Nắp». */
async function openCapRow() {
  fireEvent.click(await screen.findByRole('button', { name: /Báo cáo thực hiện/ }))
  fireEvent.click(await screen.findByText('Nắp 50 75ml'))
  await screen.findByText('Hợp đồng nắp')
}

function lastBulkDeleteIds(): number[] {
  const call = apiPost.mock.calls.find(([url]) => String(url).endsWith('/docs/bulk-delete'))
  expect(call).toBeDefined()
  return [...(call?.[1] as { doc_ids: number[] }).doc_ids].sort((a, b) => a - b)
}

describe('SurveyReportCard — delete many / delete a whole cluster (by-line view)', () => {
  beforeEach(() => {
    localStorage.clear()
    localStorage.setItem('erp.survey-report.view', 'item')
    apiGet.mockReset().mockResolvedValue(REPORT)
    apiPost.mockReset().mockResolvedValue({ ...REPORT, docs: [] })
    confirmMock.mockReset().mockResolvedValue(true)
  })

  it('deletes every doc of one line row and nothing from other rows or the common row', async () => {
    renderCard()
    await openCapRow()
    fireEvent.click(screen.getByRole('button', { name: 'Xóa cả cụm hồ sơ của "Nắp 50 75ml"' }))
    await waitFor(() => expect(apiPost).toHaveBeenCalled())
    expect(apiPost.mock.calls[0][0]).toBe('/api/execution-report/survey_request/7/docs/bulk-delete')
    expect(lastBulkDeleteIds()).toEqual([1, 2, 3])
  })

  it('deletes only the docs of one phase inside the opened line row', async () => {
    renderCard()
    await openCapRow()
    fireEvent.click(
      screen.getAllByRole('button', { name: 'Xóa cả cụm hồ sơ của giai đoạn "Pháp lý & Giấy phép"' })[0],
    )
    await waitFor(() => expect(apiPost).toHaveBeenCalled())
    //  Doc 4 (Vitamin) và doc 5 (Chung) cùng giai đoạn nhưng khác dòng → không được xóa.
    expect(lastBulkDeleteIds()).toEqual([1, 2])
  })

  it('sends exactly the ticked docs and leaves selection mode after deleting', async () => {
    renderCard()
    await openCapRow()
    fireEvent.click(screen.getByRole('button', { name: /Chọn nhiều/ }))
    const deleteButton = screen.getByRole('button', { name: /Xóa đã chọn/ })
    expect(deleteButton).toBeDisabled()

    fireEvent.click(screen.getByRole('checkbox', { name: 'Chọn hồ sơ "Giấy phép nhập khẩu"' }))
    fireEvent.click(screen.getByRole('checkbox', { name: 'Chọn hồ sơ "Hợp đồng nắp"' }))
    //  Tick rồi bỏ tick: không được còn trong danh sách gửi đi.
    fireEvent.click(screen.getByRole('checkbox', { name: 'Chọn hồ sơ "Giấy CN lưu hành"' }))
    fireEvent.click(screen.getByRole('checkbox', { name: 'Chọn hồ sơ "Giấy CN lưu hành"' }))
    expect(screen.getByText('Đã chọn 2/3')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Xóa đã chọn (2)' }))
    await waitFor(() => expect(apiPost).toHaveBeenCalled())
    expect(lastBulkDeleteIds()).toEqual([1, 3])
    await waitFor(() => expect(screen.queryByRole('button', { name: /Xóa đã chọn/ })).toBeNull())
  })

  it('select-all picks only the docs of this row, and unticking it clears the selection', async () => {
    renderCard()
    await openCapRow()
    fireEvent.click(screen.getByRole('button', { name: /Chọn nhiều/ }))
    const selectAll = screen.getByRole('checkbox', { name: 'Chọn tất cả hồ sơ của dòng hàng này' })
    fireEvent.click(selectAll)
    expect(screen.getByText('Đã chọn 3/3')).toBeInTheDocument()
    fireEvent.click(selectAll)
    expect(screen.getByText('Đã chọn 0/3')).toBeInTheDocument()
    fireEvent.click(selectAll)
    fireEvent.click(screen.getByRole('button', { name: 'Xóa đã chọn (3)' }))
    await waitFor(() => expect(apiPost).toHaveBeenCalled())
    expect(lastBulkDeleteIds()).toEqual([1, 2, 3])
  })

  it('does not call the API when the confirm dialog is cancelled, and keeps the selection', async () => {
    confirmMock.mockResolvedValue(false)
    renderCard()
    await openCapRow()
    fireEvent.click(screen.getByRole('button', { name: /Chọn nhiều/ }))
    fireEvent.click(screen.getByRole('checkbox', { name: 'Chọn hồ sơ "Hợp đồng nắp"' }))
    fireEvent.click(screen.getByRole('button', { name: 'Xóa đã chọn (1)' }))
    await waitFor(() => expect(confirmMock).toHaveBeenCalled())
    expect(apiPost).not.toHaveBeenCalled()
    expect(screen.getByText('Đã chọn 1/3')).toBeInTheDocument()
  })

  it('names the count in the confirm dialog so the user knows how much is going', async () => {
    renderCard()
    await openCapRow()
    fireEvent.click(screen.getByRole('button', { name: 'Xóa cả cụm hồ sơ của "Nắp 50 75ml"' }))
    await waitFor(() => expect(confirmMock).toHaveBeenCalled())
    const options = confirmMock.mock.calls[0][0] as { message: string; confirmLabel: string }
    expect(options.confirmLabel).toBe('Xóa 3 hồ sơ')
    expect(options.message).toContain('"Nắp 50 75ml"')
  })

  it('shows no cluster delete or select-many controls to a read-only user', async () => {
    renderCard(false)
    await openCapRow()
    expect(screen.queryByRole('button', { name: /Xóa cả cụm/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Chọn nhiều/ })).toBeNull()
  })

  it('hides the cluster button on a line row that has no docs', async () => {
    apiGet.mockResolvedValue({ ...REPORT, docs: REPORT.docs.filter((doc) => doc.item_id !== ITEM_VITAMIN) })
    renderCard()
    fireEvent.click(await screen.findByRole('button', { name: /Báo cáo thực hiện/ }))
    const row = (await screen.findByText('Vitamin B1')).closest('tr')
    expect(row).not.toBeNull()
    expect(within(row as HTMLElement).queryByRole('button', { name: /Xóa cả cụm/ })).toBeNull()
  })
})

const EMPTY_REPORT: SurveyRequestReport = {
  items: [],
  phases: [],
  docs: [],
  restorable: false,
  restorable_audit_id: 0,
}

const FIRST_DOC_OPTIONS = {
  lines: [
    { line_id: 101, name: 'Nắp 50 75ml' },
    { line_id: 102, name: 'Vitamin B1' },
  ],
  phases: [
    { order: 0, name: 'Pháp lý & Giấy phép', location: '' },
    { order: 1, name: 'Đặt hàng & Hợp đồng', location: '' },
  ],
}

/** Ô chọn Radix: mở bằng phím (jsdom không có pointer thật) rồi bấm đúng lựa chọn. */
async function pickOption(trigger: HTMLElement, optionName: string) {
  trigger.focus()
  fireEvent.keyDown(trigger, { key: 'Enter' })
  fireEvent.click(await screen.findByRole('option', { name: optionName }))
}

describe('SurveyReportCard — first doc on an empty report (duoc-CR-611)', () => {
  beforeEach(() => {
    localStorage.clear()
    apiGet.mockReset().mockImplementation((url: string) =>
      Promise.resolve(url.endsWith('/first-doc-options') ? FIRST_DOC_OPTIONS : EMPTY_REPORT),
    )
    apiPost.mockReset()
    confirmMock.mockReset().mockResolvedValue(true)
  })

  it('posts the chosen line, phase and trimmed title, then shows the doc under its line row', async () => {
    const created: SurveyRequestReport = {
      ...REPORT,
      items: [{ id: 55, name: 'Vitamin B1', line_id: 102, sort_order: 1 }],
      docs: [makeDoc(9, PHASE_ORDER, 55, 'Giấy phép vitamin mới')],
    }
    apiPost.mockResolvedValue(created)
    renderCard()
    fireEvent.click(await screen.findByRole('button', { name: /Thêm hồ sơ/ }))

    const dialog = await screen.findByRole('dialog')
    await waitFor(() =>
      expect(within(dialog).getByRole('combobox', { name: 'Dòng hàng' })).toBeEnabled(),
    )
    await pickOption(within(dialog).getByRole('combobox', { name: 'Dòng hàng' }), 'Vitamin B1')
    await pickOption(
      within(dialog).getByRole('combobox', { name: 'Giai đoạn' }),
      '2. Đặt hàng & Hợp đồng',
    )
    fireEvent.change(within(dialog).getByLabelText(/Tên hồ sơ/), {
      target: { value: '  Giấy phép vitamin mới  ' },
    })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Thêm hồ sơ' }))

    await waitFor(() => expect(apiPost).toHaveBeenCalled())
    expect(apiPost).toHaveBeenCalledWith('/api/execution-report/survey_request/7/first-doc', {
      title: 'Giấy phép vitamin mới',
      line_id: 102,
      phase_order: 1,
    })
    //  Khối chuyển sang dạng theo dòng hàng và SỔ đúng dòng của hồ sơ vừa thêm.
    expect(await screen.findByText('Giấy phép vitamin mới')).toBeInTheDocument()
    expect(localStorage.getItem('erp.survey-report.view')).toBe('item')
  })

  it('defaults to the common row and the first phase when the user only types a title', async () => {
    apiPost.mockResolvedValue({ ...REPORT, docs: [makeDoc(9, PHASE_LEGAL, 0, 'RFQ')] })
    renderCard()
    fireEvent.click(await screen.findByRole('button', { name: /Thêm hồ sơ/ }))
    const dialog = await screen.findByRole('dialog')
    fireEvent.change(within(dialog).getByLabelText(/Tên hồ sơ/), { target: { value: 'RFQ' } })
    await waitFor(() =>
      expect(within(dialog).getByRole('button', { name: 'Thêm hồ sơ' })).toBeEnabled(),
    )
    //  Enter trong ô tên = lưu (không submit form cha).
    fireEvent.keyDown(within(dialog).getByLabelText(/Tên hồ sơ/), { key: 'Enter' })
    await waitFor(() => expect(apiPost).toHaveBeenCalled())
    expect(apiPost.mock.calls[0][1]).toEqual({ title: 'RFQ', line_id: 0, phase_order: 0 })
  })

  it('refuses a blank or whitespace-only title without calling the API', async () => {
    renderCard()
    fireEvent.click(await screen.findByRole('button', { name: /Thêm hồ sơ/ }))
    const dialog = await screen.findByRole('dialog')
    fireEvent.change(within(dialog).getByLabelText(/Tên hồ sơ/), { target: { value: '   ' } })
    await waitFor(() =>
      expect(within(dialog).getByRole('button', { name: 'Thêm hồ sơ' })).toBeEnabled(),
    )
    fireEvent.click(within(dialog).getByRole('button', { name: 'Thêm hồ sơ' }))
    await new Promise((resolve) => setTimeout(resolve, 0))
    expect(apiPost).not.toHaveBeenCalled()
  })

  it('does not fetch the line options until the dialog is opened', async () => {
    renderCard()
    await screen.findByRole('button', { name: /Thêm hồ sơ/ })
    expect(apiGet.mock.calls.some(([url]) => String(url).endsWith('/first-doc-options'))).toBe(false)
  })

  it('keeps the dialog usable with only the common row when the document has no lines', async () => {
    apiGet.mockImplementation((url: string) =>
      Promise.resolve(
        url.endsWith('/first-doc-options') ? { ...FIRST_DOC_OPTIONS, lines: [] } : EMPTY_REPORT,
      ),
    )
    renderCard()
    fireEvent.click(await screen.findByRole('button', { name: /Thêm hồ sơ/ }))
    const dialog = await screen.findByRole('dialog')
    expect(await within(dialog).findByText(/chưa có dòng hàng nào/)).toBeInTheDocument()
  })
})
