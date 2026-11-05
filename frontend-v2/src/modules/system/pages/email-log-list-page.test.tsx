import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { EmailLogItem, EmailLogListResult } from '../api/email-log-api'
import { EmailLogListPage } from './email-log-list-page'

/**
 * Màn Nhật ký email (bao-CR-721).
 *
 * Chỗ dễ lủng:
 * - Thẻ đếm phải lấy từ `/stats`, không tự đếm trang hiện tại.
 * - Bảng rỗng do LỌC phải nói khác bảng rỗng vì hệ chưa ghi gì.
 * - Nhãn trạng thái / loại thư do backend trả — không tự dịch `failed`.
 * - Lọc nhiều sự kiện: mỗi sự kiện một tham số `event=` riêng trên URL.
 * - Mở màn không gọi chi tiết (`/{id}`) khi chưa bấm dòng nào.
 */

const apiGet = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: vi.fn(),
  apiPut: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}))

function item(over: Partial<EmailLogItem> = {}): EmailLogItem {
  return {
    id: 1,
    event: 'dx_submitted',
    event_label: 'Gửi duyệt → Người duyệt',
    to_email: 'an@dego.vn',
    subject: 'YCĐX DX001 chờ bạn duyệt',
    status: 'sent',
    status_label: 'Đã gửi',
    error: '',
    sent_at: '2026-11-03T08:00:00',
    mailbox_id: null,
    from_email: 'erp@dego.vn',
    created_at: '2026-11-03T08:00:00',
    created_by: 0,
    resent_from_id: null,
    has_body: true,
    can_resend: true,
    resend_block_reason: '',
    ...over,
  }
}

const META = {
  events: [
    { code: 'dx_submitted', label: 'Gửi duyệt → Người duyệt' },
    { code: 'dd_completed', label: 'Hoàn thành → Người tạo' },
  ],
  statuses: [
    { code: 'failed', label: 'Lỗi' },
    { code: 'sent', label: 'Đã gửi' },
  ],
}
const STATS = { days: 7, total: 9, failed: 3, sent: 6, pending: 0, by_status: [] }

let listResult: EmailLogListResult

function mockApi() {
  apiGet.mockImplementation((url: string) => {
    if (url.startsWith('/api/email-logs/meta')) return Promise.resolve(META)
    if (url.startsWith('/api/email-logs/stats')) return Promise.resolve(STATS)
    if (/\/api\/email-logs\/\d+/.test(url)) return Promise.resolve(item({ id: 2, error: 'SMTP 550 full error text' }))
    return Promise.resolve(listResult)
  })
}

function dung(initialEntry = '/system/email-logs') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <EmailLogListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  apiGet.mockReset()
  listResult = {
    total: 2,
    page: 1,
    page_size: 50,
    items: [
      item(),
      item({ id: 2, to_email: 'binh@dego.vn', status: 'failed', status_label: 'Lỗi', error: 'SMTP 550 mailbox unavailable' }),
    ],
  }
  mockApi()
})

describe('EmailLogListPage', () => {
  it('thẻ đếm lấy từ /stats, bảng in nhãn backend trả và câu lỗi rút gọn', async () => {
    dung()
    expect(await screen.findByText('binh@dego.vn')).toBeInTheDocument()
    expect(screen.getByText('Thư lỗi 7 ngày qua')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()          // từ /stats, không phải đếm 1 dòng lỗi trên trang
    expect(screen.getAllByText('Lỗi').length).toBeGreaterThan(0)
    expect(screen.getByText('SMTP 550 mailbox unavailable')).toBeInTheDocument()
    expect(screen.getAllByText('Gửi duyệt → Người duyệt').length).toBeGreaterThan(0)
    //  Mở màn không gọi chi tiết thư nào.
    const detailCalls = apiGet.mock.calls.filter(([url]) => /\/api\/email-logs\/\d+/.test(String(url)))
    expect(detailCalls).toHaveLength(0)
  })

  it('labels a resent row with "Gửi lại từ #id" in the table (bao-CR-727)', async () => {
    listResult = { total: 1, page: 1, page_size: 50, items: [item({ id: 5, resent_from_id: 2 })] }
    dung()
    expect(await screen.findByText('Gửi lại từ #2')).toBeInTheDocument()
  })

  it('bảng rỗng do lọc nói khác bảng rỗng vì chưa ghi gì', async () => {
    listResult = { total: 0, page: 1, page_size: 50, items: [] }
    dung()
    expect(await screen.findByText('Hệ chưa ghi thư nào.')).toBeInTheDocument()
  })

  it('lọc theo trạng thái từ URL và bảng rỗng do lọc', async () => {
    listResult = { total: 0, page: 1, page_size: 50, items: [] }
    dung('/system/email-logs?status=failed')
    expect(await screen.findByText('Không có thư nào khớp bộ lọc.')).toBeInTheDocument()
    await waitFor(() => {
      const listCalls = apiGet.mock.calls.map(([url]) => String(url)).filter((u) => u.startsWith('/api/email-logs?'))
      expect(listCalls.some((u) => u.includes('status=failed'))).toBe(true)
    })
  })

  it('gõ người nhận thì gửi `q=`; mỗi loại thư thêm một tham số `event=` riêng', async () => {
    const user = userEvent.setup()
    dung()
    await screen.findByText('binh@dego.vn')
    await user.type(screen.getByLabelText('Người nhận'), 'an@')
    await waitFor(() => {
      const urls = apiGet.mock.calls.map(([url]) => String(url))
      expect(urls.some((u) => u.includes('q=an%40'))).toBe(true)
    })
  })

  it('bấm dòng mới gọi chi tiết và ngăn in nguyên văn câu lỗi', async () => {
    const user = userEvent.setup()
    dung()
    await user.click(await screen.findByText('binh@dego.vn'))
    expect(await screen.findByText('SMTP 550 full error text')).toBeInTheDocument()
    const detailCalls = apiGet.mock.calls.filter(([url]) => /\/api\/email-logs\/2$/.test(String(url)))
    expect(detailCalls).toHaveLength(1)
  })
})
