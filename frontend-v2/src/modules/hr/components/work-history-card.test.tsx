import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { EmployeeWorkHistoryRowActions } from '../config/employee-work-history-columns'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import { WorkHistoryCard } from './work-history-card'

const TODAY = '2026-11-05'

function row(overrides: Partial<EmployeeWorkHistory> = {}): EmployeeWorkHistory {
  return {
    id: 1,
    employee_id: 1,
    event_type: 3,
    from_date: '2026-01-01',
    to_date: null,
    company_id: 10,
    company_name: 'DEGO',
    department_id: 20,
    department_name: 'Phòng KD',
    position_id: 30,
    position_label: 'Trưởng phòng',
    decision_no: '12/QĐ-DG',
    decision_date: '2025-12-20',
    note: '',
    applied_at: null,
    file_count: 0,
    is_current: true,
    can_apply: true,
    ...overrides,
  }
}

function buildActions(): EmployeeWorkHistoryRowActions {
  return {
    onEdit: vi.fn(),
    onApply: vi.fn(),
    onDelete: vi.fn(),
    isApplying: () => false,
    isDeleting: () => false,
  }
}

function renderCard(props: Partial<Parameters<typeof WorkHistoryCard>[0]> = {}) {
  return render(
    <WorkHistoryCard
      row={row()}
      variant="history"
      canOpenFiles
      onOpenFiles={vi.fn()}
      today={TODAY}
      {...props}
    />,
  )
}

describe('WorkHistoryCard — khu Quá trình công tác', () => {
  it('dòng đầu là loại sự kiện + nhãn hiệu lực; số QĐ ở dòng phụ; có tóm tắt và khoảng ngày', () => {
    renderCard()
    expect(screen.getByText('Bổ nhiệm')).toBeInTheDocument()
    expect(screen.getByText('Đang hiệu lực')).toBeInTheDocument()
    expect(screen.getByText('QĐ 12/QĐ-DG')).toBeInTheDocument()
    expect(screen.getByText('Phòng KD · Trưởng phòng · DEGO')).toBeInTheDocument()
    expect(screen.getByText('Từ 01/01/2026')).toBeInTheDocument()
  })

  //  Lượt rà mã duoc-CR-721: bản đầu chỉ in ngày ký BÊN TRONG nhánh có số QĐ, dòng nhập bù có ngày ký mà
  //  thiếu số QĐ thì thẻ rơi mất ngày đó trong khi bảng vẫn có cột Ngày ký QĐ.
  it('giữ ngày ký QĐ khi dòng không có số QĐ', () => {
    renderCard({ row: row({ decision_no: '' }) })
    expect(screen.getByText('Ký 20/12/2025')).toBeInTheDocument()
    expect(screen.queryByText(/^QĐ /)).not.toBeInTheDocument()
  })

  //  Nhập bù dòng cũ: to_date rỗng nhưng đã bị dòng chính mới hơn thay — bảng hiện "—", thẻ không được nói "Đang hiệu lực".
  it('dòng không ngày kết thúc nhưng đã bị thay thì không có nhãn hiệu lực nào', () => {
    renderCard({ row: row({ is_current: false }) })
    expect(screen.queryByText('Đang hiệu lực')).toBeNull()
    expect(screen.queryByText('Chưa hiệu lực')).toBeNull()
  })

  it('dòng tương lai nói "Chưa hiệu lực"; dòng có ngày kết thúc bày đủ hai đầu', () => {
    const { unmount } = renderCard({ row: row({ is_current: false, from_date: '2027-01-01' }) })
    expect(screen.getByText('Chưa hiệu lực')).toBeInTheDocument()
    unmount()
    renderCard({ row: row({ to_date: '2026-06-30', is_current: false }) })
    expect(screen.getByText('01/01/2026 – 30/06/2026')).toBeInTheDocument()
  })

  it('có actions: Sửa / Áp gọi đúng hàm; không áp được thì không có nút Áp', async () => {
    const user = userEvent.setup()
    const actions = buildActions()
    const { unmount } = renderCard({ actions })
    await user.click(screen.getByRole('button', { name: 'Sửa dòng' }))
    await user.click(screen.getByRole('button', { name: 'Áp vào hồ sơ' }))
    expect(actions.onEdit).toHaveBeenCalledTimes(1)
    expect(actions.onApply).toHaveBeenCalledTimes(1)
    unmount()
    renderCard({ actions, row: row({ can_apply: false }) })
    expect(screen.queryByRole('button', { name: 'Áp vào hồ sơ' })).toBeNull()
  })

  it('không có actions (Trang cá nhân) thì không có nút Sửa / Áp / Xóa', () => {
    renderCard()
    expect(screen.queryByRole('button')).toBeNull()
  })

  //  Luật A9/Q4 của bảng: có tệp mà không có quyền thì chỉ báo số tệp, không có nút mở.
  it('tệp: có quyền thì có nút mở, thiếu quyền chỉ báo số tệp', async () => {
    const user = userEvent.setup()
    const onOpenFiles = vi.fn()
    const { unmount } = renderCard({ row: row({ file_count: 2 }), onOpenFiles })
    await user.click(screen.getByRole('button', { name: '2' }))
    expect(onOpenFiles).toHaveBeenCalledTimes(1)
    unmount()
    renderCard({ row: row({ file_count: 2 }), canOpenFiles: false })
    expect(screen.getByText('Có 2 tệp đính kèm')).toBeInTheDocument()
    expect(screen.queryByRole('button')).toBeNull()
  })
})

describe('WorkHistoryCard — khu Quyết định bổ nhiệm', () => {
  it('dòng đầu là SỐ QĐ, dòng phụ là loại + ngày ký, cuối là ngày hiệu lực; không nhãn hiệu lực', () => {
    renderCard({ variant: 'decision' })
    expect(screen.getByText('12/QĐ-DG')).toBeInTheDocument()
    expect(screen.getByText('Bổ nhiệm · Ký 20/12/2025')).toBeInTheDocument()
    expect(screen.getByText('Hiệu lực từ 01/01/2026')).toBeInTheDocument()
    expect(screen.queryByText('Đang hiệu lực')).toBeNull()
  })

  it('QĐ chưa ghi ngày ký thì chỉ còn tên loại, không in "Ký" trống', () => {
    renderCard({ variant: 'decision', row: row({ decision_date: null }) })
    expect(screen.getByText('Bổ nhiệm')).toBeInTheDocument()
    expect(screen.queryByText(/Ký/)).toBeNull()
  })
})
