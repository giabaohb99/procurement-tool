import { fireEvent, render, screen } from '@testing-library/react'
import { createRef } from 'react'
import { beforeAll, describe, expect, it, vi } from 'vitest'

import { MentionInput, type MentionInputHandle } from './mention-input'

/**
 * Ô soạn có nhắc tên — phần NHẬN TỆP (dán ảnh, kéo thả) và phím tắt.
 *
 * Chỗ hỏng âm thầm: `onPaste` phải chặn sự kiện **chỉ khi thực sự có tệp**. Chặn
 * luôn thì dán một đoạn văn bản thường cũng bị nuốt; không chặn khi có tệp thì
 * trình duyệt nhét luôn cái ảnh vào vùng `contenteditable` dưới dạng `<img>`
 * base64, mà `serializeMentionBody` chỉ đọc chữ nên ảnh biến mất không dấu vết.
 *
 * Với kéo thả thì bẫy ngược lại: KHÔNG chặn `dragover` là `drop` không bao giờ
 * bắn, trình duyệt MỞ tệp thay cho cả trang và mất sạch nội dung đang gõ dở.
 */

/*  jsdom KHÔNG cài `document.execCommand` — ô soạn dùng nó để chèn chữ vào
    `contenteditable` (đường duy nhất vừa tôn trọng vị trí con trỏ vừa vào được
    ngăn hoàn tác của trình duyệt). Thiếu bản giả này thì nhánh "dán chữ thường"
    ném lỗi ngoài luồng test: bài vẫn xanh nhưng cả lượt chạy báo có lỗi.  */
beforeAll(() => {
  if (typeof document.execCommand !== 'function') {
    Object.defineProperty(document, 'execCommand', {
      configurable: true,
      value: (_lenh: string, _ui: boolean, chu: string) => {
        const o = document.activeElement
        if (o instanceof HTMLElement && o.isContentEditable) o.textContent += chu ?? ''
        return true
      },
    })
  }
})

const khongTimAi = () => Promise.resolve([])

function tep(name = 'anh.png', type = 'image/png'): File {
  return new File(['x'], name, { type, lastModified: 1 })
}

function dungO(props: Partial<React.ComponentProps<typeof MentionInput>> = {}) {
  const ref = createRef<MentionInputHandle>()
  render(
    <MentionInput
      ref={ref}
      placeholder="Viết bình luận"
      search={khongTimAi}
      onSubmit={props.onSubmit ?? vi.fn()}
      {...props}
    />,
  )
  return { ref, box: screen.getByRole('textbox') }
}

/** Dựng `DataTransfer` giả — jsdom chưa có hàm dựng thật. */
function duLieu(files: File[], text = '') {
  return {
    files,
    items: [],
    types: files.length ? ['Files'] : ['text/plain'],
    getData: () => text,
  }
}

describe('MentionInput — nhận tệp', () => {
  it('DÁN ẢNH thì báo tệp ra ngoài và chặn hành vi mặc định', () => {
    const onFiles = vi.fn()
    const { box } = dungO({ onFiles })
    const anh = tep()

    const bịChặn = !fireEvent.paste(box, { clipboardData: duLieu([anh]) })

    expect(onFiles).toHaveBeenCalledWith([anh])
    //  Không chặn thì trình duyệt tự nhét `<img>` base64 vào ô soạn, mà bộ đọc
    //  ngược chỉ lấy chữ — ảnh biến mất không dấu vết.
    expect(bịChặn).toBe(true)
  })

  it('dán CHỮ THƯỜNG thì KHÔNG gọi onFiles', () => {
    //  Chặn nhầm ở đây là mọi thao tác dán văn bản đều hỏng.
    const onFiles = vi.fn()
    const { box } = dungO({ onFiles })
    fireEvent.paste(box, { clipboardData: duLieu([], 'một đoạn văn') })
    expect(onFiles).not.toHaveBeenCalled()
  })

  it('dán nhiều ảnh một lượt thì báo ra ĐỦ, không chỉ cái đầu', () => {
    const onFiles = vi.fn()
    const { box } = dungO({ onFiles })
    const bo = [tep('a.png'), tep('b.png'), tep('c.png')]
    fireEvent.paste(box, { clipboardData: duLieu(bo) })
    expect(onFiles.mock.calls[0][0]).toHaveLength(3)
  })

  it('KHÔNG truyền onFiles thì dán tệp không nổ và không nuốt gì', () => {
    //  Diễn đàn và Thu mua đang dùng ô này mà không truyền `onFiles`.
    const { box } = dungO()
    expect(() => fireEvent.paste(box, { clipboardData: duLieu([tep()]) })).not.toThrow()
  })

  it('KÉO qua ô có tệp thì chặn mặc định, nếu không «thả» sẽ không bao giờ bắn', () => {
    const { box } = dungO({ onFiles: vi.fn() })
    const bịChặn = !fireEvent.dragOver(box, { dataTransfer: duLieu([tep()]) })
    expect(bịChặn).toBe(true)
  })

  it('kéo qua ô thứ KHÔNG PHẢI tệp (chữ bôi đen) thì để trình duyệt lo', () => {
    const { box } = dungO({ onFiles: vi.fn() })
    const bịChặn = !fireEvent.dragOver(box, { dataTransfer: duLieu([], 'chữ') })
    expect(bịChặn).toBe(false)
  })

  it('THẢ tệp thì báo ra ngoài', () => {
    const onFiles = vi.fn()
    const { box } = dungO({ onFiles })
    const t = tep('ke-hoach.xlsx', 'application/vnd.ms-excel')
    fireEvent.drop(box, { dataTransfer: duLieu([t]) })
    expect(onFiles).toHaveBeenCalledWith([t])
  })

  it('thả thứ KHÔNG có tệp nào thì bỏ qua, không gọi với mảng rỗng', () => {
    const onFiles = vi.fn()
    const { box } = dungO({ onFiles })
    fireEvent.drop(box, { dataTransfer: duLieu([], 'chữ kéo từ nơi khác') })
    expect(onFiles).not.toHaveBeenCalled()
  })

  it('không truyền onFiles thì THẢ tệp cũng không nổ', () => {
    const { box } = dungO()
    expect(() => fireEvent.drop(box, { dataTransfer: duLieu([tep()]) })).not.toThrow()
  })
})

describe('MentionInput — phím tắt và ô rỗng', () => {
  it('Ctrl/Cmd + Enter là GỬI, Enter trần thì xuống dòng', () => {
    const onSubmit = vi.fn()
    const { box } = dungO({ onSubmit })

    fireEvent.keyDown(box, { key: 'Enter' })
    expect(onSubmit).not.toHaveBeenCalled()

    fireEvent.keyDown(box, { key: 'Enter', ctrlKey: true })
    fireEvent.keyDown(box, { key: 'Enter', metaKey: true })
    expect(onSubmit).toHaveBeenCalledTimes(2)
  })

  it('báo ra ngoài khi ô CHUYỂN từ rỗng sang có chữ', () => {
    //  Nút Gửi bật/tắt theo cờ này; sai là nút chết trong khi ô đã có chữ.
    const onEmptyChange = vi.fn()
    const { box } = dungO({ onEmptyChange })
    box.textContent = 'xin chào'
    fireEvent.input(box)
    expect(onEmptyChange).toHaveBeenLastCalledWith(false)
  })

  it('ô chỉ có KHOẢNG TRẮNG vẫn tính là rỗng', () => {
    const onEmptyChange = vi.fn()
    const { box } = dungO({ onEmptyChange })
    box.textContent = '     '
    fireEvent.input(box)
    expect(onEmptyChange).toHaveBeenLastCalledWith(true)
  })

  it('`clear()` dọn sạch nội dung', () => {
    const { ref, box } = dungO()
    box.textContent = 'nội dung cũ'
    fireEvent.input(box)
    ref.current?.clear()
    expect(box.textContent).toBe('')
  })
})
