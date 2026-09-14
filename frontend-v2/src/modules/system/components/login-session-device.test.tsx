import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { DEVICE_TYPE } from '../api/login-session-api'
import { LoginSessionDevice, LoginSessionEnding } from './login-session-device'

/**
 * Ô «Thiết bị» của phiên đăng nhập (bao-CR-395).
 *
 * Backend dựng `device_label` từ User-Agent; UA lạ (script, curl, bot) thì nhãn
 * rỗng và cả `browser`/`os` cũng rỗng. Màn hình phải nói «Không rõ thiết bị»
 * chứ không để ô trống — ô trống đọc thành "không có gì đáng ngờ", trong khi
 * phiên từ UA lạ chính là thứ quản trị cần thấy nhất.
 */

const base = {
  device_type: DEVICE_TYPE.DESKTOP,
  device_label: '',
  browser: '',
  os: '',
  is_current: false,
  user_agent: 'curl/8.0',
}

describe('LoginSessionDevice', () => {
  it('prefers the backend device_label when present', () => {
    render(<LoginSessionDevice session={{ ...base, device_label: 'Chrome 120 trên Windows' }} />)
    expect(screen.getByText('Chrome 120 trên Windows')).toBeInTheDocument()
  })

  it('falls back to "browser trên os" when the label is empty', () => {
    render(<LoginSessionDevice session={{ ...base, browser: 'Safari', os: 'iOS' }} />)
    expect(screen.getByText('Safari trên iOS')).toBeInTheDocument()
  })

  it('drops the joiner when only one of browser/os is known', () => {
    render(<LoginSessionDevice session={{ ...base, os: 'Linux' }} />)
    expect(screen.getByText('Linux')).toBeInTheDocument()
    expect(screen.queryByText(/trên/)).not.toBeInTheDocument()
  })

  it('never renders an empty label for an unknown user agent', () => {
    render(<LoginSessionDevice session={base} />)
    expect(screen.getByText('Không rõ thiết bị')).toBeInTheDocument()
  })

  it('marks the session the viewer is using right now', () => {
    const { rerender } = render(<LoginSessionDevice session={{ ...base, is_current: true }} />)
    expect(screen.getByText('Thiết bị này')).toBeInTheDocument()
    rerender(<LoginSessionDevice session={base} />)
    expect(screen.queryByText('Thiết bị này')).not.toBeInTheDocument()
  })

  it('does not crash on a device_type outside the known enum', () => {
    render(<LoginSessionDevice session={{ ...base, device_type: 42, device_label: 'X' }} />)
    expect(screen.getByText('X')).toBeInTheDocument()
  })
})

describe('LoginSessionEnding', () => {
  it('shows the backend ending text verbatim', () => {
    render(<LoginSessionEnding session={{ is_alive: false, ending: 'Bị quản trị đá lúc 10:00' }} />)
    expect(screen.getByText('Bị quản trị đá lúc 10:00')).toBeInTheDocument()
  })

  it('falls back to a status word when ending is empty', () => {
    const { rerender } = render(<LoginSessionEnding session={{ is_alive: true, ending: '' }} />)
    expect(screen.getByText('Còn hiệu lực')).toBeInTheDocument()
    rerender(<LoginSessionEnding session={{ is_alive: false, ending: '' }} />)
    expect(screen.getByText('Đã kết thúc')).toBeInTheDocument()
  })
})
