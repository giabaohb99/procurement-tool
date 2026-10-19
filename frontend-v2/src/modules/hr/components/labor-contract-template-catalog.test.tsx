import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type * as CoreApi from '@/core/api'
import { LaborContractTemplateCatalog } from './labor-contract-template-catalog'
import { LaborContractTemplateHeaderActions } from './labor-contract-template-header-actions'

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
      <MemoryRouter initialEntries={['/catalog']}>
        <Routes>
          <Route
            path="/catalog"
            element={
              //  Như trang «Thiết lập văn bản»: nút ở góc tiêu đề + bảng bên dưới.
              <>
                <LaborContractTemplateHeaderActions />
                <LaborContractTemplateCatalog />
              </>
            }
          />
          <Route path="/hr/labor-contract-templates/variables" element={<p>Trang danh sách biến</p>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

afterEach(() => {
  useAuthStore.setState({ user: null })
  apiGet.mockReset()
})

describe('LaborContractTemplateCatalog — gác quyền', () => {
  // Lỗi cần chống: gõ thẳng URL khi thiếu khóa không được thấy bảng, và không được gọi API.
  it('thiếu quyền đọc: báo thiếu quyền, không dựng bảng, không gọi API', () => {
    renderAs({ labor_contract_template: {} })
    expect(screen.getByText('Bạn không có quyền xem màn này.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Tải lên mẫu/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /Danh sách biến/ })).toBeNull()
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

  //  duoc-CR-630: nút «Danh sách biến» không còn mở hộp thoại chỉ xem mà đi tới trang quản lý biến.
  it('nút Danh sách biến điều hướng tới trang biến', async () => {
    renderAs({ labor_contract_template: { read: true } })
    await userEvent.click(await screen.findByRole('button', { name: /Danh sách biến/ }))
    expect(await screen.findByText('Trang danh sách biến')).toBeInTheDocument()
  })
})
