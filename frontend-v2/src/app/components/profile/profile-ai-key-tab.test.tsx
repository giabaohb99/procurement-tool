import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { AiKeyInfo } from '@/modules/system/api/agent-hub-api'
import { ProfileAiKeyTab } from './profile-ai-key-tab'

/**
 * Tab «Khóa AI» ở Trang cá nhân (ai-CR-053).
 *
 * Chỗ dễ lủng: khóa thô phải đi qua PUT `/api/agent-hub/ai-key` rồi ô nhập XÓA TRẮNG (không để khóa nằm lại
 * trên màn), màn chỉ hiện 4 ký tự cuối do backend trả, và ô nhập là `password`.
 */

const apiGet = vi.fn()
const apiPut = vi.fn()
const apiDelete = vi.fn()

vi.mock('@/core/api', () => ({
  apiGet: (...args: unknown[]) => apiGet(...args),
  apiPost: vi.fn(),
  apiPut: (...args: unknown[]) => apiPut(...args),
  apiPatch: vi.fn(),
  apiDelete: (...args: unknown[]) => apiDelete(...args),
}))

vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

vi.mock('@/shared/ui/confirm-dialog', () => ({
  confirm: vi.fn(() => Promise.resolve(true)),
}))

function renderTab() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <ProfileAiKeyTab />
    </QueryClientProvider>,
  )
}

function mockKey(info: Partial<AiKeyInfo> = {}) {
  apiGet.mockResolvedValue({ provider: 'gemini', has_key: false, hint: '', verified_at: null, ...info })
}

describe('ProfileAiKeyTab', () => {
  beforeEach(() => {
    apiGet.mockReset()
    apiPut.mockReset()
    apiDelete.mockReset()
  })

  it('saves the raw key through PUT, then clears the input and shows only the hint', async () => {
    mockKey()
    apiPut.mockResolvedValue({ provider: 'gemini', has_key: true, hint: '…9999', verified_at: '2026-09-25T08:00:00' })
    renderTab()
    expect(await screen.findByText(/Chưa có khóa/)).toBeInTheDocument()
    const input = screen.getByLabelText(/Dán khóa Gemini/)
    expect(input).toHaveAttribute('type', 'password')
    await userEvent.type(input, 'AIzaSy-khoa-thu-9999')
    mockKey({ has_key: true, hint: '…9999', verified_at: '2026-09-25T08:00:00' })
    await userEvent.click(screen.getByRole('button', { name: /Lưu khóa/ }))
    await waitFor(() => expect(apiPut).toHaveBeenCalledWith('/api/agent-hub/ai-key', { key: 'AIzaSy-khoa-thu-9999' }))
    await waitFor(() => expect(input).toHaveValue(''))
    expect(await screen.findByText('…9999')).toBeInTheDocument()
    expect(screen.queryByText(/AIzaSy-khoa-thu-9999/)).not.toBeInTheDocument()
  })

  it('removes the key after confirmation', async () => {
    mockKey({ has_key: true, hint: '…1234' })
    apiDelete.mockResolvedValue({ provider: 'gemini', has_key: false, hint: '', verified_at: null })
    renderTab()
    await userEvent.click(await screen.findByRole('button', { name: /Gỡ khóa/ }))
    await waitFor(() => expect(apiDelete).toHaveBeenCalledWith('/api/agent-hub/ai-key'))
  })

  it('keeps the save button disabled while the input is blank', async () => {
    mockKey()
    renderTab()
    expect(await screen.findByRole('button', { name: /Lưu khóa/ })).toBeDisabled()
    expect(apiGet).toHaveBeenCalledWith('/api/agent-hub/ai-key')
  })
})
