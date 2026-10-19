import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { LaborContractVariable, LaborContractVariableDetail } from '../types/labor-contract-variable'
import { LaborContractVariableFormDialog } from './labor-contract-variable-form-dialog'

const api = vi.hoisted(() => ({ get: vi.fn(), create: vi.fn(), update: vi.fn(), list: vi.fn(), inputFields: vi.fn(), remove: vi.fn() }))
vi.mock('../api/labor-contract-variable-api', () => ({ laborContractVariableApi: api }))
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn(), warning: vi.fn() } }))

const variable = (over: Partial<LaborContractVariable> = {}): LaborContractVariable => ({
  id: 5, code: 'so_ngay_phep', source: 2, value_type: 3, label: 'Số ngày phép', description: '', example: '', default_value: '12',
  is_required: false, is_active: true, is_hidden: false, sort_order: 1, template_count: 0, group: 'Biến tùy chỉnh',
  created_at: null, created_by_name: '', ...over,
})
const detail = (v: LaborContractVariable, locked: boolean, usage = { templates: [], template_count: 0, hidden_template_count: 0, contract_count: 0 }): LaborContractVariableDetail =>
  ({ ...v, usage, code_locked: locked })

function renderDialog(v: LaborContractVariable | null) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const onOpenChange = vi.fn()
  render(
    <QueryClientProvider client={client}>
      <LaborContractVariableFormDialog open onOpenChange={onOpenChange} variable={v} />
    </QueryClientProvider>,
  )
  return { onOpenChange }
}

beforeEach(() => {
  vi.clearAllMocks()
  api.create.mockResolvedValue(variable())
  api.update.mockResolvedValue(variable())
})

describe('LaborContractVariableFormDialog', () => {
  it('thêm mới: có ô mã, kiểu, mặc định, bắt buộc, đang dùng; Lưu gửi payload không có is_hidden', async () => {
    const { onOpenChange } = renderDialog(null)
    await userEvent.type(screen.getByLabelText(/Mã biến/), 'so_ngay_phep')
    await userEvent.type(screen.getByLabelText(/Tên hiển thị/), 'Số ngày phép')
    expect(screen.getByRole('switch', { name: 'Bắt buộc' })).toBeInTheDocument()
    expect(screen.getByRole('switch', { name: 'Đang dùng' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(api.create).toHaveBeenCalledTimes(1))
    expect(api.create.mock.calls[0][0]).toMatchObject({ code: 'so_ngay_phep', label: 'Số ngày phép', value_type: 1, is_active: true, is_required: false })
    expect('is_hidden' in api.create.mock.calls[0][0]).toBe(false)
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false))
  })

  it.each(['Ho_Ten', '1abc', 'ab-cd', 'x'])('mã «%s» sai hình dạng -> báo lỗi, không gọi API', async (code) => {
    renderDialog(null)
    await userEvent.type(screen.getByLabelText(/Mã biến/), code)
    await userEvent.type(screen.getByLabelText(/Tên hiển thị/), 'Nhãn')
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    expect(await screen.findByText(/Mã biến gồm chữ thường/)).toBeInTheDocument()
    expect(api.create).not.toHaveBeenCalled()
  })

  it('bấm Lưu 3 lần liền chỉ gọi API một lần', async () => {
    let release: (v: LaborContractVariable) => void = () => undefined
    api.create.mockReturnValue(new Promise<LaborContractVariable>((r) => { release = r }))
    renderDialog(null)
    await userEvent.type(screen.getByLabelText(/Mã biến/), 'bien_moi')
    await userEvent.type(screen.getByLabelText(/Tên hiển thị/), 'Biến mới')
    const save = screen.getByRole('button', { name: 'Lưu' })
    await userEvent.click(save)
    await userEvent.click(save)
    await userEvent.click(save)
    expect(api.create).toHaveBeenCalledTimes(1)
    release(variable())
  })

  it('đổi kiểu -> ô mặc định đổi loại ô và bị xóa trắng', async () => {
    renderDialog(null)
    expect(screen.getByRole('textbox', { name: 'Giá trị mặc định' }).tagName).toBe('INPUT')
    await userEvent.click(screen.getByRole('combobox', { name: 'Kiểu giá trị' }))
    await userEvent.click(await screen.findByRole('option', { name: 'Chữ nhiều dòng' }))
    expect(screen.getByRole('textbox', { name: 'Giá trị mặc định' }).tagName).toBe('TEXTAREA')
  })

  it('sửa biến đã dùng (code_locked): mã + kiểu CHỈ ĐỌC (không disabled) kèm lý do, vẫn lưu được nhãn', async () => {
    const v = variable()
    api.get.mockResolvedValue(detail(v, true, { templates: [], template_count: 2, hidden_template_count: 0, contract_count: 3 }))
    renderDialog(v)
    expect(await screen.findByText(/Đang dùng trong 2 mẫu \/ 3 hợp đồng/)).toBeInTheDocument()
    expect(screen.queryByLabelText(/Mã biến/)).toBeNull()                 // không còn ô nhập mã
    expect(screen.getAllByText('so_ngay_phep').length).toBeGreaterThan(0)
    expect(screen.queryByRole('combobox', { name: 'Kiểu giá trị' })).toBeNull()
    const label = screen.getByLabelText(/Tên hiển thị/)
    expect(label).not.toBeDisabled()
    await userEvent.clear(label)
    await userEvent.type(label, 'Nhãn mới')
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(api.update).toHaveBeenCalledTimes(1))
    expect(api.update.mock.calls[0]).toEqual([5, expect.objectContaining({ label: 'Nhãn mới', code: 'so_ngay_phep', value_type: 3 })])
  })

  it('biến hệ thống: chỉ 3 ô (tên, mô tả, ẩn); Lưu chỉ gửi label · description · is_hidden', async () => {
    const sys = variable({ id: 9, code: 'ho_ten', source: 1, value_type: 1, label: 'Họ và tên', default_value: '' })
    api.get.mockResolvedValue(detail(sys, true))
    renderDialog(sys)
    expect(await screen.findByLabelText(/Tên hiển thị/)).toBeInTheDocument()
    expect(screen.getByRole('switch', { name: 'Ẩn khỏi danh sách hướng dẫn' })).toBeInTheDocument()
    for (const name of ['Bắt buộc', 'Đang dùng']) expect(screen.queryByRole('switch', { name })).toBeNull()
    expect(screen.queryByRole('combobox', { name: 'Kiểu giá trị' })).toBeNull()
    await userEvent.click(screen.getByRole('switch', { name: 'Ẩn khỏi danh sách hướng dẫn' }))
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(api.update).toHaveBeenCalledTimes(1))
    expect(api.update.mock.calls[0]).toEqual([9, { label: 'Họ và tên', description: '', is_hidden: true }])
  })

  it('sửa: ô điền theo bản chi tiết mới nhất, không theo dòng bảng đã cũ', async () => {
    const stale = variable({ label: 'Nhãn cũ trên bảng' })
    api.get.mockResolvedValue(detail(variable({ label: 'Nhãn mới từ máy chủ' }), false))
    renderDialog(stale)
    expect(await screen.findByDisplayValue('Nhãn mới từ máy chủ')).toBeInTheDocument()
    expect(screen.queryByDisplayValue('Nhãn cũ trên bảng')).toBeNull()
  })
})
