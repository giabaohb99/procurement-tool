import { fireEvent, render, screen } from '@testing-library/react'
import { Ban } from 'lucide-react'
import { describe, expect, it, vi } from 'vitest'

import { ConfirmIconButton } from './confirm-icon-button'

describe('ConfirmIconButton', () => {
  //  Lỗi người dùng chỉ ra 25/08/2026: thẻ «Quyền truy cập» nằm TRONG thẻ
  //  `<form>` thông tin văn bản, mà `<button>` không ghi type thì mặc định là
  //  submit. Bấm biểu tượng thu hồi, hộp xác nhận mới vừa hiện ra thôi mà toast
  //  «Cập nhật văn bản» đã nhảy — form đã bị gửi đi trước cả khi người dùng
  //  đồng ý thu hồi.
  it('nằm trong form mà bấm thì KHÔNG gửi form, chỉ mở hộp xác nhận', () => {
    const guiForm = vi.fn((event: { preventDefault: () => void }) => event.preventDefault())

    render(
      <form onSubmit={guiForm}>
        <ConfirmIconButton
          icon={Ban}
          title="Thu hồi"
          confirmTitle="Thu hồi quyền của Lý Phó Phòng?"
          onConfirm={vi.fn()}
        />
      </form>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Thu hồi' }))

    expect(guiForm).not.toHaveBeenCalled()
    expect(screen.getByText('Thu hồi quyền của Lý Phó Phòng?')).toBeInTheDocument()
  })

  it('bấm nút xác nhận trong hộp mới chạy việc', () => {
    const chay = vi.fn()

    render(
      <ConfirmIconButton
        icon={Ban}
        title="Thu hồi"
        confirmTitle="Thu hồi quyền?"
        confirmLabel="Thu hồi"
        onConfirm={chay}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Thu hồi' }))
    expect(chay).not.toHaveBeenCalled()

    //  Mở hộp rồi thì có hai nút cùng tên: nút biểu tượng ngoài bảng và nút xác
    //  nhận trong hộp. Nút xác nhận là nút SAU.
    const nut = screen.getAllByRole('button', { name: 'Thu hồi' })
    fireEvent.click(nut[nut.length - 1])
    expect(chay).toHaveBeenCalledTimes(1)
  })
})
