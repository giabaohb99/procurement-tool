import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { BookingDateTimePicker } from './booking-date-time-picker'

/** Gõ số vào MỘT cụm (Ngày/Tháng/Năm/Giờ/Phút) — mỗi cụm sửa độc lập. */
function typeSeg(label: string, value: string) {
  fireEvent.change(screen.getByLabelText(label), { target: { value } })
}

function fill(da: string, mo: string, y: string, h: string, mi: string) {
  typeSeg('Ngày', da)
  typeSeg('Tháng', mo)
  typeSeg('Năm', y)
  typeSeg('Giờ', h)
  typeSeg('Phút', mi)
}

describe('BookingDateTimePicker', () => {
  it('phát ra yyyy-MM-ddTHH:mm khi nhập đủ và hợp lệ', () => {
    const onChange = vi.fn()
    render(<BookingDateTimePicker value="" onChange={onChange} />)
    fill('08', '09', '2026', '16', '30')
    expect(onChange).toHaveBeenLastCalledWith('2026-09-08T16:30')
  })

  it('gõ vào cụm nào chỉ đổi cụm đó, không đụng cụm khác', () => {
    render(<BookingDateTimePicker value="2026-09-08T16:30" onChange={() => {}} />)
    typeSeg('Giờ', '09') // chỉ đổi giờ
    expect((screen.getByLabelText('Ngày') as HTMLInputElement).value).toBe('08')
    expect((screen.getByLabelText('Tháng') as HTMLInputElement).value).toBe('09')
    expect((screen.getByLabelText('Giờ') as HTMLInputElement).value).toBe('09')
  })

  it('cảnh báo khi giờ vượt 23 và phút vượt 59', () => {
    const { rerender } = render(<BookingDateTimePicker value="" onChange={() => {}} />)
    typeSeg('Giờ', '25')
    expect(screen.getByText(/Giờ 0–23/)).toBeInTheDocument()
    rerender(<BookingDateTimePicker value="" onChange={() => {}} />)
    typeSeg('Phút', '60')
    expect(screen.getByText(/Phút 0–59/)).toBeInTheDocument()
  })

  it('cảnh báo khi ngày vượt 31 và tháng vượt 12', () => {
    const { rerender } = render(<BookingDateTimePicker value="" onChange={() => {}} />)
    typeSeg('Ngày', '35')
    expect(screen.getByText(/Ngày 1–31/)).toBeInTheDocument()
    rerender(<BookingDateTimePicker value="" onChange={() => {}} />)
    typeSeg('Tháng', '13')
    expect(screen.getByText(/Tháng 1–12/)).toBeInTheDocument()
  })

  it('ngày không có thật (31/02) — cảnh báo và KHÔNG phát giá trị', () => {
    const onChange = vi.fn()
    render(<BookingDateTimePicker value="" onChange={onChange} />)
    fill('31', '02', '2026', '08', '00')
    expect(screen.getByText(/không có thật/)).toBeInTheDocument()
    expect(onChange).toHaveBeenLastCalledWith('')
  })

  it('cảnh báo khi sớm hơn min (chặn quá khứ)', () => {
    render(<BookingDateTimePicker value="" min="2026-09-10T08:00" onChange={() => {}} />)
    fill('08', '09', '2026', '07', '00') // trước mốc
    expect(screen.getByText(/Không được ở quá khứ/)).toBeInTheDocument()
  })
})
