import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import type { LaborContractVariable, LaborContractVariableList } from '../types/labor-contract-variable'
import { LaborContractVariablesPage } from './labor-contract-variables-page'

const api = vi.hoisted(() => ({ list: vi.fn(), get: vi.fn(), create: vi.fn(), update: vi.fn(), remove: vi.fn(), inputFields: vi.fn() }))
vi.mock('../api/labor-contract-variable-api', () => ({ laborContractVariableApi: api }))
const confirmMock = vi.hoisted(() => vi.fn())
vi.mock('@/shared/ui/confirm-dialog', () => ({ confirm: confirmMock }))
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn(), warning: vi.fn() } }))

const row = (over: Partial<LaborContractVariable>): LaborContractVariable => ({
  id: 1, code: 'ho_ten', source: 1, value_type: 1, label: 'Họ và tên', description: '', example: 'Nguyễn Văn An', default_value: '',
  is_required: false, is_active: true, is_hidden: false, sort_order: 1, template_count: 2, group: 'Người lao động',
  created_at: null, created_by_name: '', ...over,
})
const custom = row({ id: 2, code: 'so_ngay_phep', source: 2, value_type: 3, label: 'Số ngày phép', group: 'Biến tùy chỉnh', is_required: true })

function list(over: Partial<LaborContractVariableList> = {}): LaborContractVariableList {
  return { total: 2, items: [row({}), custom], can_manage: true, can_delete: true, ...over }
}

function renderPage(permissions: Record<string, Record<string, boolean>>, initial = '/hr/labor-contract-templates/variables') {
  useAuthStore.setState({ user: { permissions } as never })
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initial]}>
        <LaborContractVariablesPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  api.list.mockResolvedValue(list())
  confirmMock.mockResolvedValue(true)
})
afterEach(() => {
  useAuthStore.setState({ user: null })
  vi.clearAllMocks()
})

describe('LaborContractVariablesPage', () => {
  it('thiếu quyền đọc: báo thiếu quyền, không gọi API', () => {
    renderPage({ labor_contract_template: {} })
    expect(screen.getByText('Bạn không có quyền xem màn này.')).toBeInTheDocument()
    expect(api.list).not.toHaveBeenCalled()
  })

  it('chỉ đọc (backend báo không được ghi): thấy bảng + nút chép, KHÔNG có Thêm / Sửa / Xóa', async () => {
    api.list.mockResolvedValue(list({ can_manage: false, can_delete: false }))
    renderPage({ labor_contract_template: { read: true } })
    expect(await screen.findByText('{{ ho_ten }}')).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: /Chép/i }).length).toBeGreaterThan(0)
    expect(screen.queryByRole('button', { name: /Thêm biến/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /^Sửa biến/ })).toBeNull()
    expect(screen.queryByRole('button', { name: /^Xóa biến/ })).toBeNull()
  })

  it('người quản lý: có Thêm biến; dòng hệ thống không có Xóa, dòng tùy chỉnh có Xóa + Ngừng dùng', async () => {
    renderPage({ labor_contract_template: { read: true, write: true, delete: true } })
    expect(await screen.findByRole('button', { name: /Thêm biến/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sửa biến ho_ten' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Ẩn biến ho_ten' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Xóa biến ho_ten' })).toBeNull()
    expect(screen.getByRole('button', { name: 'Xóa biến so_ngay_phep' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Ngừng dùng biến so_ngay_phep' })).toBeInTheDocument()
  })

  it('Ngừng dùng: hỏi xác nhận rồi mới gọi PATCH is_active=false; Hủy xác nhận thì không gọi', async () => {
    api.update.mockResolvedValue(custom)
    renderPage({ labor_contract_template: { read: true, write: true } })
    confirmMock.mockResolvedValueOnce(false)
    await userEvent.click(await screen.findByRole('button', { name: 'Ngừng dùng biến so_ngay_phep' }))
    await waitFor(() => expect(confirmMock).toHaveBeenCalledTimes(1))
    expect(api.update).not.toHaveBeenCalled()
    await userEvent.click(screen.getByRole('button', { name: 'Ngừng dùng biến so_ngay_phep' }))
    await waitFor(() => expect(api.update).toHaveBeenCalledWith(2, { is_active: false }))
  })

  it('biến hệ thống Ẩn: hỏi xác nhận rồi gọi PATCH is_hidden=true', async () => {
    api.update.mockResolvedValue(row({}))
    renderPage({ labor_contract_template: { read: true, write: true } })
    await userEvent.click(await screen.findByRole('button', { name: 'Ẩn biến ho_ten' }))
    await waitFor(() => expect(api.update).toHaveBeenCalledWith(1, { is_hidden: true }))
    expect(confirmMock).toHaveBeenCalledTimes(1)
  })

  it('câu rỗng khác nhau khi đang lọc và khi chưa có biến tùy chỉnh', async () => {
    api.list.mockResolvedValue(list({ total: 0, items: [] }))
    const { unmount } = renderPage({ labor_contract_template: { read: true } })
    expect(await screen.findByText('Chưa có biến tùy chỉnh. Bấm «Thêm biến».')).toBeInTheDocument()
    unmount()
    renderPage({ labor_contract_template: { read: true } }, '/hr/labor-contract-templates/variables?source=2')
    expect(await screen.findByText('Không có biến nào khớp bộ lọc.')).toBeInTheDocument()
  })

  it('bộ lọc truyền đúng tham số lên API, mặc định chỉ có trang', async () => {
    renderPage({ labor_contract_template: { read: true } }, '/hr/labor-contract-templates/variables?source=2')
    await waitFor(() => expect(api.list).toHaveBeenCalled())
    expect(api.list.mock.calls.at(-1)?.[0]).toMatchObject({ page: 1, source: 2 })
  })
})
