import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { DataTableColumn } from '@/shared/data-table'
import type { LeaveBalance } from '../types/leave'
import {
  flattenLeaveBalanceGroups,
  groupLeaveBalances,
  type LeaveBalanceRow,
} from '../utils/group-leave-balances'
import { buildLeaveBalanceColumns } from './leave-balance-columns'

function makeBalance(overrides: Partial<LeaveBalance> = {}): LeaveBalance {
  return {
    id: 1,
    employee_id: 1,
    employee_name: 'Trần Chí Dũng',
    year: 2026,
    leave_type_id: 1,
    leave_type_name: 'Phép năm',
    company_id: 1,
    allocated_days: 0,
    seniority_days: 0,
    carried_days: 0,
    adjusted_days: 0,
    used_days: 0,
    pending_days: 0,
    carried_out_days: 0,
    carried_expired_days: 0,
    note: '',
    total_days: 0,
    remaining_days: 0,
    ...overrides,
  }
}

function column(
  columns: DataTableColumn<LeaveBalanceRow>[],
  key: string,
): DataTableColumn<LeaveBalanceRow> {
  const found = columns.find((c) => c.key === key)
  if (!found) throw new Error(`Không có cột "${key}"`)
  return found
}

describe('buildLeaveBalanceColumns', () => {
  it('bày sẵn đúng năm cột, sáu cột giải thích ẩn sẵn', () => {
    //  ⚠️ Đây là lý do tồn tại của lần bố trí lại 19/09/2026: bản cũ bày cả
    //  mười một cột và ở màn 1600px thứ bị đẩy ra ngoài mép phải chính là
    //  «Còn lại» — con số duy nhất người ta mở màn này để xem. Thêm cột vào
    //  nhóm bày sẵn thì phải đo lại bề ngang trước.
    const columns = buildLeaveBalanceColumns({ expanded: new Set(), onToggle: vi.fn() })
    const shown = columns.filter((c) => !c.defaultHidden).map((c) => c.key)

    expect(shown).toEqual([
      'employee_name',
      'total_days',
      'used_days',
      'pending_days',
      'remaining_days',
    ])
    expect(columns.filter((c) => c.defaultHidden)).toHaveLength(6)
  })

  it('cột «Nhân sự» không khai bề rộng cứng nên nó nuốt chỗ thừa', () => {
    //  Khai số cứng thì phần dư chia ĐỀU cho cả năm cột: mỗi cột số phình gần
    //  190px và con số nằm cách tiêu đề của chính nó một gang tay.
    const columns = buildLeaveBalanceColumns({ expanded: new Set(), onToggle: vi.fn() })
    expect(column(columns, 'employee_name').width).toBeUndefined()
  })

  it('người một loại nghỉ: tên kèm loại nghỉ cùng dòng, KHÔNG có nút bung', () => {
    const groups = groupLeaveBalances([makeBalance()])
    const [row] = flattenLeaveBalanceGroups(groups, new Set())
    const columns = buildLeaveBalanceColumns({ expanded: new Set(), onToggle: vi.fn() })

    render(<>{column(columns, 'employee_name').cell(row)}</>)

    expect(screen.getByText('Trần Chí Dũng')).toBeTruthy()
    expect(screen.getByText('· Phép năm')).toBeTruthy()
    expect(screen.queryByRole('button')).toBeNull()
  })

  it('người nhiều loại nghỉ: hàng nhóm có nút bung, hàng con bày tên loại nghỉ', async () => {
    const onToggle = vi.fn()
    const groups = groupLeaveBalances([
      makeBalance({ id: 1 }),
      makeBalance({ id: 2, leave_type_id: 7, leave_type_name: 'Nghỉ bù' }),
    ])
    const rows = flattenLeaveBalanceGroups(groups, new Set([1]))
    const columns = buildLeaveBalanceColumns({ expanded: new Set([1]), onToggle })
    const nameCell = column(columns, 'employee_name')

    const { rerender } = render(<>{nameCell.cell(rows[0])}</>)
    expect(screen.getByText('· 2 loại nghỉ')).toBeTruthy()

    const toggle = screen.getByRole('button')
    expect(toggle.getAttribute('aria-expanded')).toBe('true')
    await userEvent.click(toggle)
    expect(onToggle).toHaveBeenCalledWith(1)

    rerender(<>{nameCell.cell(rows[2])}</>)
    expect(screen.getByText('Nghỉ bù')).toBeTruthy()
    //  Hàng con KHÔNG lặp lại tên người — cột đã có tên ở hàng cha ngay trên.
    expect(screen.queryByText('Trần Chí Dũng')).toBeNull()
  })

  it('hàng nhóm bày TỔNG, hàng con bày số của chính loại nghỉ đó', () => {
    const groups = groupLeaveBalances([
      makeBalance({ id: 1, total_days: 12, used_days: 3, remaining_days: 9 }),
      makeBalance({ id: 2, leave_type_id: 7, total_days: 2, used_days: 0, remaining_days: 2 }),
    ])
    const rows = flattenLeaveBalanceGroups(groups, new Set([1]))
    const columns = buildLeaveBalanceColumns({ expanded: new Set([1]), onToggle: vi.fn() })
    const remaining = column(columns, 'remaining_days')

    const { rerender } = render(<>{remaining.cell(rows[0])}</>)
    expect(screen.getByText('11')).toBeTruthy()

    rerender(<>{remaining.cell(rows[1])}</>)
    expect(screen.getByText('9')).toBeTruthy()
  })

  it('«0 còn lại» chỉ tô đỏ khi CÓ quỹ mà tiêu hết, không tô cho loại vốn không cấp', () => {
    //  Loại nghỉ không hạn mức (tang chế, cưới hỏi, nghỉ bù) luôn còn 0 và
    //  chiếm phần lớn số dòng. Tô đỏ hết thì màu đỏ mất nghĩa đúng chỗ nó cần
    //  có nghĩa nhất.
    const columns = buildLeaveBalanceColumns({ expanded: new Set(), onToggle: vi.fn() })
    const remaining = column(columns, 'remaining_days')

    const usedUp = flattenLeaveBalanceGroups(
      groupLeaveBalances([makeBalance({ allocated_days: 12, used_days: 12, remaining_days: 0 })]),
      new Set(),
    )[0]
    const neverHadQuota = flattenLeaveBalanceGroups(
      groupLeaveBalances([makeBalance({ leave_type_name: 'Nghỉ tang chế' })]),
      new Set(),
    )[0]

    const { container, rerender } = render(<>{remaining.cell(usedUp)}</>)
    expect(container.querySelector('.text-destructive')).toBeTruthy()

    rerender(<>{remaining.cell(neverHadQuota)}</>)
    expect(container.querySelector('.text-destructive')).toBeNull()
  })

  it('số 0 vẽ thành dấu gạch mờ, trừ cột «Còn lại»', () => {
    //  Bảy cột số mà bốn cột hầu như luôn 0; in "0" ra hết thì cả bảng đặc số
    //  và mắt không nhặt ra được ô nào thật sự có giá trị. Riêng «Còn lại» thì
    //  0 nghĩa là HẾT PHÉP — đúng thứ phải đập vào mắt.
    const columns = buildLeaveBalanceColumns({ expanded: new Set(), onToggle: vi.fn() })
    const [row] = flattenLeaveBalanceGroups(groupLeaveBalances([makeBalance()]), new Set())

    const { container, rerender } = render(<>{column(columns, 'used_days').cell(row)}</>)
    expect(container.textContent).toBe('—')

    rerender(<>{column(columns, 'remaining_days').cell(row)}</>)
    expect(container.textContent).toBe('0')
  })
})
