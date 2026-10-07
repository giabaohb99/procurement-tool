import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type * as CoreApi from '@/core/api'
import { LaborContractTemplateListPage } from './labor-contract-template-list-page'

const apiGet = vi.hoisted(() => vi.fn())
vi.mock('@/core/api', async (original) => ({
  ...(await original<typeof CoreApi>()),
  apiGet,
}))

function renderAs(permissions: Record<string, Record<string, boolean>>) {
  useAuthStore.setState({ user: { permissions } as never })
  apiGet.mockResolvedValue({ items: [], total: 0 })
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <LaborContractTemplateListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

afterEach(() => {
  useAuthStore.setState({ user: null })
  apiGet.mockReset()
})

describe('màn Mẫu hợp đồng — gác quyền', () => {
  // Lỗi cần chống: gõ thẳng URL khi thiếu khóa không được thấy bảng, và không được gọi API.
  it('thiếu quyền đọc: báo thiếu quyền, không dựng bảng, không gọi API', () => {
    renderAs({ labor_contract_template: {} })
    expect(screen.getByText('Bạn không có quyền xem màn này.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Tải lên mẫu/ })).toBeNull()
    expect(apiGet).not.toHaveBeenCalled()
  })

  it('chỉ có quyền đọc: thấy Danh sách biến, không thấy nút Tải lên mẫu', async () => {
    renderAs({ labor_contract_template: { read: true } })
    expect(await screen.findByRole('button', { name: /Danh sách biến/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Tải lên mẫu/ })).toBeNull()
  })

  it('có quyền tạo: thấy nút Tải lên mẫu', async () => {
    renderAs({ labor_contract_template: { read: true, create: true } })
    expect(await screen.findByRole('button', { name: /Tải lên mẫu/ })).toBeInTheDocument()
  })
})
