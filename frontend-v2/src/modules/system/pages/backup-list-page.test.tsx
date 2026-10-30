import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { DbBackupListResponse } from '../types/backup'
import { BackupListPage } from './backup-list-page'

/**
 * Màn Sao lưu — lựa chọn "DB ERP | DB bot (agent_hub)" (ai-CR-139).
 *
 * Chỗ dễ lủng: DB bot phải gọi qua proxy `/api/agent-hub/backups*`, không được rơi về `/api/backups` của ERP; DB bot
 * KHÔNG có nút xóa bản và KHÔNG có đường khôi phục thật — chỉ "Khôi phục thử". Bot chạy chung DB ERP thì phải nói rõ là
 * bản ERP đã gồm bảng bot, và khóa nút chạy.
 */

const apiGet = vi.fn()
const apiPost = vi.fn()
const apiDelete = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: (...args: unknown[]) => apiPost(...args),
  apiPut: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: (...args: unknown[]) => apiDelete(...args),
}))

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

const can = vi.fn((_entity: string, _action: string) => true)
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string, action: string) => can(entity, action), canAccess: () => true }),
}))

const confirmMock = vi.fn()
vi.mock('@/shared/ui/confirm-dialog', () => ({
  confirm: (...args: unknown[]) => confirmMock(...args),
}))

function list(over: Partial<DbBackupListResponse> = {}): DbBackupListResponse {
  return {
    total: 1,
    keep: 30,
    items: [
      {
        id: 7,
        source: 'auto',
        status: 'success',
        file_key: 'dev/backup/x.sql.gz',
        size_bytes: 2048,
        message: '',
        started_at: '2026-10-09T01:20:00',
        finished_at: '2026-10-09T01:20:30',
        created_at: '2026-10-09T01:20:00',
        created_by: 0,
        created_by_name: '',
      },
    ],
    ...over,
  }
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <BackupListPage />
    </QueryClientProvider>,
  )
}

describe('BackupListPage — DB bot', () => {
  beforeEach(() => {
    apiGet.mockReset()
    apiPost.mockReset()
    apiDelete.mockReset()
  })

  it('switches to the bot database through the agent-hub proxy and offers no delete', async () => {
    apiGet.mockImplementation((url: string) =>
      Promise.resolve(url.startsWith('/api/agent-hub') ? list({ enabled: true, db_name: 'agent_hub' }) : list()),
    )
    apiPost.mockResolvedValue(null)
    renderPage()
    expect(await screen.findByTitle('Xóa bản sao lưu')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('radio', { name: /DB bot/ }))
    await waitFor(() => expect(apiGet).toHaveBeenCalledWith('/api/agent-hub/backups', expect.anything()))
    expect(await screen.findByText(/Sao lưu DB của bot \(agent_hub\)/)).toBeInTheDocument()
    expect(screen.queryByTitle('Xóa bản sao lưu')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Khôi phục$/ })).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: /Khôi phục thử/ }))
    await waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/agent-hub/backups/restore-test'))
    await userEvent.click(screen.getByRole('button', { name: /Sao lưu ngay/ }))
    await waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/agent-hub/backups/run'))
  })

  it('says the ERP backup already covers the bot when it shares the ERP database', async () => {
    apiGet.mockImplementation((url: string) =>
      Promise.resolve(url.startsWith('/api/agent-hub') ? list({ enabled: false, total: 0, items: [] }) : list()),
    )
    renderPage()
    await userEvent.click(await screen.findByRole('radio', { name: /DB bot/ }))
    expect(await screen.findByText(/Bot đang chạy chung DB ERP/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Sao lưu ngay/ })).toBeDisabled()
    expect(screen.getByRole('button', { name: /Khôi phục thử/ })).toBeDisabled()
  })
})

/**
 * kh-SL-nut-chap-nhan — nút *Chấp nhận cỡ mới* (máy chủ có từ bao-CR-656).
 *
 * CSDL thu nhỏ hợp lệ thì lượt sao lưu đánh dấu bản mới là đáng ngờ (`message` mở đầu
 * "Bỏ qua dọn bản cũ:") và ngừng dọn bản cũ. Nút gỡ dấu đó — hệ quả là lượt sau XÓA các
 * bản to cũ, nên chỉ người có `backup.delete` thấy và phải xác nhận trước.
 */
describe('BackupListPage — Chấp nhận cỡ mới', () => {
  const suspect = (over: Partial<DbBackupListResponse> = {}) =>
    list({
      items: [
        { ...list().items[0], id: 9, message: 'Bỏ qua dọn bản cũ: bản mới nhỏ hơn 50% bản trước (1,2 MB < 3,4 MB)' },
        list().items[0],
      ],
      ...over,
    })

  beforeEach(() => {
    apiGet.mockReset()
    apiPost.mockReset().mockResolvedValue({ accepted: 1 })
    confirmMock.mockReset().mockResolvedValue(true)
    can.mockImplementation(() => true)
  })

  it('stays hidden while no backup is flagged as suspicious', async () => {
    apiGet.mockResolvedValue(list())
    renderPage()
    await screen.findByTitle('Xóa bản sao lưu')
    expect(screen.queryByRole('button', { name: /Chấp nhận cỡ mới/ })).not.toBeInTheDocument()
  })

  it('does not treat a message that only CONTAINS the marker as flagged', async () => {
    //  Máy chủ so `startswith`; khớp lỏng ở đây là bày nút cho một bản không bị chặn,
    //  bấm vào ăn 400.
    apiGet.mockResolvedValue(
      list({ items: [{ ...list().items[0], message: 'Ghi chú: Bỏ qua dọn bản cũ: thử' }] }),
    )
    renderPage()
    await screen.findByTitle('Xóa bản sao lưu')
    expect(screen.queryByRole('button', { name: /Chấp nhận cỡ mới/ })).not.toBeInTheDocument()
  })

  it('asks first, says old big backups will be cleaned, then calls the ERP endpoint', async () => {
    apiGet.mockResolvedValue(suspect())
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: /Chấp nhận cỡ mới/ }))

    await waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/backups/accept-size'))
    const [options] = confirmMock.mock.calls[0] as [{ message: string }]
    expect(options.message).toMatch(/dọn/)
    expect(options.message).toMatch(/bản (sao lưu )?(to|lớn) cũ/)
  })

  it('does nothing when the confirmation is cancelled', async () => {
    confirmMock.mockResolvedValue(false)
    apiGet.mockResolvedValue(suspect())
    renderPage()
    await userEvent.click(await screen.findByRole('button', { name: /Chấp nhận cỡ mới/ }))

    await waitFor(() => expect(confirmMock).toHaveBeenCalled())
    expect(apiPost).not.toHaveBeenCalledWith('/api/backups/accept-size')
  })

  it('is hidden without backup.delete — the consequence is deleting old backups', async () => {
    can.mockImplementation((_entity, action) => action !== 'delete')
    apiGet.mockResolvedValue(suspect())
    renderPage()
    await screen.findByText(/Bỏ qua dọn bản cũ/)
    expect(screen.queryByRole('button', { name: /Chấp nhận cỡ mới/ })).not.toBeInTheDocument()
  })

  it('goes through the agent-hub proxy for the bot database', async () => {
    apiGet.mockImplementation((url: string) =>
      Promise.resolve(url.startsWith('/api/agent-hub') ? suspect({ enabled: true }) : list()),
    )
    renderPage()
    await userEvent.click(await screen.findByRole('radio', { name: /DB bot/ }))
    await userEvent.click(await screen.findByRole('button', { name: /Chấp nhận cỡ mới/ }))

    await waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/agent-hub/backups/accept-size'))
    expect(apiPost).not.toHaveBeenCalledWith('/api/backups/accept-size')
  })

  it('sends ONE request on a double click', async () => {
    let finish: (value: unknown) => void = () => {}
    apiPost.mockImplementation(() => new Promise((resolve) => (finish = resolve)))
    apiGet.mockResolvedValue(suspect())
    renderPage()
    const button = await screen.findByRole('button', { name: /Chấp nhận cỡ mới/ })
    await userEvent.dblClick(button)

    await waitFor(() => expect(apiPost).toHaveBeenCalledTimes(1))
    finish({ accepted: 1 })
    await waitFor(() => expect(confirmMock).toHaveBeenCalledTimes(1))
  })

  it('stays usable after the server refuses — the error toast comes from http-client', async () => {
    //  Máy chủ trả 400 "Không có bản sao lưu nào đang bị đánh dấu đáng ngờ" khi người
    //  khác vừa chấp nhận trước; `http-client` toast đúng câu đó cho mọi lệnh ghi.
    apiPost.mockRejectedValue(new Error('400'))
    apiGet.mockResolvedValue(suspect())
    renderPage()
    const button = await screen.findByRole('button', { name: /Chấp nhận cỡ mới/ })
    await userEvent.click(button)

    await waitFor(() => expect(apiPost).toHaveBeenCalledTimes(1))
    await waitFor(() => expect(button).toBeEnabled())
  })
})
