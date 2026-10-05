import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { EmployeeWorkHistoryRowActions } from '../config/employee-work-history-columns'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import { EmployeeWorkHistoryTimeline } from './employee-work-history-timeline'

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
    decision_no: '',
    decision_date: null,
    note: '',
    applied_at: null,
    file_count: 0,
    is_current: false,
    can_apply: true,
    ...overrides,
  }
}

function buildActions(overrides: Partial<EmployeeWorkHistoryRowActions> = {}): EmployeeWorkHistoryRowActions {
  return {
    onEdit: vi.fn(),
    onApply: vi.fn(),
    onDelete: vi.fn(),
    isApplying: () => false,
    isDeleting: () => false,
    ...overrides,
  }
}

describe('EmployeeWorkHistoryTimeline', () => {
  it('danh sách rỗng → hiện câu nhắc truyền vào, không dựng <ol>', () => {
    render(
      <EmployeeWorkHistoryTimeline
        items={[]}
        variant="history"
        canOpenFiles
        onOpenFiles={vi.fn()}
        emptyMessage="Chưa có dòng nào."
      />,
    )

    expect(screen.getByText('Chưa có dòng nào.')).toBeInTheDocument()
    expect(screen.queryByRole('list')).not.toBeInTheDocument()
  })

  it('một phần tử → dựng đúng một mốc, không lỗi', () => {
    render(
      <EmployeeWorkHistoryTimeline
        items={[row({ id: 1 })]}
        variant="history"
        canOpenFiles
        onOpenFiles={vi.fn()}
        emptyMessage="rỗng"
      />,
    )

    expect(screen.getAllByText('01/01/2026 → nay')).toHaveLength(1)
  })

  it('sắp mốc mới nhất lên TRƯỚC, không tin thứ tự items truyền vào', () => {
    render(
      <EmployeeWorkHistoryTimeline
        items={[row({ id: 1, from_date: '2024-01-01' }), row({ id: 2, from_date: '2026-06-01' })]}
        variant="history"
        canOpenFiles
        onOpenFiles={vi.fn()}
        emptyMessage="rỗng"
      />,
    )

    const headers = screen.getAllByText(/→/)
    expect(headers[0]).toHaveTextContent('01/06/2026')
    expect(headers[1]).toHaveTextContent('01/01/2024')
  })

  it('dòng is_current=true → có huy hiệu «Hiện tại», false thì không', () => {
    render(
      <EmployeeWorkHistoryTimeline
        items={[row({ id: 1, is_current: true }), row({ id: 2, from_date: '2020-01-01', is_current: false })]}
        variant="history"
        canOpenFiles
        onOpenFiles={vi.fn()}
        emptyMessage="rỗng"
      />,
    )

    expect(screen.getAllByText('Hiện tại')).toHaveLength(1)
  })

  it('variant="decision" → ngày chính là decision_date, không phải from_date', () => {
    render(
      <EmployeeWorkHistoryTimeline
        items={[row({ from_date: '2026-05-01', decision_date: '2026-04-20' })]}
        variant="decision"
        canOpenFiles
        onOpenFiles={vi.fn()}
        emptyMessage="rỗng"
      />,
    )

    expect(screen.getByText('20/04/2026')).toBeInTheDocument()
    expect(screen.queryByText(/01\/05\/2026/)).not.toBeInTheDocument()
  })

  it('canOpenFiles=false + có tệp → chỉ chữ tĩnh, KHÔNG nút xem/tải', () => {
    render(
      <EmployeeWorkHistoryTimeline
        items={[row({ file_count: 3 })]}
        variant="history"
        canOpenFiles={false}
        onOpenFiles={vi.fn()}
        emptyMessage="rỗng"
      />,
    )

    expect(screen.getByText('Có 3 tệp đính kèm')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^3$/ })).not.toBeInTheDocument()
  })

  it('canOpenFiles=true + có tệp → nút mở tệp gọi onOpenFiles với đúng dòng', async () => {
    const onOpenFiles = vi.fn()
    const target = row({ id: 42, file_count: 2 })
    render(
      <EmployeeWorkHistoryTimeline
        items={[target]}
        variant="history"
        canOpenFiles
        onOpenFiles={onOpenFiles}
        emptyMessage="rỗng"
      />,
    )

    await userEvent.click(screen.getByRole('button', { name: '2' }))
    expect(onOpenFiles).toHaveBeenCalledWith(target)
  })

  it('actions bỏ trống (chỉ đọc) → KHÔNG có nút Sửa/Áp/Xóa, kể cả can_apply=true', () => {
    render(
      <EmployeeWorkHistoryTimeline
        items={[row({ can_apply: true })]}
        variant="history"
        canOpenFiles
        onOpenFiles={vi.fn()}
        emptyMessage="rỗng"
      />,
    )

    expect(screen.queryByRole('button', { name: 'Sửa' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Áp vào hồ sơ' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Xóa' })).not.toBeInTheDocument()
  })

  it('actions truyền vào → Sửa/Xóa gọi đúng handler với đúng dòng; Áp chỉ hiện khi can_apply', async () => {
    const actions = buildActions()
    const target = row({ id: 7, can_apply: false })
    render(
      <EmployeeWorkHistoryTimeline
        items={[target]}
        variant="history"
        canOpenFiles
        onOpenFiles={vi.fn()}
        actions={actions}
        emptyMessage="rỗng"
      />,
    )

    expect(screen.queryByRole('button', { name: 'Áp vào hồ sơ' })).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('button', { name: 'Sửa' }))
    expect(actions.onEdit).toHaveBeenCalledWith(target)

    await userEvent.click(screen.getByRole('button', { name: 'Xóa' }))
    await userEvent.click(screen.getByRole('button', { name: 'Đồng ý' }))
    expect(actions.onDelete).toHaveBeenCalledWith(target)
  })

  it('số QĐ + ghi chú chỉ hiện khi có giá trị, không để dòng trống', () => {
    render(
      <EmployeeWorkHistoryTimeline
        items={[row({ decision_no: 'QD-09', note: 'Ghi chú ngắn' })]}
        variant="history"
        canOpenFiles
        onOpenFiles={vi.fn()}
        emptyMessage="rỗng"
      />,
    )

    expect(screen.getByText('Số QĐ: QD-09')).toBeInTheDocument()
    expect(screen.getByText('Ghi chú ngắn')).toBeInTheDocument()
  })
})
