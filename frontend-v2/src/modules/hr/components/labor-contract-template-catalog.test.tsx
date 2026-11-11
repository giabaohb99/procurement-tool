import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
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
              //  Như trang "Thiết lập văn bản": nút ở góc tiêu đề + bảng bên dưới.
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

  //  duoc-CR-630: nút "Danh sách biến" không còn mở hộp thoại chỉ xem mà đi tới trang quản lý biến.
  it('nút Danh sách biến điều hướng tới trang biến', async () => {
    renderAs({ labor_contract_template: { read: true } })
    await userEvent.click(await screen.findByRole('button', { name: /Danh sách biến/ }))
    expect(await screen.findByText('Trang danh sách biến')).toBeInTheDocument()
  })

  //  duoc-CR-748: sắp xếp tại MÁY CHỦ; "Tệp gốc" và "Thao tác" không xếp được.
  it('bấm tiêu đề cột gửi đúng khóa xếp lên API và về trang 1', async () => {
    const header = (text: string) => screen.getByText(text, { selector: 'thead span' })
    const lastParams = () => {
      const calls = apiGet.mock.calls.filter(([url]) => url === '/api/labor-contract-templates')
      return (calls.at(-1)?.[1] as { params: Record<string, unknown> }).params
    }
    renderAs({ labor_contract_template: { read: true } })
    await screen.findByText('Tên mẫu', { selector: 'thead span' })
    //  Cột "Ngày tạo" khai `sortDescFirst`: lần bấm đầu xếp GIẢM (mới nhất trước).
    const cases: [string, string, string][] = [
      ['Tên mẫu', 'name', 'asc'],
      ['Pháp nhân', 'company', 'asc'],
      ['Loại HĐ', 'contract_type', 'asc'],
      ['Số HĐ đã dùng', 'contract_count', 'asc'],
      ['Trạng thái', 'is_active', 'asc'],
      ['Ngày tạo', 'created_at', 'desc'],
    ]
    for (const [text, key, dir] of cases) {
      await userEvent.click(header(text))
      await waitFor(() => expect(lastParams()).toMatchObject({ sort_by: key, sort_dir: dir, page: 1 }))
    }
    await userEvent.click(header('Tệp gốc'))
    await userEvent.click(header('Ngày tạo'))
    await waitFor(() => expect(lastParams()).toMatchObject({ sort_by: 'created_at', sort_dir: 'asc' }))
  })
})
