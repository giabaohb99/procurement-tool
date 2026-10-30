import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { JOB_RUN_STATUS, type JobItem, type JobListResult, type JobRunListResult } from '../api/job-run-api'
import { BackgroundJobListPage } from './background-job-list-page'

/**
 * Màn Việc chạy ngầm (bao-CR-703).
 *
 * Chỗ dễ lủng:
 * - Việc CHƯA chạy lần nào (`last_run = null`) phải nói rõ "Chưa chạy", không vỡ màn, không in 0 ms.
 * - Lọc "chưa chạy lần nào" là `status=0` — số 0 rất dễ bị coi là "không lọc".
 * - Mã việc có dấu chấm (tên task Celery) — đường lịch sử phải mã hóa, và chỉ gọi khi đã mở một việc.
 * - Đổi sang việc khác không được hiện lịch sử của việc cũ.
 * - Không có nút chạy tay đợt này.
 */

const apiGet = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: vi.fn(),
  apiPut: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}))

function job(over: Partial<JobItem> = {}): JobItem {
  return {
    code: 'backup.nightly',
    name: 'Sao lưu CSDL',
    purpose: 'Chép toàn bộ cơ sở dữ liệu lên kho lưu trữ mỗi đêm.',
    group: 'backup',
    group_label: 'Sao lưu',
    schedule_label: '02:45 mỗi đêm',
    enabled: true,
    next_run_at: '2026-10-31T02:45:00',
    last_run: {
      id: 91,
      job_code: 'backup.nightly',
      started_at: '2026-10-30T02:45:00',
      finished_at: '2026-10-30T02:49:05',
      duration_ms: 245_000,
      status: JOB_RUN_STATUS.SUCCESS,
      status_label: 'Thành công',
      summary: 'Bản sao 1,2 GB',
      error: '',
    },
    avg_duration_ms_7d: 240_000,
    runs_7d: 7,
    failed_7d: 0,
    ...over,
  }
}

const STATUSES = [
  { code: 1, label: 'Đang chạy' },
  { code: 2, label: 'Thành công' },
  { code: 3, label: 'Lỗi' },
  { code: 4, label: 'Bỏ qua' },
]

function list(items: JobItem[]): JobListResult {
  return { items, groups: [{ code: 'backup', label: 'Sao lưu' }, { code: 'customs', label: 'Hải quan' }], statuses: STATUSES }
}

function runs(code: string, summary: string): JobRunListResult {
  return {
    items: [
      {
        id: code === 'customs.cleanup_row_logs' ? 501 : 401,
        job_code: code,
        started_at: '2026-10-30T03:00:00',
        finished_at: '2026-10-30T03:00:02',
        duration_ms: 2100,
        status: JOB_RUN_STATUS.FAILED,
        status_label: 'Lỗi',
        summary,
        error: 'OperationalError: Lost connection to MySQL server',
      },
    ],
    total: 1,
    page: 1,
    page_size: 20,
  }
}

const customs = job({
  code: 'customs.cleanup_row_logs',
  name: 'Dọn nhật ký dòng hải quan',
  purpose: 'Xóa nhật ký dòng cũ hơn 90 ngày.',
  group: 'customs',
  group_label: 'Hải quan',
  schedule_label: 'ngày 1 và 16 lúc 03:30',
  last_run: null,
  avg_duration_ms_7d: null,
  runs_7d: 0,
  failed_7d: 0,
})

function mockServer(items: JobItem[] = [job(), customs]) {
  apiGet.mockImplementation((url: string) => {
    if (url === '/api/system/jobs') return Promise.resolve(list(items))
    if (url === '/api/system/jobs/backup.nightly/runs') return Promise.resolve(runs('backup.nightly', 'Lượt sao lưu'))
    if (url === '/api/system/jobs/customs.cleanup_row_logs/runs')
      return Promise.resolve(runs('customs.cleanup_row_logs', 'Lượt dọn hải quan'))
    return Promise.resolve(null)
  })
}

function renderPage(path = '/system/background-jobs') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[path]}>
        <BackgroundJobListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function listCalls() {
  return apiGet.mock.calls.filter(([url]) => url === '/api/system/jobs')
}

function runCalls() {
  return apiGet.mock.calls.filter(([url]) => String(url).endsWith('/runs'))
}

beforeEach(() => {
  apiGet.mockReset()
})

describe('BackgroundJobListPage', () => {
  it('lists each job with its purpose, readable schedule, last result and durations, without opening any history', async () => {
    mockServer()
    renderPage()

    expect(await screen.findByText('Sao lưu CSDL')).toBeInTheDocument()
    expect(screen.getByText('Chép toàn bộ cơ sở dữ liệu lên kho lưu trữ mỗi đêm.')).toBeInTheDocument()
    expect(screen.getByText('02:45 mỗi đêm')).toBeInTheDocument()
    expect(screen.getByText('Thành công')).toBeInTheDocument()
    expect(screen.getByText('4 phút 05 giây')).toBeInTheDocument()
    expect(screen.getByText('4 phút 00 giây')).toBeInTheDocument()
    expect(screen.getByText('7 lần')).toBeInTheDocument()
    //  Mở màn KHÔNG tải lịch sử của việc nào.
    expect(runCalls()).toHaveLength(0)
  })

  it('says a job never ran instead of breaking or printing a zero duration', async () => {
    mockServer([customs])
    renderPage()

    expect(await screen.findByText('Dọn nhật ký dòng hải quan')).toBeInTheDocument()
    expect(screen.getAllByText('Chưa chạy').length).toBeGreaterThanOrEqual(1)
    expect(screen.queryByText(/0 ms/)).not.toBeInTheDocument()
  })

  it('marks a switched-off job and shows no next run for it', async () => {
    mockServer([job({ enabled: false })])
    renderPage()

    expect(await screen.findByText('Đang tắt')).toBeInTheDocument()
    expect(screen.queryByText(/31\/10\/2026/)).not.toBeInTheDocument()
  })

  it('sends status=0 for the never-ran filter instead of dropping it as "all"', async () => {
    mockServer()
    renderPage('/system/background-jobs?status=0')

    await screen.findByText('Sao lưu CSDL')
    expect(listCalls().at(-1)?.[1]).toEqual({ params: { group: undefined, status: 0, q: undefined } })
  })

  it('opens the run history of the clicked job through an encoded path, with the error text', async () => {
    mockServer()
    renderPage()

    await userEvent.click(await screen.findByText('Dọn nhật ký dòng hải quan'))
    const sheet = await screen.findByRole('dialog')
    expect(await within(sheet).findByText('Lượt dọn hải quan')).toBeInTheDocument()
    expect(within(sheet).getByText(/Lost connection to MySQL server/)).toBeInTheDocument()
    expect(within(sheet).getByText('2,1 giây')).toBeInTheDocument()
    expect(runCalls().at(-1)?.[0]).toBe('/api/system/jobs/customs.cleanup_row_logs/runs')
    expect(runCalls().at(-1)?.[1]).toEqual({ params: { status: undefined, page: 1, page_size: expect.any(Number) } })
  })

  it('opens straight on a job from a shared link and never shows another job’s history', async () => {
    mockServer()
    renderPage('/system/background-jobs?job=backup.nightly')

    const sheet = await screen.findByRole('dialog')
    expect(await within(sheet).findByText('Lượt sao lưu')).toBeInTheDocument()
    expect(within(sheet).queryByText('Lượt dọn hải quan')).not.toBeInTheDocument()
  })

  it('offers no button to run a job by hand', async () => {
    mockServer()
    renderPage('/system/background-jobs?job=backup.nightly')

    const sheet = await screen.findByRole('dialog')
    await within(sheet).findByText('Lượt sao lưu')
    expect(screen.queryByRole('button', { name: /Chạy (ngay|lại|tay)/ })).not.toBeInTheDocument()
  })

  it('tells an empty filter result apart from a server with no jobs', async () => {
    mockServer([])
    renderPage('/system/background-jobs?group=customs')
    expect(await screen.findByText('Không có việc nào khớp bộ lọc.')).toBeInTheDocument()
  })

  it('sends the typed search to the server after the pause', async () => {
    mockServer()
    renderPage()
    await screen.findByText('Sao lưu CSDL')

    await userEvent.type(screen.getByRole('textbox', { name: 'Tìm việc' }), '  hải quan ')
    await waitFor(() => expect(listCalls().at(-1)?.[1]).toEqual({ params: { group: undefined, status: undefined, q: 'hải quan' } }))
  })
})
