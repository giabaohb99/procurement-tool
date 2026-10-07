import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type * as CoreApi from '@/core/api'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { LaborContractPlaceholderGuideDialog } from './labor-contract-placeholder-guide-dialog'

const apiGet = vi.hoisted(() => vi.fn())
vi.mock('@/core/api', async (original) => ({
  ...(await original<typeof CoreApi>()),
  apiGet,
}))

afterEach(() => {
  Reflect.deleteProperty(navigator, 'clipboard')
  apiGet.mockReset()
})

function renderGuide() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <LaborContractPlaceholderGuideDialog open onOpenChange={vi.fn()} />
    </QueryClientProvider>,
  )
}

describe('hộp hướng dẫn biến', () => {
  it('đọc danh mục từ API, nhóm theo group, nút chép đặt đúng {{ ho_ten }}', async () => {
    apiGet.mockResolvedValue([
      { key: 'ho_ten', label: 'Họ và tên', group: 'Người lao động', example: 'Nguyễn Văn An' },
      { key: 'ten_cong_ty', label: 'Tên pháp nhân', group: 'Pháp nhân (bên A)', example: 'Cty A' },
    ])
    const writeText = vi.fn(async () => {})
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true, writable: true })

    renderGuide()

    expect(await screen.findByRole('heading', { name: 'Người lao động' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Pháp nhân (bên A)' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /Chép biến Họ và tên/ }))
    expect(writeText).toHaveBeenCalledWith('{{ ho_ten }}')
    expect(apiGet).toHaveBeenCalledWith('/api/labor-contract-templates/placeholders')
  })

  it('API lỗi thì báo lỗi, không vỡ trang', async () => {
    apiGet.mockRejectedValue(new Error('boom'))
    renderGuide()
    expect(await screen.findByText('Không tải được danh sách biến.')).toBeInTheDocument()
  })
})
