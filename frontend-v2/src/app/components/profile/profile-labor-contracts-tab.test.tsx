import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { MyLaborContract } from '@/modules/hr/types/my-labor-contract'
import { ProfileLaborContractsTab } from './profile-labor-contracts-tab'

const state = vi.hoisted(() => ({
  items: [] as MyLaborContract[],
  downloads: [] as string[],
}))

vi.mock('@/core/api', () => ({
  apiGet: vi.fn((url: string) =>
    url === '/api/me/labor-contracts' ? Promise.resolve({ items: state.items }) : Promise.resolve(null),
  ),
  downloadFile: vi.fn((url: string) => {
    state.downloads.push(url)
    return Promise.resolve()
  }),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiPut: vi.fn(),
  apiDelete: vi.fn(),
  httpClient: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
}))

function row(overrides: Partial<MyLaborContract> = {}): MyLaborContract {
  return {
    id: 5,
    code: 'HDLD005',
    contract_no: 'HD-05/2026',
    company_name: 'DEGO',
    contract_type: 2,
    status: 2,
    effective_status: 2,
    sign_date: '2026-01-05',
    start_date: '2026-01-01',
    end_date: '2026-12-31',
    terminated_date: null,
    job_title: 'Chuyên viên thu mua',
    base_salary: 15000000,
    has_generated_file: true,
    has_signed_file: true,
    ...overrides,
  }
}

function renderTab() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <ProfileLaborContractsTab />
    </QueryClientProvider>,
  )
}

describe('ProfileLaborContractsTab', () => {
  beforeEach(() => {
    state.items = []
    state.downloads = []
  })

  it('hiện danh sách: số HĐ, chức danh, trạng thái, lương và hai nút tải khi có đủ tệp', async () => {
    state.items = [row()]
    renderTab()
    expect(await screen.findByText('HD-05/2026')).toBeInTheDocument()
    expect(screen.getByText('Chuyên viên thu mua')).toBeInTheDocument()
    expect(screen.getByText('Đã ký – hiệu lực')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Tải bản mềm \(\.docx\)/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Xem \/ tải bản đã ký/ })).toBeInTheDocument()
  })

  it('chỉ đọc: không có nút sửa / sinh tệp / chuyển trạng thái / xóa', async () => {
    state.items = [row()]
    renderTab()
    await screen.findByText('HD-05/2026')
    for (const name of [/Sửa/, /Sinh tệp/, /Xóa/, /Chuyển/, /Lập hợp đồng/, /Tải lên/]) {
      expect(screen.queryByRole('button', { name })).not.toBeInTheDocument()
    }
  })

  it('nút theo tệp có sẵn: thiếu bản ký thì ẩn nút bản ký', async () => {
    state.items = [row({ has_signed_file: false })]
    renderTab()
    await screen.findByText('HD-05/2026')
    expect(screen.getByRole('button', { name: /Tải bản mềm/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /bản đã ký/ })).not.toBeInTheDocument()
  })

  it('không có tệp nào thì báo «Chưa có tệp»', async () => {
    state.items = [row({ has_generated_file: false, has_signed_file: false })]
    renderTab()
    expect(await screen.findByText('Chưa có tệp')).toBeInTheDocument()
  })

  it('bấm nút gọi đúng đường tải của «của tôi»', async () => {
    state.items = [row()]
    renderTab()
    const user = userEvent.setup()
    await user.click(await screen.findByRole('button', { name: /Tải bản mềm/ }))
    await waitFor(() => expect(state.downloads).toContain('/api/me/labor-contracts/5/document'))
    await user.click(screen.getByRole('button', { name: /bản đã ký/ }))
    await waitFor(() => expect(state.downloads).toContain('/api/me/labor-contracts/5/signed-file'))
  })

  it('hết hạn hiện nhãn «Hết hạn»', async () => {
    state.items = [row({ effective_status: 3 })]
    renderTab()
    expect(await screen.findByText('Hết hạn')).toBeInTheDocument()
  })

  it('trống thì hiện câu rỗng', async () => {
    renderTab()
    expect(await screen.findByText('Bạn chưa có hợp đồng lao động nào đã ký.')).toBeInTheDocument()
  })
})
