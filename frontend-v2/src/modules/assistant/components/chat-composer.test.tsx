import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { assistantApi } from '../api/assistant-api'
import { ChatComposer } from './chat-composer'

//  Chặn gọi API thật: tải tệp lên mock ở tầng api của module (không mock axios).
vi.mock('../api/assistant-api', () => ({
  assistantApi: { uploadAttachment: vi.fn() },
}))

const uploadMock = vi.mocked(assistantApi.uploadAttachment)

function build(props: Partial<Parameters<typeof ChatComposer>[0]> = {}) {
  const onSend = vi.fn()
  render(<ChatComposer disabled={false} busy={false} onSend={onSend} {...props} />)
  return { onSend, o: screen.getByLabelText('Câu hỏi cho trợ lý') }
}

const pngFile = (name = 'man-hinh.png') =>
  new File(['x'], name, { type: 'image/png' })

const pngMeta = { id: 7, filename: 'man-hinh.png', content_type: 'image/png', size: 1 }

beforeEach(() => {
  uploadMock.mockReset()
})

describe('ChatComposer', () => {
  it('đang CHỜ trả lời vẫn gõ tiếp được, chỉ chặn gửi', async () => {
    //  Ép ra được 25/08/2026: bản đầu khóa luôn ô nhập trong lúc chờ, cướp mất
    //  mấy giây người dùng có thể gõ sẵn câu sau — mà câu trả lời hay mất vài
    //  giây tới cả chục giây.
    const nguoi = userEvent.setup()
    const { o, onSend } = build({ busy: true })

    expect(o).not.toBeDisabled()
    await nguoi.type(o, 'gõ sẵn câu sau')
    expect(o).toHaveValue('gõ sẵn câu sau')

    await nguoi.click(screen.getByLabelText('Gửi câu hỏi'))
    expect(onSend).not.toHaveBeenCalled()
  })

  it('GỬI HỎNG thì trả lại nguyên câu vào ô, không để mất trắng', async () => {
    //  Bản đầu: ô nhập đã xóa từ lúc bấm gửi, bong bóng chờ thì bị gỡ ở
    //  `finally` — câu vừa nghĩ cả phút biến mất, phải gõ lại từ đầu.
    const nguoi = userEvent.setup()
    const onSend = vi.fn().mockRejectedValue(new Error('mạng hỏng'))
    render(<ChatComposer disabled={false} busy={false} onSend={onSend} />)
    const o = screen.getByLabelText('Câu hỏi cho trợ lý')

    await nguoi.type(o, 'câu hỏi quý giá{Enter}')

    expect(onSend).toHaveBeenCalledWith('câu hỏi quý giá', undefined)
    expect(o).toHaveValue('câu hỏi quý giá')
  })

  it('gửi được thì xóa ô, không giữ lại chữ cũ', async () => {
    const nguoi = userEvent.setup()
    const { o } = build()
    await nguoi.type(o, 'hỏi thử{Enter}')
    expect(o).toHaveValue('')
  })

  it('Shift+Enter xuống dòng chứ không gửi', async () => {
    const nguoi = userEvent.setup()
    const { o, onSend } = build()
    await nguoi.type(o, 'dòng một{Shift>}{Enter}{/Shift}dòng hai')
    expect(onSend).not.toHaveBeenCalled()
    expect(String(o.getAttribute('value') ?? (o as HTMLTextAreaElement).value)).toContain('\n')
  })

  it('câu rỗng / toàn khoảng trắng thì không gửi', async () => {
    const nguoi = userEvent.setup()
    const { o, onSend } = build()
    await nguoi.type(o, '   {Enter}')
    expect(onSend).not.toHaveBeenCalled()
    expect(screen.getByLabelText('Gửi câu hỏi')).toBeDisabled()
  })

  it('cắt khoảng trắng thừa trước khi gửi', async () => {
    const nguoi = userEvent.setup()
    const { o, onSend } = build()
    await nguoi.type(o, '   hỏi có khoảng trắng   {Enter}')
    expect(onSend).toHaveBeenCalledWith('hỏi có khoảng trắng', undefined)
  })

  it('chưa cấu hình nhà cung cấp thì khóa hẳn ô nhập', () => {
    const { o } = build({ disabled: true })
    expect(o).toBeDisabled()
  })

  //  ── Đính kèm tệp (CR-204) ──────────────────────────────────────────────────

  it('chọn ảnh -> tải lên ngay, hiện chip, gửi kèm metadata tệp', async () => {
    const nguoi = userEvent.setup()
    uploadMock.mockResolvedValue(pngMeta)
    const { o, onSend } = build()

    await nguoi.upload(screen.getByLabelText('Chọn tệp đính kèm'), pngFile())
    expect(uploadMock).toHaveBeenCalledTimes(1)
    expect(await screen.findByText('man-hinh.png')).toBeInTheDocument()

    await nguoi.type(o, 'ảnh này là đơn nào?{Enter}')
    expect(onSend).toHaveBeenCalledWith('ảnh này là đơn nào?', [pngMeta])
    //  Gửi xong thì chip phải biến mất — không dính sang câu sau.
    expect(screen.queryByText('man-hinh.png')).not.toBeInTheDocument()
  })

  it('gửi được KHI CHỈ CÓ TỆP không kèm chữ', async () => {
    const nguoi = userEvent.setup()
    uploadMock.mockResolvedValue(pngMeta)
    const { onSend } = build()

    await nguoi.upload(screen.getByLabelText('Chọn tệp đính kèm'), pngFile())
    await screen.findByText('man-hinh.png')

    await nguoi.click(screen.getByLabelText('Gửi câu hỏi'))
    expect(onSend).toHaveBeenCalledWith('', [pngMeta])
  })

  it('tệp sai loại bị chặn ở client, không tốn lượt tải lên', async () => {
    //  `applyAccept: false` để vượt qua bộ lọc accept của trình duyệt — mô phỏng
    //  người dùng kéo-thả / chọn "All files".
    const nguoi = userEvent.setup({ applyAccept: false })
    const { onSend } = build()
    const xlsx = new File(['x'], 'bang.xlsx', {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })

    await nguoi.upload(screen.getByLabelText('Chọn tệp đính kèm'), xlsx)

    expect(uploadMock).not.toHaveBeenCalled()
    expect(screen.queryByText('bang.xlsx')).not.toBeInTheDocument()
    expect(onSend).not.toHaveBeenCalled()
  })

  it('đang tải tệp lên thì CHẶN gửi — gửi id chưa có là mất tệp', async () => {
    const nguoi = userEvent.setup()
    let finishUpload!: (m: typeof pngMeta) => void
    uploadMock.mockReturnValue(new Promise((resolve) => { finishUpload = resolve }))
    const { o, onSend } = build()

    await nguoi.upload(screen.getByLabelText('Chọn tệp đính kèm'), pngFile())
    await nguoi.type(o, 'câu hỏi{Enter}')
    expect(onSend).not.toHaveBeenCalled()

    finishUpload(pngMeta)
    await waitFor(() => expect(screen.getByLabelText('Gửi câu hỏi')).not.toBeDisabled())
    await nguoi.type(o, '{Enter}')
    expect(onSend).toHaveBeenCalledWith('câu hỏi', [pngMeta])
  })

  it('gỡ chip thì tệp không đi kèm câu gửi', async () => {
    const nguoi = userEvent.setup()
    uploadMock.mockResolvedValue(pngMeta)
    const { o, onSend } = build()

    await nguoi.upload(screen.getByLabelText('Chọn tệp đính kèm'), pngFile())
    await screen.findByText('man-hinh.png')
    await nguoi.click(screen.getByLabelText('Gỡ tệp man-hinh.png'))

    await nguoi.type(o, 'hỏi chay{Enter}')
    expect(onSend).toHaveBeenCalledWith('hỏi chay', undefined)
  })
})
