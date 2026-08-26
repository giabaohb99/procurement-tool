import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { EditorRuler, type PageMargins } from './editor-ruler'

/**
 * LỖI ĐÃ XẢY RA (19/08/2026): thước báo thay đổi theo TỪNG KHUNG HÌNH lúc rê
 * chuột, nên trang cha phải hẹn giờ 600ms để gom nhịp. Khe hở đó gây hai lỗi
 * người dùng gặp thật:
 *   - kéo lề xong bấm ngay «In / Xuất PDF» → bản in đọc lề CŨ;
 *   - kéo lề rồi chuyển tab trong khoảng đó → hàm dọn dẹp hủy hẹn giờ, MẤT hẳn.
 *
 * Nên `onCommit` phải bắn đúng MỘT LẦN mỗi cú chỉnh, ngay lúc buông tay — và
 * `onChange` (chỉ để vẽ) không được dùng để ghi xuống bản ghi.
 */
const LE: PageMargins = { left: 113, right: 76 }
const DEFAULT_VALUE: PageMargins = { left: 113, right: 76 }

function buildProps() {
  const onChange = vi.fn()
  const onCommit = vi.fn()
  render(
    <EditorRuler
      pageWidth={794}
      defaultMargins={DEFAULT_VALUE}
      margins={LE}
      onChange={onChange}
      onCommit={onCommit}
      zoom={1}
      page={null}
    />,
  )
  return { onChange, onCommit, tayTrai: screen.getByLabelText(/^Lề trái/) }
}

/** jsdom chưa dựng `PointerEvent`; `MouseEvent` mang được `clientX` là đủ. */
function chuot(type: string, clientX: number) {
  return new MouseEvent(type, { clientX, bubbles: true })
}

describe('EditorRuler', () => {
  it('rê chuột thì vẽ liên tục nhưng CHƯA ghi', () => {
    const { onChange, onCommit, tayTrai } = buildProps()

    fireEvent.pointerDown(tayTrai, { clientX: 100 })
    window.dispatchEvent(chuot('pointermove', 140))
    window.dispatchEvent(chuot('pointermove', 180))

    expect(onChange).toHaveBeenCalled()
    expect(onCommit).not.toHaveBeenCalled()
  })

  it('buông tay thì ghi ĐÚNG MỘT LẦN, theo giá trị cuối cùng của cú kéo', () => {
    const { onCommit, tayTrai } = buildProps()

    fireEvent.pointerDown(tayTrai, { clientX: 100 })
    window.dispatchEvent(chuot('pointermove', 140))
    window.dispatchEvent(chuot('pointermove', 180))
    window.dispatchEvent(chuot('pointerup', 180))

    expect(onCommit).toHaveBeenCalledTimes(1)
    //  Kéo sang phải 80px → lề trái rộng ra, không phải giữ nguyên giá trị đầu.
    expect(onCommit.mock.calls[0][0].left).toBeGreaterThan(LE.left)
  })

  it('không ghi thêm lần nữa sau khi đã buông tay', () => {
    const { onCommit, tayTrai } = buildProps()

    fireEvent.pointerDown(tayTrai, { clientX: 100 })
    window.dispatchEvent(chuot('pointermove', 140))
    window.dispatchEvent(chuot('pointerup', 140))
    window.dispatchEvent(chuot('pointerup', 140))

    expect(onCommit).toHaveBeenCalledTimes(1)
  })

  it('nhích bằng phím mũi tên cũng ghi ngay', () => {
    const { onCommit, tayTrai } = buildProps()

    fireEvent.keyDown(tayTrai, { key: 'ArrowRight' })

    expect(onCommit).toHaveBeenCalledTimes(1)
    expect(onCommit.mock.calls[0][0].left).toBeGreaterThan(LE.left)
  })

  it('bấm đúp về lề mặc định cũng ghi ngay', () => {
    const onChange = vi.fn()
    const onCommit = vi.fn()
    render(
      <EditorRuler
        pageWidth={794}
        defaultMargins={DEFAULT_VALUE}
        margins={{ left: 170, right: 76 }}
        onChange={onChange}
        onCommit={onCommit}
        zoom={1}
        page={null}
      />,
    )

    fireEvent.doubleClick(screen.getByLabelText(/^Lề trái/))

    expect(onCommit).toHaveBeenCalledTimes(1)
    expect(onCommit.mock.calls[0][0].left).toBe(DEFAULT_VALUE.left)
  })
})
