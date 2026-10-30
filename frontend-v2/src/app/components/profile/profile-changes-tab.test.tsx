import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { toast } from 'sonner'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { BotChange, BotChangeDetail, UndoChangeResult } from '@/modules/system/api/bot-changes-api'
import { ProfileChangesTab } from './profile-changes-tab'

/**
 * Tab "Bot đã ghi gì" (ai-CR-185, phase 15.3).
 *
 * Chỗ dễ lủng:
 * 1. Người thường KHÔNG được gửi `all=1` — backend trả 403 và người ta ăn một toast lỗi ngay lúc mở tab
 *    dù chẳng bấm gì. Công tắc "Xem của mọi người" chỉ hiện khi có `agent_group.read`.
 * 2. Nút Hoàn tác phải TẮT đúng theo `can_undo` của backend và nói lý do; bật thì bấm → xác nhận → gọi
 *    undo đúng MỘT lần (bấm đúp không ra hai lượt), rồi làm tươi danh sách.
 * 3. Lỗi nghiệp vụ (409 phiếu đã đổi) phải hiện đúng câu trong phong bì, không phải câu chung.
 */

const apiGet = vi.fn()
const apiPost = vi.fn()

vi.mock('@/core/api', async () => {
  //  Dùng bản THẬT của hàm bóc lỗi để bài 409 kiểm đúng câu trong phong bì, không kiểm một bản giả.
  const envelope = await import('@/core/api/response-envelope')
  return {
    apiGet: (...args: unknown[]) => apiGet(...args),
    apiPost: (...args: unknown[]) => apiPost(...args),
    apiPut: vi.fn(),
    apiPatch: vi.fn(),
    apiDelete: vi.fn(),
    extractErrorMessage: envelope.extractErrorMessage,
  }
})

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

const confirmMock = vi.fn(() => Promise.resolve(true))
vi.mock('@/shared/ui/confirm-dialog', () => ({ confirm: () => confirmMock() }))

//  Khóa quyền đổi theo từng bài — mặc định là NGƯỜI THƯỜNG (không quản lý bot AI).
let isManager = false
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) => entity === 'agent_group' && action === 'read' && isManager,
    canAccess: () => true,
  }),
}))

function change(over: Partial<BotChange> = {}): BotChange {
  return {
    id: 11,
    //  Mốc UTC trần của backend → 09:30 giờ Việt Nam.
    when: '2026-10-13T02:30:00',
    user_id: 7,
    entity: 'leave_request',
    entity_label: 'Đơn nghỉ phép',
    entity_id: 5,
    doc_code: 'NP001',
    action: 2,
    action_label: 'Sửa',
    summary: 'Sửa Đơn nghỉ phép NP001: Đến ngày',
    source: 1,
    source_label: 'Telegram',
    undo_status: 0,
    undo_status_label: 'Chưa hoàn tác',
    undo_of: 0,
    can_undo: true,
    undo_reason: '',
    url: '/hr/leave-requests/5',
    ...over,
  }
}

const ROWS: BotChange[] = [
  change(),
  change({
    id: 12,
    doc_code: 'YCMH00123',
    entity: 'purchase_request',
    entity_label: 'Yêu cầu mua hàng',
    action: 1,
    action_label: 'Tạo',
    summary: 'Tạo yêu cầu mua hàng (YCMH) YCMH00123',
    undo_status: 2,
    undo_status_label: 'Bị chặn',
    can_undo: false,
    undo_reason: 'Phiếu đã gửi duyệt — rút / trả về bằng tay.',
    url: '/procurement/purchase-requests/9',
  }),
  change({
    id: 13,
    undo_of: 7,
    action: 2,
    action_label: 'Sửa',
    summary: 'Hoàn tác: Sửa Đơn nghỉ phép NP002: Lý do',
    can_undo: false,
    undo_reason: 'Dòng ghi việc hoàn tác, không hoàn tác lại.',
    url: '',
    doc_code: '',
  }),
]

const DETAIL: BotChangeDetail = {
  ...change(),
  before: { fields: { end_date: '2026-10-20' }, truncated: true },
  after: { fields: { end_date: '2026-10-22' } },
  undone_at: '',
  undone_by: 0,
}

function mockList(items: BotChange[] = ROWS) {
  apiGet.mockImplementation((url: string) =>
    Promise.resolve(url === '/api/assistant/changes' ? { items } : DETAIL),
  )
}

function renderTab() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ProfileChangesTab />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ProfileChangesTab', () => {
  beforeEach(() => {
    isManager = false
    apiGet.mockReset()
    apiPost.mockReset()
    confirmMock.mockClear()
    vi.mocked(toast.success).mockClear()
    vi.mocked(toast.error).mockClear()
    //  Bảng nhớ bố cục cột trong localStorage — sót lại giữa hai bài là cột ẩn/hiện lẫn nhau.
    localStorage.clear()
  })

  it('lists only my own changes by default, with the document linked to its v2 page', async () => {
    mockList()
    renderTab()
    expect(await screen.findByText('Sửa Đơn nghỉ phép NP001: Đến ngày')).toBeInTheDocument()
    //  Không có `all` trong tham số — người thường mà gửi `all=1` là 403.
    expect(apiGet).toHaveBeenCalledWith('/api/assistant/changes', { params: { limit: 50 } })
    expect(screen.getByRole('link', { name: 'NP001' })).toHaveAttribute('href', '/hr/leave-requests/5')
    //  dd/MM HH:mm theo giờ Việt Nam (mốc UTC trần 02:30 → 09:30); ba dòng mẫu cùng một mốc.
    expect(screen.getAllByText('13/10 09:30')).toHaveLength(3)
    expect(screen.getByText('Bị chặn')).toBeInTheDocument()
    //  Dòng ngược không hiện trạng thái hoàn tác mà trỏ về dòng gốc.
    expect(screen.getByText('Hoàn tác của #7')).toBeInTheDocument()
    //  Không có khóa quản lý → không có công tắc, kể cả ở dạng tắt.
    expect(screen.queryByRole('switch')).not.toBeInTheDocument()
  })

  it('disables Undo when the backend says so and shows the reason', async () => {
    mockList()
    renderTab()
    const blocked = await screen.findByRole('button', { name: 'Hoàn tác: Tạo yêu cầu mua hàng (YCMH) YCMH00123' })
    expect(blocked).toBeDisabled()
    expect(screen.getByTitle('Phiếu đã gửi duyệt — rút / trả về bằng tay.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Hoàn tác: Sửa Đơn nghỉ phép NP001: Đến ngày' })).toBeEnabled()
    //  Dòng ngược cũng tắt nút.
    expect(screen.getByRole('button', { name: /Hoàn tác: Hoàn tác: Sửa Đơn nghỉ phép NP002/ })).toBeDisabled()
  })

  it('undoes once after confirmation, even on a double click, then toasts and reloads the list', async () => {
    mockList()
    //  Giữ lời gọi undo ĐANG CHỜ trong lúc bấm đúp — mock trả ngay thì lượt đầu xong trước cú bấm thứ hai
    //  và bài này không còn kiểm được chốt chặn.
    let release: (v: UndoChangeResult) => void = () => {}
    apiPost.mockImplementation(() => new Promise<UndoChangeResult>((r) => (release = r)))
    renderTab()
    const button = await screen.findByRole('button', { name: 'Hoàn tác: Sửa Đơn nghỉ phép NP001: Đến ngày' })
    await userEvent.dblClick(button)
    release({
      id: 14,
      undo_of: 11,
      entity: 'leave_request',
      entity_label: 'Đơn nghỉ phép',
      doc_code: 'NP001',
      action: 2,
      action_label: 'Sửa',
      summary: 'Hoàn tác: Sửa Đơn nghỉ phép NP001: Đến ngày',
      url: '/hr/leave-requests/5',
    })
    await waitFor(() => expect(apiPost).toHaveBeenCalledTimes(1))
    expect(apiPost).toHaveBeenCalledWith('/api/assistant/changes/11/undo', undefined, { _silent: true })
    expect(confirmMock).toHaveBeenCalledTimes(1)
    await waitFor(() => expect(toast.success).toHaveBeenCalledWith('Hoàn tác: Sửa Đơn nghỉ phép NP001: Đến ngày'))
    //  Làm tươi danh sách: gọi lại cửa danh sách sau khi hoàn tác.
    await waitFor(() =>
      expect(apiGet.mock.calls.filter(([url]) => url === '/api/assistant/changes').length).toBeGreaterThanOrEqual(2),
    )
  })

  it('does nothing when the confirmation is cancelled', async () => {
    mockList()
    confirmMock.mockResolvedValueOnce(false)
    renderTab()
    await userEvent.click(await screen.findByRole('button', { name: 'Hoàn tác: Sửa Đơn nghỉ phép NP001: Đến ngày' }))
    expect(confirmMock).toHaveBeenCalledTimes(1)
    expect(apiPost).not.toHaveBeenCalled()
  })

  it('shows the envelope message when the undo is refused (409)', async () => {
    mockList()
    apiPost.mockRejectedValue({
      response: {
        status: 409,
        data: { success: false, error: { code: 'conflict', message: 'Phiếu đã bị sửa sau khi bot ghi — mở phiếu sửa tay.' } },
      },
    })
    renderTab()
    await userEvent.click(await screen.findByRole('button', { name: 'Hoàn tác: Sửa Đơn nghỉ phép NP001: Đến ngày' }))
    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith('Phiếu đã bị sửa sau khi bot ghi — mở phiếu sửa tay.'),
    )
    expect(toast.success).not.toHaveBeenCalled()
  })

  it('offers "everyone" only to bot managers and then asks for all=1 with a user column', async () => {
    isManager = true
    mockList()
    renderTab()
    const toggle = await screen.findByRole('switch', { name: 'Xem của mọi người' })
    expect(screen.queryByRole('columnheader', { name: /Người/ })).not.toBeInTheDocument()
    await userEvent.click(toggle)
    await waitFor(() =>
      expect(apiGet).toHaveBeenCalledWith('/api/assistant/changes', { params: { limit: 50, all: 1 } }),
    )
    expect(await screen.findByRole('columnheader', { name: /Người/ })).toBeInTheDocument()
    //  API chưa trả tên → hiện id.
    expect(screen.getAllByText('#7').length).toBeGreaterThan(0)
  })

  it('opens before / after snapshots when a row is clicked and flags truncation', async () => {
    mockList()
    renderTab()
    await userEvent.click(await screen.findByText('Sửa Đơn nghỉ phép NP001: Đến ngày'))
    await waitFor(() => expect(apiGet).toHaveBeenCalledWith('/api/assistant/changes/11'))
    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText('Trước')).toBeInTheDocument()
    expect(within(dialog).getByText('Sau')).toBeInTheDocument()
    expect(within(dialog).getByText('(đã cắt bớt)')).toBeInTheDocument()
    expect(within(dialog).getByText(/2026-10-22/)).toBeInTheDocument()
  })

  it('says plainly when the bot has written nothing for me', async () => {
    mockList([])
    renderTab()
    expect(await screen.findByText('Bot chưa ghi thay đổi nào cho bạn.')).toBeInTheDocument()
  })
})
