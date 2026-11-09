import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { JobPositionRoleCard } from './job-position-role-card'

describe('JobPositionRoleCard', () => {
  it('bày tên và mã; bấm bỏ gọi đúng hàm', async () => {
    const onRemove = vi.fn()
    render(<JobPositionRoleCard name="Trưởng phòng" code="dept_head" onRemove={onRemove} />)

    expect(screen.getByText('Trưởng phòng')).toBeInTheDocument()
    expect(screen.getByText('dept_head')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Bỏ vai trò Trưởng phòng khỏi gói' }))
    expect(onRemove).toHaveBeenCalledTimes(1)
  })

  //  Màn chi tiết chức vụ có biểu mẫu: nút thiếu type mặc định là submit, bấm bỏ là lưu cả form (bẫy biểu mẫu thứ ba).
  it('nút bỏ là type="button"', () => {
    render(<JobPositionRoleCard name="X" code="x" onRemove={vi.fn()} />)
    expect(screen.getByRole('button')).toHaveAttribute('type', 'button')
  })

  it('không truyền onRemove thì không có nút; mã rỗng thì không có dòng phụ', () => {
    const { container } = render(<JobPositionRoleCard name="#9" code="" />)
    expect(screen.queryByRole('button')).toBeNull()
    expect(container.querySelectorAll('p')).toHaveLength(1)
  })
})
