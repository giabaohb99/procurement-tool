import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { EmailNotificationCard } from './email-notification-card'

/**
 * Công tắc EMAIL thông báo của chính mình (bao-CR-349).
 *
 * Chỗ dễ hỏng nhất KHÔNG phải cú bấm mà là giá trị `undefined`: hệ chưa chạy
 * migration `d2f45a8c9e10` thì `/api/auth/me` không trả trường này. Đọc nó thành
 * "đang tắt" là màn hình bịa ra một người không nhận thư trong khi họ vẫn nhận —
 * và người đó sẽ bấm "Bật" cho một công tắc vốn đang bật.
 */

//  Chặn ở tầng `@/core/api` theo luật test của dự án, không chặn axios.
const apiPut = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiPut: (...args: unknown[]) => apiPut(...args),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}))

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

function renderCard(value?: boolean) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <EmailNotificationCard value={value} />
    </QueryClientProvider>,
  )
}

describe('EmailNotificationCard', () => {
  beforeEach(() => {
    apiPut.mockReset()
    apiPut.mockResolvedValue({ notify_email: false })
  })

  it('treats a missing notify_email as ON, the column default', () => {
    renderCard(undefined)
    expect(screen.getByText('Đang bật')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Tắt email thông báo/ })).toBeInTheDocument()
  })

  it('shows OFF only for an explicit false', () => {
    renderCard(false)
    expect(screen.getByText('Đang tắt')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Bật email thông báo/ })).toBeInTheDocument()
  })

  it('sends the opposite of the current value when clicked', async () => {
    renderCard(true)
    await userEvent.click(screen.getByRole('button', { name: /Tắt email thông báo/ }))
    await waitFor(() =>
      expect(apiPut).toHaveBeenCalledWith('/api/auth/notify-email', { notify_email: false }),
    )
  })

  it('keeps the password-reset promise on screen — that mail must not look blocked', () => {
    renderCard(false)
    expect(screen.getByText(/Thư đặt lại mật khẩu/)).toBeInTheDocument()
  })
})
