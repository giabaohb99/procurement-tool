import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { SettingSecret } from '../types/setting'

import { SettingSecretRow } from './setting-secret-row'

/**
 * Ô nhập khóa bí mật — nay còn giữ cả khóa API của Claude và Gemini (bao-CR-429).
 *
 * Hai thứ tệp này canh. Thứ nhất là link ra trang cấp khóa: khóa API là thứ
 * người dùng phải tự đi đăng ký rồi mang về, nên lúc mở ô ra lần đầu họ chưa có
 * gì để gõ cả — thiếu đường dẫn thì việc kế tiếp của họ là đi hỏi người khác.
 * Thứ hai là luật cũ vẫn phải đứng: giá trị đã lưu KHÔNG bao giờ đi ngược ra
 * màn hình, ô chỉ chứa thứ người dùng vừa tự gõ.
 */

const base: SettingSecret = {
  key: 'gemini_api_key',
  group: 'ai',
  label: 'Google Gemini API Key',
  configured: false,
}

describe('SettingSecretRow', () => {
  it('bày link ra trang cấp khóa khi backend khai doc_url', () => {
    render(
      <SettingSecretRow
        secret={{ ...base, doc_url: 'https://aistudio.google.com/apikey' }}
        value=""
        disabled={false}
        onChange={vi.fn()}
      />,
    )

    const link = screen.getByRole('link', { name: /Lấy ở đây/ })
    expect(link).toHaveAttribute('href', 'https://aistudio.google.com/apikey')
    //  Thiếu `noreferrer` thì trang đích cầm `window.opener` và đổi được địa chỉ
    //  tab ERP đang mở sau lưng người dùng.
    expect(link).toHaveAttribute('rel', expect.stringContaining('noreferrer'))
    expect(link).toHaveAttribute('target', '_blank')
  })

  it('không có doc_url thì không vẽ link rỗng', () => {
    render(<SettingSecretRow secret={base} value="" disabled={false} onChange={vi.fn()} />)
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })

  it('ô vẫn là ô mật khẩu và chỉ chứa thứ người dùng vừa gõ', () => {
    render(
      <SettingSecretRow
        secret={{ ...base, configured: true }}
        value="nguoi-dung-vua-go"
        disabled={false}
        onChange={vi.fn()}
      />,
    )

    const input = screen.getByLabelText(/Google Gemini API Key/)
    expect(input).toHaveAttribute('type', 'password')
    expect(input).toHaveValue('nguoi-dung-vua-go')
    //  Đã cấu hình rồi thì chữ gợi ý phải nói rõ "để trống = giữ nguyên", kẻo
    //  người dùng tưởng bỏ trống là xóa khóa đang chạy thật.
    expect(input).toHaveAttribute('placeholder', 'Để trống nếu giữ nguyên')
  })

  it('hiện diễn giải của ô khi backend có khai', () => {
    render(
      <SettingSecretRow
        secret={{ ...base, hint: 'Để trống thì trợ lý dùng nhà còn lại.' }}
        value=""
        disabled={false}
        onChange={vi.fn()}
      />,
    )
    expect(screen.getByText('Để trống thì trợ lý dùng nhà còn lại.')).toBeInTheDocument()
  })
})
