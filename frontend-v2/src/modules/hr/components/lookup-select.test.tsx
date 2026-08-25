import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { LookupSelect } from './lookup-select'

const DANH_SACH = [
  { id: 5, label: 'DEMO_MANAGER — Trưởng bộ phận' },
  { id: 7, label: 'DEMONV — Nhân viên' },
]

describe('LookupSelect', () => {
  //  Lỗi khách báo 24/08/2026: chọn trưởng bộ phận (hoặc phòng ban của nhân sự),
  //  bấm Lưu, ô trở lại «— Chưa chỉ định —» và dữ liệu mất thật trên máy chủ.
  //
  //  Radix dựng thêm một `<select>` nguyên bản ẩn. Danh mục nạp bất đồng bộ nên
  //  có nhịp `value` đã là 5 mà `<option value="5">` chưa sinh ra; trình duyệt
  //  thấy không option nào khớp thì kéo về rỗng và bắn `change` — Radix chuyển
  //  tiếp thành `onValueChange("")`. `Number("")` = 0 ghi đè trường trong form,
  //  lần Lưu kế tiếp gửi 0 xuống và xóa thật.
  it('bỏ qua giá trị RỖNG do thẻ select ẩn của Radix bắn ra, không ghi đè trường', () => {
    const doi = vi.fn()

    //  Thẻ `<select>` ẩn chỉ được Radix dựng khi ô nằm TRONG một form — cũng
    //  đúng bối cảnh thật: cả hai màn dính lỗi đều là form chi tiết.
    render(
      <form>
        <LookupSelect value={5} onChange={doi} items={[]} placeholder="Chọn nhân sự" />
      </form>,
    )

    //  Mô phỏng đúng nhịp hỏng: thẻ select ẩn bắn `change` với chuỗi rỗng.
    const an = document.querySelector('select')
    expect(an).not.toBeNull()
    fireEvent.change(an as HTMLSelectElement, { target: { value: '' } })

    expect(doi).not.toHaveBeenCalled()
  })

  it('người dùng chọn mục «bỏ chọn» thì VẪN báo 0 — đừng chặn nhầm', () => {
    const doi = vi.fn()

    render(
      <form>
        <LookupSelect
          value={5}
          onChange={doi}
          items={DANH_SACH}
          placeholder="Chọn nhân sự"
          emptyLabel="— Chưa chỉ định —"
        />
      </form>,
    )

    const an = document.querySelector('select') as HTMLSelectElement
    fireEvent.change(an, { target: { value: '0' } })

    expect(doi).toHaveBeenCalledWith(0)
  })

  it('giá trị đang lưu KHÔNG có trong danh sách thì vẫn hiện tên, không hiện trống', () => {
    //  Ca thật: trưởng bộ phận thuộc pháp nhân khác nên bị lọc khỏi ô chọn.
    render(
      <LookupSelect
        value={99}
        onChange={vi.fn()}
        items={DANH_SACH}
        placeholder="Chọn nhân sự"
        emptyLabel="— Chưa chỉ định —"
        fallbackLabel="Trưởng phòng Thu mua (Demo)"
      />,
    )

    expect(screen.getByText('Trưởng phòng Thu mua (Demo)')).toBeInTheDocument()
  })

  it('không có nhãn dự phòng thì hiện #id — vẫn hơn là một ô trống', () => {
    render(
      <LookupSelect value={99} onChange={vi.fn()} items={DANH_SACH} placeholder="Chọn nhân sự" />,
    )

    expect(screen.getByText('#99')).toBeInTheDocument()
  })
})
