// duoc-CR-614 — «Khởi tạo báo cáo mẫu» có chọn mẫu. Chạy qua NGUYÊN `SurveyReportCard` (chỉ giả
// tầng `@/core/api`): gửi nhầm mã mẫu là khối dựng sai cả bộ hồ sơ, và đại ca muốn khởi tạo xong
// là thấy ngay dạng Bảng để sửa.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type {
  ReportTemplateOption,
  SurveyReportDoc,
  SurveyRequestReport,
} from '../../types/survey-request-report'
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
vi.mock('@/shared/ui/confirm-dialog', () => ({ confirm: vi.fn().mockResolvedValue(true) }))

const BASE = '/api/execution-report/survey_request/7'

const EMPTY: SurveyRequestReport = {
  items: [],
  phases: [],
  docs: [],
  restorable: false,
  restorable_audit_id: 0,
}

const TEMPLATES: ReportTemplateOption[] = [
  { id: 1, name: 'Mẫu chung hồ sơ nhập khẩu', description: '5 giai đoạn', phase_count: 5, doc_count: 19 },
  {
    id: 2,
    name: 'Tiến độ kế hoạch công việc nhập khẩu',
    description: '21 việc',
    phase_count: 1,
    doc_count: 21,
  },
]

const doc: SurveyReportDoc = {
  id: 1,
  phase_id: 9,
  item_id: 0,
  title: 'Tìm NCC nước ngoài',
  description: 'Thời gian xử lý: 1 ngày',
  required: true,
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
  sort_order: 0,
}
const PLAN_REPORT: SurveyRequestReport = {
  ...EMPTY,
  phases: [{ id: 9, name: 'Kế hoạch công việc nhập khẩu', location: '', sort_order: 0 }],
  docs: [doc],
}

function mockApi(templates: () => Promise<unknown>) {
  apiGet.mockReset().mockImplementation((url: string) => {
    if (url.endsWith('/templates')) return templates()
    if (url.startsWith('/api/employees')) return Promise.resolve({ items: [], total: 0 })
    return Promise.resolve(EMPTY)
  })
}

function renderCard() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <SurveyReportCard ownerId={7} canEdit />
    </QueryClientProvider>,
  )
}

async function openInitDialog() {
  fireEvent.click(await screen.findByRole('button', { name: /Khởi tạo báo cáo mẫu/ }))
  return screen.findByRole('dialog')
}

describe('SurveyReportCard — pick a template when initialising', () => {
  beforeEach(() => {
    localStorage.clear()
    mockApi(() => Promise.resolve(TEMPLATES))
    apiPost.mockReset().mockResolvedValue(PLAN_REPORT)
  })

  it('does not initialise until a template is confirmed in the dialog', async () => {
    renderCard()
    const dialog = await openInitDialog()
    expect(apiPost).not.toHaveBeenCalled()
    fireEvent.click(within(dialog).getByRole('button', { name: 'Hủy' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(apiPost).not.toHaveBeenCalled()
  })

  it('defaults to the first template, the same as the old one-click button', async () => {
    renderCard()
    const dialog = await openInitDialog()
    expect(await within(dialog).findByRole('radio', { name: /Mẫu chung hồ sơ nhập khẩu/ })).toBeChecked()
    fireEvent.click(within(dialog).getByRole('button', { name: 'Khởi tạo' }))
    await waitFor(() => expect(apiPost).toHaveBeenCalledWith(`${BASE}/init`, { template: 1 }))
  })

  it('sends the picked import-plan template and lands on the editable table view', async () => {
    //  Người dùng từng chọn «Theo dòng hàng» — khởi tạo xong vẫn phải về Bảng.
    localStorage.setItem('erp.survey-report.view', 'item')
    renderCard()
    const dialog = await openInitDialog()
    fireEvent.click(
      await within(dialog).findByRole('radio', { name: /Tiến độ kế hoạch công việc nhập khẩu/ }),
    )
    fireEvent.click(within(dialog).getByRole('button', { name: 'Khởi tạo' }))
    await waitFor(() => expect(apiPost).toHaveBeenCalledWith(`${BASE}/init`, { template: 2 }))
    expect(apiPost).toHaveBeenCalledTimes(1)
    expect(await screen.findByRole('button', { name: 'Bảng' })).toHaveAttribute('aria-pressed', 'true')
    expect(localStorage.getItem('erp.survey-report.view')).toBe('table')
    expect(await screen.findByRole('table')).toBeInTheDocument()
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('shows the counts so users can tell the two templates apart', async () => {
    renderCard()
    const dialog = await openInitDialog()
    expect(await within(dialog).findByText(/1 giai đoạn · 21 hồ sơ/)).toBeInTheDocument()
    expect(within(dialog).getByText(/5 giai đoạn · 19 hồ sơ/)).toBeInTheDocument()
  })

  it('says so and blocks initialising when the template list fails to load', async () => {
    mockApi(() => Promise.reject(new Error('mất mạng')))
    renderCard()
    const dialog = await openInitDialog()
    expect(await within(dialog).findByText(/Không tải được danh sách mẫu/)).toBeInTheDocument()
    expect(within(dialog).getByRole('button', { name: 'Khởi tạo' })).toBeDisabled()
  })

  it('a fast double click on Khởi tạo sends one request only', async () => {
    let release: (value: SurveyRequestReport) => void = () => {}
    apiPost.mockReset().mockImplementation(
      () => new Promise<SurveyRequestReport>((resolve) => (release = resolve)),
    )
    renderCard()
    const dialog = await openInitDialog()
    await within(dialog).findByRole('radio', { name: /Mẫu chung/ })
    const confirm = within(dialog).getByRole('button', { name: 'Khởi tạo' })
    fireEvent.click(confirm)
    fireEvent.click(confirm)
    await waitFor(() => expect(apiPost).toHaveBeenCalledTimes(1))
    release(PLAN_REPORT)
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(apiPost).toHaveBeenCalledTimes(1)
  })
})
