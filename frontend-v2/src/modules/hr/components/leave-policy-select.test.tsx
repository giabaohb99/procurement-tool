import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { LeavePolicySelect } from './leave-policy-select'

let granted = new Set<string>()
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string, action: string) => granted.has(`${entity}.${action}`) }),
}))

const POLICIES = [{ id: 7, code: 'CS-CHUAN', name: 'Chính sách tiêu chuẩn' }]

function renderSelect(props: Partial<Parameters<typeof LeavePolicySelect>[0]> = {}) {
  const onChange = vi.fn()
  render(
    <MemoryRouter>
      <LeavePolicySelect id="p" policies={[]} isLoading={false} value={0} onChange={onChange} {...props} />
    </MemoryRouter>,
  )
  return onChange
}

describe('LeavePolicySelect', () => {
  beforeEach(() => {
    granted = new Set()
  })

  // Lỗi đã gặp 11/11/2026: hệ chưa có chính sách nào, ô vẫn mời "Chọn chính sách đang dùng" rồi mở ra
  // trống trơn, người dùng tưởng ô hỏng.
  it('says there is no active policy and disables the select when the list is empty', () => {
    granted = new Set(['leave_type.write'])
    renderSelect()
    expect(screen.getByText('Chưa có chính sách nào đang dùng')).toBeInTheDocument()
    expect(screen.getByRole('combobox')).toBeDisabled()
    expect(screen.getByRole('link', { name: 'Thiết lập › Chính sách nghỉ phép' })).toHaveAttribute(
      'href',
      '/hr/leave-policies',
    )
  })

  it('tells users without leave_type.write to ask HR instead of linking to a screen they cannot open', () => {
    granted = new Set(['leave_balance.write', 'leave_type.read'])
    renderSelect()
    expect(screen.getByText(/Nhờ quản trị nhân sự tạo chính sách/)).toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })

  it('does not claim the list is empty while it is still loading', () => {
    renderSelect({ isLoading: true })
    expect(screen.queryByText('Chưa có chính sách nào đang dùng')).not.toBeInTheDocument()
    expect(screen.getByRole('combobox')).toBeEnabled()
  })

  it('lets the user pick a policy when the list has items', async () => {
    const user = userEvent.setup()
    const onChange = renderSelect({ policies: POLICIES })
    expect(screen.queryByText(/Chưa có chính sách/)).not.toBeInTheDocument()
    await user.click(screen.getByRole('combobox'))
    await user.click(await screen.findByRole('option', { name: 'Chính sách tiêu chuẩn (CS-CHUAN)' }))
    expect(onChange).toHaveBeenCalledWith(7)
  })
})
