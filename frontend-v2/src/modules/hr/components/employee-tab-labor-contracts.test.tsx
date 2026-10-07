import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { EmployeeTabLaborContracts } from './employee-tab-labor-contracts'
import { laborContractEmployee, makeLaborContract } from './labor-contract-fixture'

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true, canAny: () => true }),
}))
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn(), warning: vi.fn() } }))

const api = {
  listByEmployee: vi.fn(),
  listTemplateOptions: vi.fn(),
  listTemplateOptionsForContract: vi.fn(),
  transition: vi.fn(),
  generate: vi.fn(),
  downloadDocument: vi.fn(),
  remove: vi.fn(),
}
vi.mock('../api/labor-contract-api', () => ({
  laborContractApi: {
    listByEmployee: (...a: unknown[]) => api.listByEmployee(...a),
    listTemplateOptions: (...a: unknown[]) => api.listTemplateOptions(...a),
    listTemplateOptionsForContract: (...a: unknown[]) => api.listTemplateOptionsForContract(...a),
    transition: (...a: unknown[]) => api.transition(...a),
    generate: (...a: unknown[]) => api.generate(...a),
    downloadDocument: (...a: unknown[]) => api.downloadDocument(...a),
    remove: (...a: unknown[]) => api.remove(...a),
  },
}))
const confirmMock = vi.fn()
vi.mock('@/shared/ui/confirm-dialog', () => ({ confirm: (...a: unknown[]) => confirmMock(...a) }))

beforeEach(() => {
  vi.clearAllMocks()
  api.listTemplateOptions.mockResolvedValue([{ id: 5, name: 'Mẫu HĐ xác định', contract_type: 2 }])
  api.listTemplateOptionsForContract.mockResolvedValue([{ id: 5, name: 'Mẫu HĐ xác định', contract_type: 2 }])
  api.transition.mockResolvedValue(makeLaborContract())
  api.generate.mockResolvedValue(makeLaborContract())
  api.downloadDocument.mockResolvedValue(undefined)
})

function renderTab() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <MemoryRouter>
      <QueryClientProvider client={client}>
        <EmployeeTabLaborContracts employee={laborContractEmployee} />
      </QueryClientProvider>
    </MemoryRouter>,
  )
}

describe('EmployeeTabLaborContracts', () => {
  it('danh sách rỗng: câu hướng dẫn; có nút «Lập hợp đồng» khi can_create', async () => {
    api.listByEmployee.mockResolvedValue({ items: [], can_create: true })
    renderTab()
    expect(await screen.findByText('Nhân sự này chưa có hợp đồng lao động nào.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Lập hợp đồng/ })).toBeInTheDocument()
  })

  it('can_create = false: ẩn nút Lập hợp đồng', async () => {
    api.listByEmployee.mockResolvedValue({ items: [], can_create: false })
    renderTab()
    await screen.findByText('Nhân sự này chưa có hợp đồng lao động nào.')
    expect(screen.queryByRole('button', { name: /Lập hợp đồng/ })).not.toBeInTheDocument()
  })

  it('HĐ đã ký nhưng quá hạn hiện huy hiệu «Hết hạn» (effective_status), không phải «Đã ký»', async () => {
    api.listByEmployee.mockResolvedValue({
      items: [makeLaborContract({ status: 2, effective_status: 3, can_edit: false, transitions: [4] })],
      can_create: true,
    })
    renderTab()
    expect(await screen.findByText('Hết hạn')).toBeInTheDocument()
    expect(screen.queryByText('Đã ký – hiệu lực')).not.toBeInTheDocument()
  })

  it('hiện lương, thời hạn, loại; HĐ không xác định thời hạn hiện «Từ …» không có ngày cuối', async () => {
    api.listByEmployee.mockResolvedValue({
      items: [makeLaborContract({ contract_type: 3, end_date: null })],
      can_create: true,
    })
    renderTab()
    expect(await screen.findByText('15.000.000')).toBeInTheDocument()
    expect(screen.getByText('Không xác định thời hạn')).toBeInTheDocument()
    expect(screen.getByText('Từ 01/01/2026')).toBeInTheDocument()
  })

  it('Ký: hộp chỉ hỏi ngày ký, gửi to_status=2 KHÔNG kèm tệp hay lý do', async () => {
    api.listByEmployee.mockResolvedValue({ items: [makeLaborContract({ id: 9 })], can_create: true })
    renderTab()
    await userEvent.click(await screen.findByLabelText('Đánh dấu đã ký'))
    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).queryByLabelText(/Lý do/)).not.toBeInTheDocument()
    await userEvent.click(within(dialog).getByRole('button', { name: 'Xác nhận' }))
    await waitFor(() => expect(api.transition).toHaveBeenCalledTimes(1))
    expect(api.transition.mock.calls[0][0]).toBe(9)
    expect(api.transition.mock.calls[0][1]).toMatchObject({ to_status: 2, reason: '' })
    expect(api.transition.mock.calls[0][1].date).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })

  it('Hủy thiếu lý do: báo lỗi tại chỗ, KHÔNG gọi API', async () => {
    api.listByEmployee.mockResolvedValue({ items: [makeLaborContract()], can_create: true })
    renderTab()
    await userEvent.click(await screen.findByLabelText('Hủy hợp đồng'))
    const dialog = await screen.findByRole('dialog')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Xác nhận' }))
    expect(await within(dialog).findByRole('alert')).toHaveTextContent(/lý do/i)
    expect(api.transition).not.toHaveBeenCalled()
  })

  it('Sinh tệp khi pháp nhân chưa có mẫu: hiện câu hướng dẫn và khóa nút Sinh', async () => {
    api.listByEmployee.mockResolvedValue({ items: [makeLaborContract()], can_create: true })
    api.listTemplateOptionsForContract.mockResolvedValue([])
    renderTab()
    await userEvent.click(await screen.findByLabelText('Sinh tệp hợp đồng'))
    const dialog = await screen.findByRole('dialog')
    expect(await within(dialog).findByText(/chưa có mẫu cho loại hợp đồng này/)).toBeInTheDocument()
    expect(within(dialog).getByRole('button', { name: 'Sinh tệp' })).toBeDisabled()
  })

  it('Sinh tệp với đúng một mẫu: chọn sẵn, gửi template_id của mẫu đó', async () => {
    api.listByEmployee.mockResolvedValue({ items: [makeLaborContract({ id: 3 })], can_create: true })
    renderTab()
    await userEvent.click(await screen.findByLabelText('Sinh tệp hợp đồng'))
    const dialog = await screen.findByRole('dialog')
    const gen = within(dialog).getByRole('button', { name: 'Sinh tệp' })
    await waitFor(() => expect(gen).toBeEnabled())
    await userEvent.click(gen)
    await waitFor(() => expect(api.generate).toHaveBeenCalledWith(3, { template_id: 5 }))
    // Ô chọn mẫu hỏi theo CHÍNH hợp đồng (pháp nhân + loại lúc lập), không theo nhân sự hiện tại:
    // nhân sự chuyển pháp nhân sau khi lập HĐ thì mẫu cũ vẫn ra, mẫu pháp nhân mới không lẫn vào.
    expect(api.listTemplateOptionsForContract).toHaveBeenCalledWith(3)
    expect(api.listTemplateOptions).not.toHaveBeenCalled()
  })

  it('Xóa: hỏi xác nhận; từ chối thì không gọi API', async () => {
    api.listByEmployee.mockResolvedValue({ items: [makeLaborContract()], can_create: true })
    confirmMock.mockResolvedValue(false)
    renderTab()
    await userEvent.click(await screen.findByLabelText('Xóa hợp đồng'))
    await waitFor(() => expect(confirmMock).toHaveBeenCalled())
    expect(api.remove).not.toHaveBeenCalled()
  })

  it('tải .docx lỗi (đã toast) không gây lỗi chưa bắt', async () => {
    api.listByEmployee.mockResolvedValue({
      items: [makeLaborContract({ has_generated_file: true, can_print: true })],
      can_create: true,
    })
    api.downloadDocument.mockRejectedValue(new Error('403'))
    renderTab()
    await userEvent.click(await screen.findByLabelText('Tải hợp đồng (.docx)'))
    await waitFor(() => expect(api.downloadDocument).toHaveBeenCalled())
    expect(screen.getByLabelText('Tải hợp đồng (.docx)')).toBeEnabled()
  })
})
