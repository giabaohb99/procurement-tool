import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { DbBackupListResponse } from '../types/backup'
import { BackupListPage } from './backup-list-page'

/**
 * Màn Sao lưu — lựa chọn «DB ERP | DB bot (agent_hub)» (ai-CR-139).
 *
 * Chỗ dễ lủng: DB bot phải gọi qua proxy `/api/agent-hub/backups*`, không được rơi về `/api/backups` của ERP; DB bot
 * KHÔNG có nút xóa bản và KHÔNG có đường khôi phục thật — chỉ «Khôi phục thử». Bot chạy chung DB ERP thì phải nói rõ là
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

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAccess: () => true }),
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
