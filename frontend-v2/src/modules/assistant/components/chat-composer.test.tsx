import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { ChatComposer } from './chat-composer'

function dung(props: Partial<Parameters<typeof ChatComposer>[0]> = {}) {
  const onSend = vi.fn()
  render(<ChatComposer disabled={false} busy={false} onSend={onSend} {...props} />)
  return { onSend, o: screen.getByLabelText('Câu hỏi cho trợ lý') }
}

describe('ChatComposer', () => {
  it('đang CHỜ trả lời vẫn gõ tiếp được, chỉ chặn gửi', async () => {
    //  Ép ra được 25/08/2026: bản đầu khóa luôn ô nhập trong lúc chờ, cướp mất
    //  mấy giây người dùng có thể gõ sẵn câu sau — mà câu trả lời hay mất vài
    //  giây tới cả chục giây.
    const nguoi = userEvent.setup()
    const { o, onSend } = dung({ busy: true })

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

    expect(onSend).toHaveBeenCalledWith('câu hỏi quý giá')
    expect(o).toHaveValue('câu hỏi quý giá')
  })

  it('gửi được thì xóa ô, không giữ lại chữ cũ', async () => {
    const nguoi = userEvent.setup()
    const { o } = dung()
    await nguoi.type(o, 'hỏi thử{Enter}')
    expect(o).toHaveValue('')
  })

  it('Shift+Enter xuống dòng chứ không gửi', async () => {
    const nguoi = userEvent.setup()
    const { o, onSend } = dung()
    await nguoi.type(o, 'dòng một{Shift>}{Enter}{/Shift}dòng hai')
    expect(onSend).not.toHaveBeenCalled()
    expect(String(o.getAttribute('value') ?? (o as HTMLTextAreaElement).value)).toContain('\n')
  })

  it('câu rỗng / toàn khoảng trắng thì không gửi', async () => {
    const nguoi = userEvent.setup()
    const { o, onSend } = dung()
    await nguoi.type(o, '   {Enter}')
    expect(onSend).not.toHaveBeenCalled()
    expect(screen.getByLabelText('Gửi câu hỏi')).toBeDisabled()
  })

  it('cắt khoảng trắng thừa trước khi gửi', async () => {
    const nguoi = userEvent.setup()
    const { o, onSend } = dung()
    await nguoi.type(o, '   hỏi có khoảng trắng   {Enter}')
    expect(onSend).toHaveBeenCalledWith('hỏi có khoảng trắng')
  })

  it('chưa cấu hình nhà cung cấp thì khóa hẳn ô nhập', () => {
    const { o } = dung({ disabled: true })
    expect(o).toBeDisabled()
  })
})
