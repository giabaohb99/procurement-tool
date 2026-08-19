import { describe, expect, it } from 'vitest'

import type { SettingField } from '../types/setting'
import { buildSettingValues } from './build-setting-values'

const fields: SettingField[] = [
  { key: 'email_enabled', group: 'email', label: 'Bật gửi email', type: 'bool', value: true },
  { key: 'smtp_port', group: 'email', label: 'SMTP Port', type: 'int', value: 587 },
  { key: 'smtp_host', group: 'email', label: 'SMTP Host', type: 'str', value: 'smtp-relay.brevo.com' },
]

describe('buildSettingValues', () => {
  it('gửi mọi trường thường, giữ nguyên kiểu luận lý và kiểu số', () => {
    const values = buildSettingValues(fields, {})

    expect(values).toEqual({
      email_enabled: true,
      smtp_port: 587,
      smtp_host: 'smtp-relay.brevo.com',
    })
  })

  it('gửi cả trường thường bị xóa rỗng — rỗng ở đó là chủ ý xóa cấu hình', () => {
    const values = buildSettingValues(
      [{ key: 'email_test_override', group: 'email', label: '', type: 'str', value: '' }],
      {},
    )

    expect(values).toHaveProperty('email_test_override', '')
  })

  it('KHÔNG gửi ô bí mật để trống — gửi lên là xóa mất mật khẩu SMTP đang chạy', () => {
    const values = buildSettingValues(fields, { smtp_password: '' })

    expect(values).not.toHaveProperty('smtp_password')
  })

  it('KHÔNG gửi ô bí mật chỉ có khoảng trắng — lỡ chạm phím cách không tính là đổi khóa', () => {
    const values = buildSettingValues(fields, { smtp_password: '   ', r2_secret_access_key: '\t\n' })

    expect(values).not.toHaveProperty('smtp_password')
    expect(values).not.toHaveProperty('r2_secret_access_key')
  })

  it('gửi ô bí mật NGUYÊN VẸN khi có gõ, giữ cả khoảng trắng giữa các cụm', () => {
    // Mật khẩu ứng dụng của Google có dạng bốn cụm bốn ký tự cách nhau; cắt
    // khoảng trắng bên trong là sai mật khẩu.
    const values = buildSettingValues(fields, { smtp_password: 'abcd efgh ijkl mnop' })

    expect(values.smtp_password).toBe('abcd efgh ijkl mnop')
  })
})
