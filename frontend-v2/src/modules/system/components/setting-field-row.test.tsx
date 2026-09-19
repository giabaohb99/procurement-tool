import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import type { SettingField } from '../types/setting'

import { SettingFieldRow } from './setting-field-row'

/**
 * Một hàng cấu hình vẽ theo `type` backend khai (bao-CR-429 thêm kiểu `select`).
 *
 * Kiểu `select` có mặt vì ô *Nhà cung cấp mặc định* trước đây là ô chữ tự do:
 * gõ "Claude" viết hoa hay "chatgpt" đều lưu được, và hậu quả chỉ lộ ra lúc ai
 * đó hỏi trợ lý rồi nhận câu báo chưa cấu hình. Backend nay chặn giá trị lạ,
 * còn màn hình thì không cho gõ sai ngay từ đầu.
 */

const base: SettingField = {
  key: 'ai_default_provider',
  group: 'ai',
  label: 'Nhà cung cấp mặc định',
  type: 'select',
  value: 'claude',
  options: [
    { value: 'claude', label: 'Claude (Anthropic)' },
    { value: 'gemini', label: 'Gemini (Google)' },
  ],
}

describe('SettingFieldRow — ô chọn', () => {
  it('bày nhãn của giá trị đang chọn, không bày mã kỹ thuật', () => {
    render(<SettingFieldRow field={base} disabled={false} onChange={vi.fn()} />)
    expect(screen.getByText('Claude (Anthropic)')).toBeInTheDocument()
    expect(screen.queryByText('claude')).not.toBeInTheDocument()
  })

  it('chưa đặt thì hiện chữ gợi ý chứ không phải một dòng rỗng', () => {
    //  Radix cấm `value=""`; truyền rỗng mà không đổi sang `undefined` thì ô
    //  hiện trắng trơn và không ai biết nó đang ở trạng thái nào.
    render(<SettingFieldRow field={{ ...base, value: '' }} disabled={false} onChange={vi.fn()} />)
    expect(screen.getByText('— Chưa chọn —')).toBeInTheDocument()
  })

  it('chỉ có quyền xem thì ô chọn bị khóa', () => {
    render(<SettingFieldRow field={base} disabled onChange={vi.fn()} />)
    expect(screen.getByRole('combobox')).toBeDisabled()
  })
})

describe('SettingFieldRow — link tới chỗ lấy giá trị', () => {
  it('ô chữ có doc_url thì kèm link ra ngoài', () => {
    render(
      <SettingFieldRow
        field={{
          key: 'ai_gemini_model',
          group: 'ai',
          label: 'Model Gemini',
          type: 'str',
          value: 'gemini-flash-latest',
          doc_url: 'https://ai.google.dev/gemini-api/docs/models',
        }}
        disabled={false}
        onChange={vi.fn()}
      />,
    )

    expect(screen.getByRole('link', { name: /Lấy ở đây/ })).toHaveAttribute(
      'href',
      'https://ai.google.dev/gemini-api/docs/models',
    )
    expect(screen.getByLabelText('Model Gemini')).toHaveValue('gemini-flash-latest')
  })

  it('ô không khai doc_url thì không mọc link thừa', () => {
    render(
      <SettingFieldRow
        field={{ key: 'smtp_host', group: 'email', label: 'SMTP Host', type: 'str', value: 'a.vn' }}
        disabled={false}
        onChange={vi.fn()}
      />,
    )
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })
})
