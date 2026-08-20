import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { FileDropzone } from './file-dropzone'

function fakeFile(name = 'bao-gia.pdf') {
  return new File(['noi dung'], name, { type: 'application/pdf' })
}

describe('FileDropzone', () => {
  it('thả tệp vào vùng thì báo danh sách tệp ra ngoài', () => {
    const onFiles = vi.fn()
    render(<FileDropzone onFiles={onFiles} hint="Kéo thả tệp vào đây" />)

    const file = fakeFile()
    fireEvent.drop(screen.getByRole('button', { name: 'Kéo thả tệp vào đây' }), {
      dataTransfer: { files: [file] },
    })

    expect(onFiles).toHaveBeenCalledWith([file])
  })

  it('thả mà không có tệp nào thì không gọi gì cả', () => {
    const onFiles = vi.fn()
    render(<FileDropzone onFiles={onFiles} hint="Kéo thả tệp vào đây" />)

    fireEvent.drop(screen.getByRole('button', { name: 'Kéo thả tệp vào đây' }), {
      dataTransfer: { files: [] },
    })

    expect(onFiles).not.toHaveBeenCalled()
  })

  /**
   * Ô chọn mục lưu tệp nằm NGAY TRONG vùng thả. Không chặn nổi bọt thì bấm vào ô
   * chọn là hộp chọn tệp của trình duyệt nhảy ra đè lên danh sách mục.
   */
  it('bấm vào khối phụ bên trong không mở hộp chọn tệp', async () => {
    const user = userEvent.setup()
    render(
      <FileDropzone onFiles={vi.fn()} hint="Kéo thả tệp vào đây">
        <button type="button">Lưu vào mục</button>
      </FileDropzone>,
    )

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const click = vi.spyOn(input, 'click')

    await user.click(screen.getByRole('button', { name: 'Lưu vào mục' }))

    expect(click).not.toHaveBeenCalled()
  })

  it('bấm vào vùng thả thì mở hộp chọn tệp', async () => {
    const user = userEvent.setup()
    render(<FileDropzone onFiles={vi.fn()} hint="Kéo thả tệp vào đây" />)

    const input = document.querySelector('input[type="file"]') as HTMLInputElement
    const click = vi.spyOn(input, 'click')

    await user.click(screen.getByRole('button', { name: 'Kéo thả tệp vào đây' }))

    expect(click).toHaveBeenCalled()
  })

  it('đang tải lên thì khóa vùng thả, thả thêm cũng không ăn', () => {
    const onFiles = vi.fn()
    render(<FileDropzone onFiles={onFiles} hint="Kéo thả tệp vào đây" busy />)

    expect(screen.getByText('Đang tải tệp lên…')).toBeInTheDocument()
    fireEvent.drop(screen.getByRole('button', { name: 'Kéo thả tệp vào đây' }), {
      dataTransfer: { files: [fakeFile()] },
    })

    expect(onFiles).not.toHaveBeenCalled()
  })
})
