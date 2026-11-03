import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { CrudTabDraftProvider } from '@/shared/crud'
import { LeavePolicyLinesCard } from './leave-policy-lines-card'

const apiGet = vi.fn()
const apiPut = vi.fn()
vi.mock('@/core/api', () => ({
  apiGet: (...a: unknown[]) => apiGet(...a),
  apiPut: (...a: unknown[]) => apiPut(...a),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
  extractErrorMessage: () => 'lỗi',
  httpClient: {},
}))
vi.mock('sonner', () => ({ toast: { success: vi.fn(), error: vi.fn() } }))

let granted = new Set<string>()
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string, action: string) => granted.has(`${entity}.${action}`) }),
}))

const TYPES = {
  total: 5,
  items: [
    { id: 1, name: 'Phép năm', counts_balance: true, is_compensatory: false, is_active: true },
    { id: 2, name: 'Không lương', counts_balance: false, is_compensatory: false, is_active: true },
    { id: 3, name: 'Nghỉ bù', counts_balance: true, is_compensatory: true, is_active: true },
    { id: 4, name: 'Phép cũ', counts_balance: true, is_compensatory: false, is_active: false },
    { id: 5, name: 'Phép thâm niên', counts_balance: true, is_compensatory: false, is_active: true },
  ],
}

function renderCard() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <LeavePolicyLinesCard policyId={8} />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  granted = new Set(['leave_type.read', 'leave_type.write'])
  apiGet.mockReset().mockImplementation((url: string) =>
    Promise.resolve(
      url === '/api/leave-types'
        ? TYPES
        : { total: 1, items: [{ id: 30, leave_type_id: 4, annual_days: 10 }] },
    ),
  )
  apiPut.mockReset().mockImplementation((_url: string, body: { items: unknown[] }) =>
    Promise.resolve({ total: body.items.length, items: body.items }),
  )
})

describe('LeavePolicyLinesCard (duoc-CR-717)', () => {
  it('offers only active, balance-counting, non-compensatory types — but still names an existing line of an inactive type', async () => {
    const user = userEvent.setup()
    renderCard()
    //  Dòng cũ của loại đã ngừng vẫn ra TÊN, không ra "#4".
    expect(await screen.findByText('Phép cũ')).toBeInTheDocument()
    await user.click(screen.getByRole('combobox', { name: 'Loại nghỉ' }))
    const options = (await screen.findAllByRole('option')).map((o) => o.textContent)
    expect(options).toEqual(['Phép năm', 'Phép thâm niên'])
  })

  it('overwrites a duplicate type in the draft and PUTs the whole list once on Save', async () => {
    const user = userEvent.setup()
    renderCard()
    await screen.findByText('Phép cũ')
    const save = screen.getByRole('button', { name: 'Lưu số ngày' })
    expect(save).toBeDisabled()

    const days = screen.getByLabelText('Số ngày mỗi năm')
    await user.click(screen.getByRole('combobox', { name: 'Loại nghỉ' }))
    await user.click(await screen.findByRole('option', { name: 'Phép năm' }))
    await user.clear(days)
    await user.type(days, '12')
    await user.click(screen.getByRole('button', { name: 'Thêm dòng' }))
    //  Cùng loại lần nữa với số khác → GHI ĐÈ, không thêm dòng thứ hai.
    await user.clear(days)
    await user.type(days, '15{Enter}')

    const list = screen.getByRole('list')
    expect(within(list).getAllByRole('listitem')).toHaveLength(2)
    expect(within(list).getByText('15 ngày/năm')).toBeInTheDocument()

    await user.click(save)
    await waitFor(() => expect(apiPut).toHaveBeenCalledTimes(1))
    expect(apiPut).toHaveBeenCalledWith('/api/leave-policies/8/lines', {
      items: [
        { leave_type_id: 4, annual_days: 10 },
        { leave_type_id: 1, annual_days: 15 },
      ],
    })
  })

  it('rejects an off-step number with a visible message instead of sending it', async () => {
    const user = userEvent.setup()
    renderCard()
    await screen.findByText('Phép cũ')
    await user.click(screen.getByRole('combobox', { name: 'Loại nghỉ' }))
    await user.click(await screen.findByRole('option', { name: 'Phép năm' }))
    const days = screen.getByLabelText('Số ngày mỗi năm')
    await user.clear(days)
    await user.type(days, '12.25')
    await user.click(screen.getByRole('button', { name: 'Thêm dòng' }))
    expect(screen.getByText(/bước 0,5/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Lưu số ngày' })).toBeDisabled()
  })

  it('is read-only without leave_type.write: no add row, no remove buttons, no save', async () => {
    granted = new Set(['leave_type.read'])
    renderCard()
    await screen.findByText('Phép cũ')
    expect(screen.queryByRole('button', { name: 'Thêm dòng' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Bỏ / })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Lưu số ngày' })).not.toBeInTheDocument()
  })

  it('refuses an empty day count with "Nhập số ngày" instead of silently adding a 0-day line (review M3)', async () => {
    //  LỖI REVIEW M3: ô `type=number` + `Number('')` = 0 → bấm Thêm với ô rỗng thêm dòng "0 ngày/năm".
    const user = userEvent.setup()
    renderCard()
    await screen.findByText('Phép cũ')
    await user.click(screen.getByRole('combobox', { name: 'Loại nghỉ' }))
    await user.click(await screen.findByRole('option', { name: 'Phép năm' }))
    await user.clear(screen.getByLabelText('Số ngày mỗi năm'))
    await user.click(screen.getByRole('button', { name: 'Thêm dòng' }))
    expect(screen.getByText(/Nhập số ngày/)).toBeInTheDocument()
    expect(within(screen.getByRole('list')).getAllByRole('listitem')).toHaveLength(1)
    expect(screen.getByRole('button', { name: 'Lưu số ngày' })).toBeDisabled()
  })

  it('accepts the Vietnamese decimal comma "12,5" (review M3)', async () => {
    const user = userEvent.setup()
    renderCard()
    await screen.findByText('Phép cũ')
    await user.click(screen.getByRole('combobox', { name: 'Loại nghỉ' }))
    await user.click(await screen.findByRole('option', { name: 'Phép năm' }))
    const days = screen.getByLabelText('Số ngày mỗi năm')
    await user.clear(days)
    await user.type(days, '12,5{Enter}')
    expect(await screen.findByText('12,5 ngày/năm')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Lưu số ngày' }))
    await waitFor(() =>
      expect(apiPut).toHaveBeenCalledWith('/api/leave-policies/8/lines', {
        items: [
          { leave_type_id: 4, annual_days: 10 },
          { leave_type_id: 1, annual_days: 12.5 },
        ],
      }),
    )
  })

  it('keeps the unsaved draft when the tab is unmounted and mounted again, and says so (review M4)', async () => {
    //  LỖI REVIEW M4: Radix hủy mount tab ẩn → sang "Thông tin" rồi quay lại là mất dòng vừa thêm.
    const user = userEvent.setup()
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
    const view = (mounted: boolean) => (
      <QueryClientProvider client={client}>
        <CrudTabDraftProvider>{mounted && <LeavePolicyLinesCard policyId={8} />}</CrudTabDraftProvider>
      </QueryClientProvider>
    )
    const { rerender } = render(view(true))
    await screen.findByText('Phép cũ')
    expect(screen.queryByText('Có thay đổi chưa lưu')).not.toBeInTheDocument()
    await user.click(screen.getByRole('combobox', { name: 'Loại nghỉ' }))
    await user.click(await screen.findByRole('option', { name: 'Phép năm' }))
    await user.type(screen.getByLabelText('Số ngày mỗi năm'), '{Enter}')
    expect(await screen.findByText('Có thay đổi chưa lưu')).toBeInTheDocument()

    rerender(view(false))
    expect(screen.queryByText('Phép năm')).not.toBeInTheDocument()
    rerender(view(true))
    expect(await screen.findByText('12 ngày/năm')).toBeInTheDocument()
    expect(screen.getByText('Có thay đổi chưa lưu')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Lưu số ngày' })).toBeEnabled()

    //  Lưu xong thì nháp bỏ, dấu "chưa lưu" tắt.
    await user.click(screen.getByRole('button', { name: 'Lưu số ngày' }))
    await waitFor(() => expect(screen.queryByText('Có thay đổi chưa lưu')).not.toBeInTheDocument())
  })
})
