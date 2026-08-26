import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'

import { FilterResetButton, type FilterResetButtonProps } from './filter-reset-button'

/** Hiện query string ra DOM để khẳng định được URL sau khi bấm. */
function UrlProbe() {
  const location = useLocation()
  return <span data-testid="url">{location.search}</span>
}

function build(url: string, props: FilterResetButtonProps = {}) {
  return render(
    <MemoryRouter initialEntries={[url]}>
      <FilterResetButton {...props} />
      <UrlProbe />
    </MemoryRouter>,
  )
}

const nut = () => screen.queryByRole('button', { name: /xóa lọc/i })

describe('FilterResetButton', () => {
  it('chưa lọc gì thì KHÔNG mọc thêm nút trên thanh công cụ', () => {
    build('/hr/employees')
    expect(nut()).not.toBeInTheDocument()
  })

  it('có param lọc trên URL thì hiện nút', () => {
    build('/hr/employees?status=active')
    expect(nut()).toBeInTheDocument()
  })

  it('bấm là quét sạch mọi param lọc, kể cả ô tìm kiếm và điều kiện nâng cao', async () => {
    const nguoi = userEvent.setup()
    build('/hr/employees?q=nguyen&status=active&full_name__contains=an&conjunction=or')

    await nguoi.click(screen.getByRole('button', { name: /xóa lọc/i }))

    expect(screen.getByTestId('url')).toHaveTextContent('')
    expect(nut()).not.toBeInTheDocument()
  })

  it('GIỮ tab đang mở và thứ tự sắp xếp — hai thứ đó không phải bộ lọc', async () => {
    //  Xóa lọc mà nhảy tab là mất luôn chỗ đang đứng (Văn bản đến/đi, Thông báo).
    const nguoi = userEvent.setup()
    build('/documents?tab=den&sort_by=code&sort_dir=desc&status=draft')

    await nguoi.click(screen.getByRole('button', { name: /xóa lọc/i }))

    const url = screen.getByTestId('url').textContent ?? ''
    const params = new URLSearchParams(url)
    expect(params.get('tab')).toBe('den')
    expect(params.get('sort_by')).toBe('code')
    expect(params.get('sort_dir')).toBe('desc')
    expect(params.get('status')).toBeNull()
  })

  it('chỉ có tab / sắp xếp thì coi như chưa lọc, không hiện nút', () => {
    build('/documents?tab=den&sort_by=code&sort_dir=asc')
    expect(nut()).not.toBeInTheDocument()
  })

  it('param rỗng (`?status=`) không tính là đang lọc', () => {
    build('/hr/employees?status=')
    expect(nut()).not.toBeInTheDocument()
  })

  it('trang tự lo bộ lọc thì bảng gọi hàm của trang và KHÔNG đụng vào URL', async () => {
    //  Bảng con trong trang chi tiết giữ bộ lọc bằng state cục bộ, mà URL lúc đó
    //  là của trang cha — quét sạch nó là phá trang cha.
    const nguoi = userEvent.setup()
    const reset = vi.fn()
    build('/production/suppliers/7?tab=surveys', { active: true, onReset: reset })

    await nguoi.click(screen.getByRole('button', { name: /xóa lọc/i }))

    expect(reset).toHaveBeenCalledTimes(1)
    expect(screen.getByTestId('url')).toHaveTextContent('tab=surveys')
  })

  it('trang khai `active={false}` thì ẩn nút dù URL có param', () => {
    build('/production/suppliers/7?tab=surveys', { active: false, onReset: vi.fn() })
    expect(nut()).not.toBeInTheDocument()
  })
})
