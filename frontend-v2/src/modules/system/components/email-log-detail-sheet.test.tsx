import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ConfirmDialogHost } from '@/shared/ui/confirm-dialog'

import type { EmailLogItem } from '../api/email-log-api'
import { EmailLogDetailSheet } from './email-log-detail-sheet'

/**
 * Nút Gửi lại trong ngăn chi tiết thư (bao-CR-727).
 *
 * Chỗ dễ lủng:
 * - Không có `audit.write` thì không hiện nút.
 * - Thư không gửi lại được (thư cũ, thư mật khẩu) thì nút TẮT và in lý do backend trả.
 * - Phải qua hộp xác nhận ghi rõ người nhận + tiêu đề; bấm Hủy thì không gọi API.
 * - Dòng gửi lại hiện nhãn "Gửi lại từ #id".
 */

const apiGet = vi.fn()
const apiPost = vi.fn()
let canWrite = true

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: (...args: unknown[]) => apiPost(...args),
  apiPut: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) => entity === 'audit' && (action === 'read' || canWrite),
    canAccess: () => true,
  }),
}))

vi.mock('sonner', () => ({ toast: { error: vi.fn(), success: vi.fn() } }))

function item(over: Partial<EmailLogItem> = {}): EmailLogItem {
  return {
    id: 7,
    event: 'dx_submitted',
    event_label: 'Gửi duyệt → Người duyệt',
    to_email: 'an@dego.vn',
    subject: 'YCĐX DX001 chờ bạn duyệt',
    status: 'failed',
    status_label: 'Lỗi',
    error: 'SMTP 550',
    sent_at: null,
    mailbox_id: null,
    from_email: '',
    created_at: '2026-11-04T08:00:00',
    created_by: 0,
    resent_from_id: null,
    has_body: true,
    can_resend: true,
    resend_block_reason: '',
    ...over,
  }
}

function build(row: EmailLogItem) {
  apiGet.mockResolvedValue(row)
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <EmailLogDetailSheet logId={row.id} onClose={() => {}} />
      <ConfirmDialogHost />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  apiGet.mockReset()
  apiPost.mockReset()
  apiPost.mockResolvedValue(item({ id: 8, resent_from_id: 7, status: 'pending' }))
  canWrite = true
})

describe('EmailLogDetailSheet resend', () => {
  it('asks for confirmation showing recipient and subject; cancel sends nothing, confirm calls /resend', async () => {
    const user = userEvent.setup()
    build(item())
    await user.click(await screen.findByRole('button', { name: /Gửi lại/ }))
    const dialog = await screen.findByRole('alertdialog')
    expect(dialog).toHaveTextContent('an@dego.vn')
    expect(dialog).toHaveTextContent('YCĐX DX001 chờ bạn duyệt')
    await user.click(screen.getByRole('button', { name: 'Hủy' }))
    expect(apiPost).not.toHaveBeenCalled()

    await user.click(screen.getByRole('button', { name: /Gửi lại/ }))
    const confirmButtons = await screen.findAllByRole('button', { name: 'Gửi lại' })
    await user.click(confirmButtons[confirmButtons.length - 1])
    await waitFor(() => expect(apiPost).toHaveBeenCalledWith('/api/email-logs/7/resend', {}))
  })

  it('disables the button and prints the backend reason when the mail cannot be resent', async () => {
    const reason = 'Thư gửi trước ngày 04/11/2026 không lưu nội dung nên không gửi lại được.'
    build(item({ has_body: false, can_resend: false, resend_block_reason: reason }))
    expect(await screen.findByText(reason)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Gửi lại/ })).toBeDisabled()
  })

  it('hides the button without audit.write', async () => {
    canWrite = false
    build(item())
    expect(await screen.findByText('SMTP 550')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Gửi lại/ })).not.toBeInTheDocument()
  })

  it('labels a resent row with its origin id', async () => {
    build(item({ id: 9, resent_from_id: 7 }))
    expect(await screen.findByText('Gửi lại từ #7')).toBeInTheDocument()
  })
})
