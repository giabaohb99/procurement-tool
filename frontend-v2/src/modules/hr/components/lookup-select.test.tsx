import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { LookupSelect } from './lookup-select'

const DANH_SACH = [
  { id: 5, label: 'DEMO_MANAGER — Trưởng bộ phận' },
  { id: 7, label: 'DEMONV — Nhân viên' },
]

describe('LookupSelect', () => {
  //  Lỗi khách báo 24/08/2026: chọn trưởng bộ phận (hoặc phòng ban của nhân sự),
  //  bấm Lưu, ô trở lại "— Chưa chỉ định —" và dữ liệu mất thật trên máy chủ. Gốc
  //  lỗi là thẻ `<select>` ẩn của Radix tự bắn chuỗi rỗng khi danh mục về muộn.
  //  duoc-CR-747 chuyển sang `SearchSelect` (không có thẻ ẩn) — bài này canh để
  //  không ai đưa một ô chọn tự-bắn-change quay lại.
  it('does not call onChange by itself when the catalog arrives after the value (old Radix data-loss bug)', () => {
    const doi = vi.fn()
    const { rerender } = render(
      <form>
        <LookupSelect value={5} onChange={doi} items={[]} placeholder="Chọn nhân sự" />
      </form>,
    )
    rerender(
      <form>
        <LookupSelect value={5} onChange={doi} items={DANH_SACH} placeholder="Chọn nhân sự" />
      </form>,
    )
    expect(document.querySelector('select')).toBeNull()
    expect(doi).not.toHaveBeenCalled()
    expect(screen.getByText('DEMO_MANAGER — Trưởng bộ phận')).toBeInTheDocument()
  })

  it('still reports 0 when the user picks the "unassign" item', async () => {
    const user = userEvent.setup()
    const doi = vi.fn()
    render(
      <LookupSelect
        value={5}
        onChange={doi}
        items={DANH_SACH}
        placeholder="Chọn nhân sự"
        emptyLabel="— Chưa chỉ định —"
      />,
    )
    await user.click(screen.getByRole('combobox'))
    await user.click(await screen.findByText('— Chưa chỉ định —'))
    expect(doi).toHaveBeenCalledWith(0)
  })

  it('filters the list by typing, ignoring Vietnamese diacritics', async () => {
    const user = userEvent.setup()
    const doi = vi.fn()
    render(<LookupSelect value={0} onChange={doi} items={DANH_SACH} placeholder="Chọn nhân sự" />)
    await user.click(screen.getByRole('combobox'))
    await user.type(screen.getByPlaceholderText('Gõ để tìm…'), 'nhan vien')
    expect(screen.queryByText('DEMO_MANAGER — Trưởng bộ phận')).not.toBeInTheDocument()
    await user.click(screen.getByText('DEMONV — Nhân viên'))
    expect(doi).toHaveBeenCalledWith(7)
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
