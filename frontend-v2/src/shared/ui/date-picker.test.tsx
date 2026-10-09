// duoc-CR-612 — bấm lại đúng ngày đang chọn: lịch «bỏ chọn». Ô có nút ✕ thì KHÔNG được coi đó
// là xóa ngày — ô ngày trong bảng Báo cáo thực hiện lưu ngay khi đổi, xóa nhầm là ghi xuống DB.
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { DatePicker } from './date-picker'

function openAndClickDay(day: string) {
  fireEvent.click(screen.getByRole('button', { name: /15\/10\/2026|Chọn ngày/ }))
  fireEvent.click(screen.getByRole('button', { name: new RegExp(`\\b${day}\\b.*October|October.*\\b${day}\\b|tháng 10.*\\b${day}\\b|\\b${day}\\b.*tháng 10`, 'i') }))
}

describe('DatePicker re-clicking the selected day', () => {
  it('keeps the date when the picker has a clear button', () => {
    const onChange = vi.fn()
    render(<DatePicker clearable value="2026-10-15" onChange={onChange} />)
    openAndClickDay('15')
    expect(onChange).not.toHaveBeenCalled()
  })

  it('still lets the clear button wipe the date', () => {
    const onChange = vi.fn()
    render(<DatePicker clearable value="2026-10-15" onChange={onChange} />)
    fireEvent.pointerDown(screen.getByRole('button', { name: 'Xóa ngày' }))
    expect(onChange).toHaveBeenCalledWith('')
  })

  it('still picks a different day normally', () => {
    const onChange = vi.fn()
    render(<DatePicker clearable value="2026-10-15" onChange={onChange} />)
    openAndClickDay('20')
    expect(onChange).toHaveBeenCalledWith('2026-10-20')
  })
})
