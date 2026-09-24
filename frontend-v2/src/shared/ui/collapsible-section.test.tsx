import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'

import { CollapsibleSection } from './collapsible-section'

const BODY = 'nội dung bên trong'

function renderSection(props: Partial<Parameters<typeof CollapsibleSection>[0]> = {}) {
  return render(
    <CollapsibleSection title="Khối thử" {...props}>
      <p>{BODY}</p>
    </CollapsibleSection>,
  )
}

/** Thân khối có đang bị `hidden` không — `toBeVisible` bắt được `display:none`. */
function bodyIsShown() {
  return screen.getByText(BODY)
}

beforeEach(() => {
  localStorage.clear()
})

describe('CollapsibleSection — dựng thân', () => {
  it('LUÔN dựng thân kể cả khi gập, chỉ ẩn bằng CSS', () => {
    //  ⚠️ LỖI ĐÃ TRÁNH: hủy mount thân thì ô nhập gắn luật qua `useController`
    //  bị gỡ đăng ký, luật chặn submit biến mất theo, và người dùng lưu được
    //  một bộ dữ liệu sai mà không có gì báo. Đây là lý do tệp này tồn tại thay
    //  vì dùng thẳng `Collapsible` của Radix — xóa bài này là mất cái chốt đó.
    renderSection({ defaultOpen: false })
    expect(bodyIsShown()).toBeInTheDocument()
    expect(bodyIsShown()).not.toBeVisible()
  })

  it('mở thì thân nhìn thấy được', () => {
    renderSection({ defaultOpen: true })
    expect(bodyIsShown()).toBeVisible()
  })
})

describe('nút tiêu đề', () => {
  it('là `type="button"` — trong `<form>` mà thiếu thì bấm gập là LƯU cả biểu mẫu', () => {
    //  Bẫy thứ ba của duoc-CR-317. HTML mặc định `type="submit"`.
    renderSection()
    expect(screen.getByRole('button')).toHaveAttribute('type', 'button')
  })

  it('bấm thì đảo trạng thái và `aria-expanded` đi theo', async () => {
    const user = userEvent.setup()
    renderSection({ defaultOpen: true })
    const button = screen.getByRole('button')

    expect(button).toHaveAttribute('aria-expanded', 'true')
    await user.click(button)
    expect(button).toHaveAttribute('aria-expanded', 'false')
    expect(bodyIsShown()).not.toBeVisible()
  })
})

describe('tóm tắt', () => {
  it('chỉ hiện khi GẬP — lúc mở thì nội dung đã nói rồi', async () => {
    const user = userEvent.setup()
    renderSection({ defaultOpen: false, summary: '4 trường' })
    expect(screen.getByText('4 trường')).toBeInTheDocument()

    await user.click(screen.getByRole('button'))
    expect(screen.queryByText('4 trường')).not.toBeInTheDocument()
  })

  it('câu mô tả thì ngược lại — chỉ hiện khi MỞ', async () => {
    const user = userEvent.setup()
    renderSection({ defaultOpen: true, description: 'giải thích dài' })
    expect(screen.getByText('giải thích dài')).toBeInTheDocument()

    await user.click(screen.getByRole('button'))
    expect(screen.queryByText('giải thích dài')).not.toBeInTheDocument()
  })
})

describe('mặc định CÒN SỐNG cho tới khi người dùng tự quyết', () => {
  it('`defaultOpen` đổi sau lượt vẽ đầu thì khối đi theo', () => {
    //  ⚠️ LỖI ĐÃ TRÁNH: bản đầu chốt `defaultOpen` vào `useState`, nên nó được
    //  tính trên dữ liệu RỖNG của lượt vẽ đầu (bản ghi còn đang nạp). Hậu quả:
    //  khối «Điều kiện áp dụng» của một hồ sơ đã khai đầy đủ vẫn gập sẵn mãi
    //  mãi, vì `useState` không đọc lại khi dữ liệu về.
    const { rerender } = render(
      <CollapsibleSection title="Khối thử" defaultOpen={false}>
        <p>{BODY}</p>
      </CollapsibleSection>,
    )
    expect(bodyIsShown()).not.toBeVisible()

    rerender(
      <CollapsibleSection title="Khối thử" defaultOpen={true}>
        <p>{BODY}</p>
      </CollapsibleSection>,
    )
    expect(bodyIsShown()).toBeVisible()
  })

  it('nhưng NGƯỜI DÙNG đã bấm thì mặc định thôi có tiếng nói', async () => {
    const user = userEvent.setup()
    const { rerender } = render(
      <CollapsibleSection title="Khối thử" defaultOpen={false}>
        <p>{BODY}</p>
      </CollapsibleSection>,
    )
    await user.click(screen.getByRole('button'))
    expect(bodyIsShown()).toBeVisible()

    //  Dữ liệu về, `defaultOpen` thành `false` — không được giật khối đóng lại
    //  dưới tay người đang đọc nó.
    rerender(
      <CollapsibleSection title="Khối thử" defaultOpen={false}>
        <p>{BODY}</p>
      </CollapsibleSection>,
    )
    expect(bodyIsShown()).toBeVisible()
  })
})

describe('nhớ trạng thái', () => {
  it('bản lưu THẮNG mặc định', () => {
    localStorage.setItem('erp.section.thu', '0')
    renderSection({ storageKey: 'thu', defaultOpen: true })
    expect(bodyIsShown()).not.toBeVisible()
  })

  it('ghi lại đúng khóa có tiền tố khi người dùng bấm', async () => {
    const user = userEvent.setup()
    renderSection({ storageKey: 'thu', defaultOpen: true })
    await user.click(screen.getByRole('button'))
    expect(localStorage.getItem('erp.section.thu')).toBe('0')
  })

  it('không khai `storageKey` thì KHÔNG ghi gì cả', async () => {
    const user = userEvent.setup()
    renderSection({ defaultOpen: true })
    await user.click(screen.getByRole('button'))
    expect(localStorage.length).toBe(0)
  })

  it('giá trị rác trong bộ nhớ không làm khối hỏng', () => {
    //  `'true'`, `'{}'` … đều không phải `'1'` nên đọc ra ĐÓNG. Miễn là không nổ.
    localStorage.setItem('erp.section.thu', 'rác')
    renderSection({ storageKey: 'thu', defaultOpen: true })
    expect(bodyIsShown()).not.toBeVisible()
  })
})

describe('ép mở', () => {
  it('`forceOpen` thắng cả bản lưu — vì câu báo lỗi đang nằm trong đó', async () => {
    //  Ô sai trong khối gập = bấm Lưu không thấy gì xảy ra (bẫy thứ nhất
    //  duoc-CR-317). Có lỗi thì phải banh khối ra, bất kể người dùng đã gập.
    localStorage.setItem('erp.section.thu', '0')
    renderSection({ storageKey: 'thu', forceOpen: true })
    expect(bodyIsShown()).toBeVisible()
    expect(screen.getByRole('button')).toHaveAttribute('aria-expanded', 'true')
  })

  it('hết lỗi thì trả lại đúng trạng thái người dùng đã chọn', () => {
    localStorage.setItem('erp.section.thu', '0')
    const { rerender } = render(
      <CollapsibleSection title="Khối thử" storageKey="thu" forceOpen>
        <p>{BODY}</p>
      </CollapsibleSection>,
    )
    expect(bodyIsShown()).toBeVisible()

    rerender(
      <CollapsibleSection title="Khối thử" storageKey="thu" forceOpen={false}>
        <p>{BODY}</p>
      </CollapsibleSection>,
    )
    expect(bodyIsShown()).not.toBeVisible()
  })
})
