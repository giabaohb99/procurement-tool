import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { MemoryRouter, useLocation } from 'react-router-dom'

import type { EmployeeWorkHistory } from '../types/employee-work-history'
import { EmployeeWorkHistoryDecisionSection } from './employee-work-history-decision-section'

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
    decision_date: '2026-01-01',
    note: '',
    applied_at: null,
    file_count: 0,
    is_current: true,
    can_apply: true,
    ...overrides,
  }
}

/** Hiện query hiện tại — xác nhận lựa chọn Bảng/Dòng thời gian nằm trên URL. */
function WhereAmI() {
  const location = useLocation()
  return <output data-testid="where">{location.search}</output>
}

function renderSection(items: EmployeeWorkHistory[], extraProps: Partial<Parameters<typeof EmployeeWorkHistoryDecisionSection>[0]> = {}) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <EmployeeWorkHistoryDecisionSection
          items={items}
          canOpenFiles
          onOpenFiles={vi.fn()}
          storageKey="test.decisions"
          {...extraProps}
        />
        <WhereAmI />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('EmployeeWorkHistoryDecisionSection', () => {
  it('chỉ hiện dòng có decision_no, bỏ qua dòng không có — dù cùng một nguồn items', () => {
    renderSection([
      row({ id: 1, decision_no: 'QD-01', position_label: 'Trưởng phòng A' }),
      row({ id: 2, decision_no: '', position_label: 'Không có QĐ' }),
    ])

    expect(screen.getByText('QD-01')).toBeInTheDocument()
    expect(screen.queryByText('Không có QĐ')).not.toBeInTheDocument()
  })

  it('danh sách rỗng → câu gợi ý ngắn, không phải câu lỗi chung', () => {
    renderSection([])

    expect(
      screen.getByText('Chưa có quyết định nào — ghi số QĐ khi thêm dòng quá trình công tác.'),
    ).toBeInTheDocument()
  })

  it('toggle Bảng → Dòng thời gian: đổi hiển thị VÀ ghi vào URL param decView', async () => {
    renderSection([row({ id: 1, decision_no: 'QD-02' })])

    //  Mặc định «Bảng»: bảng dùng cấu trúc <table>, không có <ol> dòng thời gian.
    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(screen.getByTestId('where')).not.toHaveTextContent('decView')

    await userEvent.click(screen.getByRole('radio', { name: 'Dòng thời gian' }))

    expect(screen.queryByRole('table')).not.toBeInTheDocument()
    expect(screen.getByTestId('where')).toHaveTextContent('decView=timeline')
  })

  it('canOpenFiles=false + có tệp → chữ tĩnh, không nút xem/tải (cả hai dạng)', async () => {
    renderSection([row({ id: 1, decision_no: 'QD-03', file_count: 1 })], { canOpenFiles: false })

    expect(screen.getByText('Có 1 tệp đính kèm')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^1$/ })).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('radio', { name: 'Dòng thời gian' }))
    expect(screen.getByText('Có 1 tệp đính kèm')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^1$/ })).not.toBeInTheDocument()
  })

  it('KHÔNG có nút Sửa/Xóa/Áp ở cả hai dạng — khu này không nhận actions', async () => {
    renderSection([row({ id: 1, decision_no: 'QD-04', can_apply: true })])

    expect(screen.queryByRole('button', { name: 'Sửa' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Áp vào hồ sơ' })).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('radio', { name: 'Dòng thời gian' }))
    expect(screen.queryByRole('button', { name: 'Sửa' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Áp vào hồ sơ' })).not.toBeInTheDocument()
  })

  it('một phần tử → hiện đúng một dòng ở cả hai dạng', async () => {
    renderSection([row({ id: 1, decision_no: 'QD-05' })])

    expect(screen.getByText('QD-05')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('radio', { name: 'Dòng thời gian' }))
    expect(screen.getByText('Số QĐ: QD-05')).toBeInTheDocument()
  })
})

describe('EmployeeWorkHistoryDecisionSection — nút gợi ý «Thêm ở tab Quá trình công tác» (tách tab, đại ca chốt 03/10/2026)', () => {
  it('rỗng + có onAddInWorkHistoryClick → hiện nút, bấm vào gọi đúng handler', async () => {
    const onAddInWorkHistoryClick = vi.fn()
    renderSection([], { onAddInWorkHistoryClick })

    const button = screen.getByRole('button', { name: 'Thêm ở tab Quá trình công tác' })
    await userEvent.click(button)

    expect(onAddInWorkHistoryClick).toHaveBeenCalledTimes(1)
  })

  it('rỗng + KHÔNG truyền onAddInWorkHistoryClick (vd thẻ Trang cá nhân /me) → KHÔNG hiện nút', () => {
    renderSection([])
    expect(screen.queryByRole('button', { name: 'Thêm ở tab Quá trình công tác' })).not.toBeInTheDocument()
  })

  it('CÓ dòng rồi (không rỗng) → KHÔNG hiện nút dù có handler', () => {
    renderSection([row({ id: 1, decision_no: 'QD-06' })], { onAddInWorkHistoryClick: vi.fn() })
    expect(screen.queryByRole('button', { name: 'Thêm ở tab Quá trình công tác' })).not.toBeInTheDocument()
  })

  it('đang tải → KHÔNG hiện nút dù rỗng và có handler (tránh nhấp nháy trước khi biết thật sự rỗng)', () => {
    renderSection([], { onAddInWorkHistoryClick: vi.fn(), isLoading: true })
    expect(screen.queryByRole('button', { name: 'Thêm ở tab Quá trình công tác' })).not.toBeInTheDocument()
  })
})
