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

    expect(screen.getByText('Chưa có quyết định nào.')).toBeInTheDocument()
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

describe('EmployeeWorkHistoryDecisionSection — nút «+ Thêm quyết định» (mục 3, đại ca chốt 03/10/2026)', () => {
  it('rỗng + có onAddClick → hiện CẢ nút ở thanh công cụ LẪN nút gợi ý giữa khu, bấm nút nào cũng gọi đúng handler', async () => {
    const onAddClick = vi.fn()
    renderSection([], { onAddClick })

    //  Rỗng → có 2 nút cùng tên: toolbarEnd (luôn hiện) + gợi ý giữa khu (chỉ rỗng).
    const buttons = screen.getAllByRole('button', { name: /Thêm quyết định/ })
    expect(buttons).toHaveLength(2)
    await userEvent.click(buttons[0])

    expect(onAddClick).toHaveBeenCalledTimes(1)
  })

  it('rỗng + KHÔNG truyền onAddClick (vd thẻ Trang cá nhân /me) → KHÔNG hiện nút nào', () => {
    renderSection([])
    expect(screen.queryByRole('button', { name: /Thêm quyết định/ })).not.toBeInTheDocument()
  })

  it('CÓ dòng rồi (không rỗng) → vẫn hiện nút Ở THANH CÔNG CỤ (khác nút gợi ý giữa khu, chỉ ẨN khi rỗng)', () => {
    renderSection([row({ id: 1, decision_no: 'QD-06' })], { onAddClick: vi.fn() })
    //  Đúng MỘT nút «Thêm quyết định» (toolbarEnd) — nút gợi ý giữa khu chỉ hiện lúc rỗng.
    expect(screen.getAllByRole('button', { name: /Thêm quyết định/ })).toHaveLength(1)
  })

  it('đang tải → KHÔNG hiện nút gợi ý giữa khu dù rỗng và có handler (tránh nhấp nháy)', () => {
    renderSection([], { onAddClick: vi.fn(), isLoading: true })
    //  `DataTable` tự dựng Skeleton nên nút toolbarEnd vẫn còn — chỉ chặn RIÊNG
    //  nút gợi ý giữa khu (đi theo trạng thái rỗng-đã-biết, không phải đang tải).
    expect(screen.getAllByRole('button', { name: /Thêm quyết định/ })).toHaveLength(1)
  })

  it('chế độ Dòng thời gian: nút «+ Thêm quyết định» đứng cạnh Tải lại ở hàng công cụ', async () => {
    const onAddClick = vi.fn()
    renderSection([row({ id: 1, decision_no: 'QD-09' })], { onAddClick })

    await userEvent.click(screen.getByRole('radio', { name: 'Dòng thời gian' }))
    const button = screen.getByRole('button', { name: /Thêm quyết định/ })
    await userEvent.click(button)

    expect(onAddClick).toHaveBeenCalledTimes(1)
  })
})

/**
 * Gộp hàng điều khiển thành MỘT HÀNG (đại ca chê hai hàng rời rạc, 03/10/2026).
 * Khu này KHÔNG có nút «Thêm dòng» (chỉ đọc) — khác khu Quá trình công tác.
 */
describe('EmployeeWorkHistoryDecisionSection — gộp thanh điều khiển một hàng', () => {
  it('chế độ Bảng: có Tải lại + Cột, không Thêm dòng, không Xóa lọc', () => {
    renderSection([row({ id: 1, decision_no: 'QD-07' })])

    expect(screen.getByRole('button', { name: 'Tải lại dữ liệu' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cột' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Thêm dòng/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Xóa lọc' })).not.toBeInTheDocument()
  })

  it('chế độ Dòng thời gian: vẫn có Tải lại, KHÔNG có menu Cột, không Xóa lọc', async () => {
    renderSection([row({ id: 1, decision_no: 'QD-08' })])

    await userEvent.click(screen.getByRole('radio', { name: 'Dòng thời gian' }))

    expect(screen.getByRole('button', { name: 'Tải lại dữ liệu' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Cột' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Xóa lọc' })).not.toBeInTheDocument()
  })
})
