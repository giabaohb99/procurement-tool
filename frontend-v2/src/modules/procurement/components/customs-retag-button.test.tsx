import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { CustomsRetagButton } from './customs-retag-button'

const retag = vi.fn()
vi.mock('../api/customs-kind-api', () => ({ retagCustomsKinds: () => retag() }))
const toastSuccess = vi.fn()
vi.mock('sonner', () => ({ toast: { success: (m: string) => toastSuccess(m), error: vi.fn() } }))

function mount() {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <CustomsRetagButton />
    </QueryClientProvider>,
  )
}

describe('CustomsRetagButton — bao-CR-494', () => {
  it('bấm là gọi gắn lại và báo số dòng nguyên liệu / thành phẩm', async () => {
    retag.mockResolvedValue({ total: 18243, tagged: 9000, technical: 4100 })
    mount()
    await userEvent.click(screen.getByRole('button', { name: /gắn lại nhãn/i }))
    await waitFor(() => expect(toastSuccess).toHaveBeenCalledTimes(1))
    expect(toastSuccess.mock.calls[0][0]).toContain('4.100 nguyên liệu')
    expect(toastSuccess.mock.calls[0][0]).toContain('14.143 thành phẩm')
  })
})
