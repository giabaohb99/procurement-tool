import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { laborContractEmployee, makeLaborContract } from './labor-contract-fixture'
import { LaborContractFormDialog } from './labor-contract-form-dialog'

const canMock = vi.fn((_entity: string, _action: string) => true)
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: canMock, canAny: () => true }),
}))

const listTemplateOptions = vi.fn()
const update = vi.fn()
const create = vi.fn()
vi.mock('../api/labor-contract-api', () => ({
  laborContractApi: {
    listTemplateOptions: (...a: unknown[]) => listTemplateOptions(...a),
    update: (...a: unknown[]) => update(...a),
    create: (...a: unknown[]) => create(...a),
  },
}))
const inputFields = vi.fn()
vi.mock('../api/labor-contract-variable-api', () => ({
  laborContractVariableApi: { inputFields: (...a: unknown[]) => inputFields(...a) },
}))
const toastWarning = vi.fn()
vi.mock('sonner', () => ({
  toast: { success: vi.fn(), error: vi.fn(), warning: (...a: unknown[]) => toastWarning(...a) },
}))

beforeEach(() => {
  vi.clearAllMocks()
  canMock.mockReturnValue(true)
  listTemplateOptions.mockResolvedValue([{ id: 1, name: 'Mẫu 1', contract_type: 2 }])
  inputFields.mockResolvedValue([])
  update.mockResolvedValue({ item: makeLaborContract(), warnings: [] })
})

function renderDialog(opts: { row?: ReturnType<typeof makeLaborContract> | null; outerSubmit?: () => void } = {}) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const onOpenChange = vi.fn()
  const dialog = (
    <MemoryRouter>
      <QueryClientProvider client={client}>
        <LaborContractFormDialog open onOpenChange={onOpenChange} employee={laborContractEmployee} row={opts.row ?? null} />
      </QueryClientProvider>
    </MemoryRouter>
  )
  render(
    opts.outerSubmit ? (
      <form onSubmit={(e) => { e.preventDefault(); opts.outerSubmit?.() }}>{dialog}</form>
    ) : (
      dialog
    ),
  )
  return { onOpenChange }
}

describe('LaborContractFormDialog', () => {
  // Bẫy 1: hộp nằm trong <form> hồ sơ; bấm Lưu mà submit nổi bọt thì lưu đè hồ sơ nhân sự.
  it('bấm Lưu KHÔNG submit form cha (hồ sơ nhân sự)', async () => {
    const outerSubmit = vi.fn()
    renderDialog({ row: makeLaborContract(), outerSubmit })
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(update).toHaveBeenCalledTimes(1))
    expect(outerSubmit).not.toHaveBeenCalled()
  })

  it('sửa: gửi PATCH tới đúng id, tiền giữ nguyên, ngày kết thúc là chuỗi ngày', async () => {
    renderDialog({ row: makeLaborContract({ id: 42 }) })
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(update).toHaveBeenCalled())
    expect(update.mock.calls[0][0]).toBe(42)
    expect(update.mock.calls[0][1]).toMatchObject({ base_salary: 15_000_000, end_date: '2026-12-31', contract_type: 2 })
  })

  it('cảnh báo từ backend (> 36 tháng) hiện toast warning, hộp vẫn đóng như thành công', async () => {
    update.mockResolvedValue({ item: makeLaborContract(), warnings: ['Nên không quá 36 tháng'] })
    const { onOpenChange } = renderDialog({ row: makeLaborContract() })
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(toastWarning).toHaveBeenCalledWith('Nên không quá 36 tháng'))
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false))
  })

  it('backend trả thiếu warnings (undefined) cũng không vỡ', async () => {
    update.mockResolvedValue({ item: makeLaborContract() })
    const { onOpenChange } = renderDialog({ row: makeLaborContract() })
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(onOpenChange).toHaveBeenCalledWith(false))
  })

  it('không xác định thời hạn: ẩn ô Ngày kết thúc', () => {
    renderDialog({ row: makeLaborContract({ contract_type: 3, end_date: null }) })
    expect(screen.queryByText(/Ngày kết thúc/)).not.toBeInTheDocument()
  })

  it('loại xác định thời hạn: có ô Ngày kết thúc bắt buộc (*)', () => {
    renderDialog({ row: makeLaborContract() })
    expect(screen.getByText('Ngày kết thúc *')).toBeInTheDocument()
  })

  it('pháp nhân hiện CHỈ ĐỌC (không phải ô nhập)', () => {
    renderDialog({ row: makeLaborContract() })
    expect(screen.getByText('Công ty A')).toBeInTheDocument()
    expect(screen.queryByRole('textbox', { name: /Pháp nhân/ })).not.toBeInTheDocument()
  })

  it('mẫu rỗng: báo «chưa có mẫu cho loại này» kèm liên kết khi có quyền xem màn Mẫu', async () => {
    listTemplateOptions.mockResolvedValue([])
    renderDialog({ row: makeLaborContract() })
    expect(await screen.findByText(/chưa có mẫu cho loại này/)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Mẫu hợp đồng/ })).toHaveAttribute('href', '/document/settings?tab=templates&kind=labor-contract')
  })

  it('mẫu rỗng nhưng không có quyền xem màn Mẫu: chỉ câu báo, không có liên kết', async () => {
    listTemplateOptions.mockResolvedValue([])
    canMock.mockImplementation((entity) => entity !== 'labor_contract_template')
    renderDialog({ row: makeLaborContract() })
    expect(await screen.findByText(/chưa có mẫu cho loại này/)).toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })

  it('có mẫu thì không hiện câu cảnh báo', async () => {
    renderDialog({ row: makeLaborContract() })
    await waitFor(() => expect(listTemplateOptions).toHaveBeenCalled())
    expect(screen.queryByText(/chưa có mẫu/)).not.toBeInTheDocument()
  })

  it('lập mới chưa chọn loại: bấm Lưu bị chặn ở form, không gọi API (kể cả không gọi list mẫu)', async () => {
    renderDialog()
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    expect(await screen.findByText('Chọn loại hợp đồng')).toBeInTheDocument()
    expect(create).not.toHaveBeenCalled()
    expect(listTemplateOptions).not.toHaveBeenCalled()
  })

  // duoc-CR-630 ─ ô «Thông tin bổ sung cho mẫu»
  const field = (code: string, over: Record<string, unknown> = {}) => ({
    code, label: `Nhãn ${code}`, description: '', value_type: 1, default_value: '', is_required: false,
    is_active: true, sort_order: 0, ...over,
  })

  it('có biến tùy chỉnh: ô hiện; Lưu (sửa) gửi custom_values, ô trống gửi "" và biến ngừng dùng KHÔNG được gửi', async () => {
    inputFields.mockResolvedValue([field('a_chu'), field('b_cu', { is_active: false })])
    renderDialog({ row: makeLaborContract({ custom_values: { a_chu: 'cũ', b_cu: 'giữ' } }) })
    const box = await screen.findByRole('textbox', { name: 'Nhãn a_chu' })
    expect(box).toHaveValue('cũ')
    await userEvent.clear(box)
    await userEvent.type(box, 'mới')
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(update).toHaveBeenCalled())
    expect(update.mock.calls[0][1].custom_values).toEqual({ a_chu: 'mới' })
  })

  it('lập mới: giá trị mặc định được SAO vào ô; sửa hợp đồng đã lập thì KHÔNG điền mặc định', async () => {
    inputFields.mockResolvedValue([field('a_chu', { default_value: 'mặc định' })])
    const { unmount } = render(
      <MemoryRouter>
        <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
          <LaborContractFormDialog open onOpenChange={vi.fn()} employee={laborContractEmployee} row={null} />
        </QueryClientProvider>
      </MemoryRouter>,
    )
    expect(await screen.findByDisplayValue('mặc định')).toBeInTheDocument()
    unmount()
    renderDialog({ row: makeLaborContract({ custom_values: {} }) })
    expect(await screen.findByRole('textbox', { name: 'Nhãn a_chu' })).toHaveValue('')
  })

  it('lập mới: người dùng xóa trắng ô đã điền sẵn thì ô giữ TRỐNG (không bị sao lại mặc định)', async () => {
    inputFields.mockResolvedValue([field('a_chu', { default_value: 'mặc định' })])
    renderDialog({ row: null })
    const box = await screen.findByDisplayValue('mặc định')
    await userEvent.clear(box)
    await userEvent.type(screen.getByLabelText(/Số hợp đồng/), 'HD-1')   // render lại form
    expect(box).toHaveValue('')
  })

  it('không có biến tùy chỉnh: không vẽ khối bổ sung và payload không có custom_values', async () => {
    renderDialog({ row: makeLaborContract() })
    await userEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(update).toHaveBeenCalled())
    expect(screen.queryByText('Thông tin bổ sung cho mẫu')).toBeNull()
    expect(update.mock.calls[0][1].custom_values).toEqual({})
  })
})
