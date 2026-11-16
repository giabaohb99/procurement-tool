import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { validateShiftRows, type ShiftRow } from '../utils/work-shift-rows'
import { WorkShiftSegmentRows } from './work-shift-segment-rows'

/*  Danh sách khung của hộp xếp ca (bản làm lại duoc-CR-761): trần 12 khung có câu lý do, xóa bằng nút biểu tượng có tên
    đọc được, và không còn giờ trống thì nút thêm cũng tắt kèm lý do (nút tắt mà im lặng là thứ đại ca chê). */

function renderRows(rows: ShiftRow[], onChange = vi.fn()) {
  render(<WorkShiftSegmentRows rows={rows} onChange={onChange} validation={validateShiftRows(rows)} />)
  return onChange
}

const hourly = (count: number, from = 0): ShiftRow[] =>
  Array.from({ length: count }, (_, i) => ({ id: `r${i}`, start: from + i, end: from + i + 1 }))

describe('WorkShiftSegmentRows', () => {
  it('stops at 12 rows and says why instead of a silent disabled button', () => {
    renderRows(hourly(12))
    expect(screen.getByRole('button', { name: /Thêm khung giờ/ })).toBeDisabled()
    expect(screen.getByText('Đã đủ 12 khung giờ — tối đa một ngày.')).toBeInTheDocument()
  })

  it('a full day in fewer than 12 rows also disables adding, with its own reason', () => {
    renderRows([{ id: 'a', start: 0, end: 24 }])
    expect(screen.getByRole('button', { name: /Thêm khung giờ/ })).toBeDisabled()
    expect(screen.getByText('Không còn giờ trống trong ngày để thêm khung.')).toBeInTheDocument()
  })

  it('the icon-only delete button is named after its row and removes exactly that row', () => {
    const rows = hourly(3, 8)
    const onChange = renderRows(rows)
    fireEvent.click(screen.getByRole('button', { name: 'Xóa khung 2' }))
    expect(onChange).toHaveBeenCalledWith([rows[0], rows[2]])
  })

  it('an empty list tells the user how to start, and adding offers the 08:00 hour first', () => {
    const onChange = renderRows([])
    expect(screen.getByText('Chưa có khung giờ nào — thêm khung hoặc chọn mẫu nhanh.')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Thêm khung giờ/ }))
    expect(onChange).toHaveBeenCalledWith([expect.objectContaining({ start: 8, end: 9 })])
  })

  it('marks the broken row and links its error message to both hour pickers', () => {
    renderRows([
      { id: 'a', start: 8, end: 12 },
      { id: 'b', start: 10, end: 14 },
    ])
    const start = screen.getByRole('combobox', { name: 'Khung 2 — từ giờ' })
    expect(start).toHaveAttribute('aria-invalid', 'true')
    expect(start).toHaveAccessibleDescription('Trùng giờ với khung 1.')
    expect(screen.getByRole('combobox', { name: 'Khung 2 — đến giờ' })).toHaveTextContent('14:00')
  })
})
