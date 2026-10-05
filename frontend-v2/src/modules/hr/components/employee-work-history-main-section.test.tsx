import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import type { EmployeeWorkHistoryRowActions } from '../config/employee-work-history-columns'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import { EmployeeWorkHistoryMainSection } from './employee-work-history-main-section'

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
    is_current: true,
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

function WhereAmI() {
  const location = useLocation()
  return <output data-testid="where">{location.search}</output>
}

function renderSection(
  items: EmployeeWorkHistory[],
  extraProps: Partial<Parameters<typeof EmployeeWorkHistoryMainSection>[0]> = {},
) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <EmployeeWorkHistoryMainSection
          items={items}
          emptyMessage="Chưa có dòng quá trình công tác nào."
          canOpenFiles
          onOpenFiles={vi.fn()}
          storageKey="test.main"
          {...extraProps}
        />
        <WhereAmI />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('EmployeeWorkHistoryMainSection', () => {
  it('hiện MỌI dòng, kể cả dòng không có decision_no (khác khu Quyết định)', () => {
    renderSection([row({ id: 1, decision_no: '', position_label: 'Không QĐ' })])
    expect(screen.getByText('Không QĐ')).toBeInTheDocument()
  })

  it('toggle Bảng → Dòng thời gian: đổi hiển thị VÀ ghi vào URL param whView', async () => {
    renderSection([row({ id: 1 })])

    expect(screen.getByRole('table')).toBeInTheDocument()

    await userEvent.click(screen.getByRole('radio', { name: 'Dòng thời gian' }))

    expect(screen.queryByRole('table')).not.toBeInTheDocument()
    expect(screen.getByTestId('where')).toHaveTextContent('whView=timeline')
  })

  it('dòng thời gian sắp mới nhất trước, có «Hiện tại»', async () => {
    renderSection([
      row({ id: 1, from_date: '2020-01-01', is_current: false }),
      row({ id: 2, from_date: '2026-06-01', is_current: true }),
    ])

    await userEvent.click(screen.getByRole('radio', { name: 'Dòng thời gian' }))

    expect(screen.getAllByText('Hiện tại')).toHaveLength(1)
    const dates = screen.getAllByText(/→/)
    expect(dates[0]).toHaveTextContent('01/06/2026')
  })

  it('actions bỏ trống (chỉ đọc, /me) → KHÔNG nút Sửa/Xóa/Áp ở CẢ HAI dạng', async () => {
    renderSection([row({ id: 1, can_apply: true })])

    expect(screen.queryByRole('button', { name: 'Sửa' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Áp vào hồ sơ' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Xóa' })).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('radio', { name: 'Dòng thời gian' }))
    expect(screen.queryByRole('button', { name: 'Sửa' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Áp vào hồ sơ' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Xóa' })).not.toBeInTheDocument()
  })

  it('actions truyền vào → bảng có cột Thao tác, bấm Sửa gọi đúng handler', async () => {
    const actions = buildActions()
    const target = row({ id: 9 })
    renderSection([target], { actions })

    await userEvent.click(screen.getByRole('button', { name: 'Sửa' }))
    expect(actions.onEdit).toHaveBeenCalledWith(target)
  })

  it('onAddClick bỏ trống → KHÔNG nút «Thêm dòng»; truyền vào → có nút và gọi đúng handler', async () => {
    const onAddClick = vi.fn()
    renderSection([row({ id: 1 })], { onAddClick })

    const button = screen.getByRole('button', { name: /Thêm dòng/ })
    await userEvent.click(button)
    expect(onAddClick).toHaveBeenCalledTimes(1)
  })

  it('không có onAddClick → không nút Thêm dòng', () => {
    renderSection([row({ id: 1 })])
    expect(screen.queryByRole('button', { name: /Thêm dòng/ })).not.toBeInTheDocument()
  })

  it('danh sách rỗng + onCreateFromProfileClick → hiện nút «Tạo dòng đầu từ hồ sơ»', () => {
    renderSection([], { onCreateFromProfileClick: vi.fn() })
    expect(screen.getByRole('button', { name: 'Tạo dòng đầu từ hồ sơ' })).toBeInTheDocument()
  })

  it('CÓ dòng rồi (không rỗng) → KHÔNG hiện nút «Tạo dòng đầu từ hồ sơ» dù có handler', () => {
    renderSection([row({ id: 1 })], { onCreateFromProfileClick: vi.fn() })
    expect(screen.queryByRole('button', { name: 'Tạo dòng đầu từ hồ sơ' })).not.toBeInTheDocument()
  })

  it('canOpenFiles=false → chữ tĩnh, không nút xem/tải ở cả hai dạng', async () => {
    renderSection([row({ id: 1, file_count: 4 })], { canOpenFiles: false })

    expect(screen.getByText('Có 4 tệp đính kèm')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^4$/ })).not.toBeInTheDocument()

    await userEvent.click(screen.getByRole('radio', { name: 'Dòng thời gian' }))
    expect(screen.getByText('Có 4 tệp đính kèm')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^4$/ })).not.toBeInTheDocument()
  })
})

/**
 * Gộp hàng điều khiển thành MỘT HÀNG (đại ca chê hai hàng rời rạc, 03/10/2026):
 * tiêu đề + toggle đi qua `toolbar` của `DataTable`, «Thêm dòng» đi qua
 * `toolbarEnd` (sau menu «Cột»), Tải lại tự dựng lại ở chế độ Dòng thời gian.
 */
describe('EmployeeWorkHistoryMainSection — gộp thanh điều khiển một hàng', () => {
  it('chế độ Bảng: có Tải lại + Cột + Thêm dòng, Thêm dòng đứng SAU Cột, không có Xóa lọc', () => {
    renderSection([row({ id: 1 })], { onAddClick: vi.fn() })

    expect(screen.getByRole('button', { name: 'Tải lại dữ liệu' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Cột' })).toBeInTheDocument()
    //  «Xóa lọc» chỉ nên hiện khi THẬT SỰ có bộ lọc — khu này không có bộ lọc
    //  nào, chỉ có `whView` (không phải lọc), nên dù `toolbar` nay đã khai
    //  (trước đây trống, chưa từng gặp nhánh này) thì nút đó vẫn phải ẩn.
    expect(screen.queryByRole('button', { name: 'Xóa lọc' })).not.toBeInTheDocument()

    const buttons = Array.from(document.querySelectorAll('button')).map((b) => b.textContent)
    const addIndex = buttons.findIndex((t) => t?.includes('Thêm dòng'))
    const columnsIndex = buttons.findIndex((t) => t?.includes('Cột'))
    expect(addIndex).toBeGreaterThan(columnsIndex)
  })

  it('chế độ Dòng thời gian: vẫn có Tải lại, KHÔNG có menu Cột, không Xóa lọc', async () => {
    renderSection([row({ id: 1 })], { onAddClick: vi.fn() })

    await userEvent.click(screen.getByRole('radio', { name: 'Dòng thời gian' }))

    expect(screen.getByRole('button', { name: 'Tải lại dữ liệu' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Cột' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Xóa lọc' })).not.toBeInTheDocument()
    //  Nút Thêm dòng vẫn phải còn — chuyển qua dòng thời gian không phải mất quyền ghi.
    expect(screen.getByRole('button', { name: /Thêm dòng/ })).toBeInTheDocument()
  })

  it('bấm Tải lại ở chế độ Dòng thời gian gọi đúng onRefresh truyền từ cha', async () => {
    const onRefresh = vi.fn().mockResolvedValue(undefined)
    renderSection([row({ id: 1 })], { onRefresh })

    await userEvent.click(screen.getByRole('radio', { name: 'Dòng thời gian' }))
    await userEvent.click(screen.getByRole('button', { name: 'Tải lại dữ liệu' }))

    expect(onRefresh).toHaveBeenCalledTimes(1)
  })
})
