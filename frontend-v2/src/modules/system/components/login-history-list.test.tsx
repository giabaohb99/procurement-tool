import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import type { LoginHistoryItem, LoginHistoryResult } from '../api/login-session-api'
import { HISTORY_KIND } from '../api/login-session-api'
import { HISTORY_PREVIEW_ROWS, LoginHistoryList } from './login-history-list'

/**
 * Danh sách lịch sử đăng nhập dùng chung (bao-CR-400) — hai chỗ vẽ (hồ sơ nhân
 * sự + tab Trang cá nhân) cùng đi qua đây, nên cái gì lủng ở đây là lủng cả hai.
 *
 * Chỗ dễ sai: dòng THẤT BẠI mà backend không ghi câu lỗi thì phải có chữ mặc
 * định — để trống là người đọc thấy một dòng đỏ không nói gì, không biết vì sao.
 */

function makeRow(overrides: Partial<LoginHistoryItem> = {}): LoginHistoryItem {
  return {
    kind: HISTORY_KIND.LOGIN,
    ok: true,
    at: '2026-09-14T08:00:00',
    session_id: 11,
    login_method: 1,
    login_method_label: 'Mật khẩu',
    device_label: 'Chrome trên Windows',
    ip: '10.0.0.5',
    ending: 'Còn hiệu lực',
    revoked_by_name: '',
    message: '',
    ...overrides,
  }
}

function makeResult(items: LoginHistoryItem[], days = 90): LoginHistoryResult {
  return {
    items,
    days,
    login_count: items.filter((r) => r.ok).length,
    failed_count: items.filter((r) => !r.ok).length,
  }
}

describe('LoginHistoryList', () => {
  it('shows an empty message naming the range instead of a blank list', () => {
    render(<LoginHistoryList data={makeResult([], 30)} isLoading={false} days={30} />)
    expect(screen.getByText('Chưa ghi nhận lần đăng nhập nào trong 30 ngày qua.')).toBeInTheDocument()
    expect(screen.queryByRole('list')).not.toBeInTheDocument()
  })

  it('renders a success row with its device and a failed row with the backend message', () => {
    const data = makeResult([
      makeRow(),
      makeRow({
        kind: HISTORY_KIND.LOGIN_FAILED,
        ok: false,
        session_id: 0,
        device_label: '',
        ip: '1.2.3.4',
        ending: '',
        message: 'Tài khoản bị khóa',
      }),
    ])
    render(<LoginHistoryList data={data} isLoading={false} days={90} />)
    expect(screen.getByText('Thành công')).toBeInTheDocument()
    expect(screen.getByText('Chrome trên Windows')).toBeInTheDocument()
    expect(screen.getByText('Thất bại')).toBeInTheDocument()
    expect(screen.getByText('Tài khoản bị khóa')).toBeInTheDocument()
    expect(screen.getByText('1 lần đăng nhập · 1 lần thất bại')).toBeInTheDocument()
  })

  it('falls back to "Sai mật khẩu" when a failed row carries no message', () => {
    const data = makeResult([
      makeRow({ kind: HISTORY_KIND.LOGIN_FAILED, ok: false, session_id: 0, message: '' }),
    ])
    render(<LoginHistoryList data={data} isLoading={false} days={90} />)
    expect(screen.getByText('Sai mật khẩu')).toBeInTheDocument()
  })

  it('hides the heading line when the host already has its own title', () => {
    render(
      <LoginHistoryList data={makeResult([makeRow()])} isLoading={false} days={90} heading={false} />,
    )
    expect(screen.queryByText(/Lịch sử 90 ngày/)).not.toBeInTheDocument()
    expect(screen.queryByText(/lần đăng nhập ·/)).not.toBeInTheDocument()
    expect(screen.getByText('Chrome trên Windows')).toBeInTheDocument()
  })

  it('previews the first rows and expands to the full list on demand', async () => {
    const total = HISTORY_PREVIEW_ROWS + 2
    const items = Array.from({ length: total }, (_, i) =>
      makeRow({ session_id: i + 1, at: `2026-09-${String(i + 1).padStart(2, '0')}T08:00:00` }),
    )
    render(<LoginHistoryList data={makeResult(items)} isLoading={false} days={90} />)
    expect(screen.getAllByRole('listitem')).toHaveLength(HISTORY_PREVIEW_ROWS)

    await userEvent.click(screen.getByRole('button', { name: `Xem cả ${total} dòng` }))
    expect(screen.getAllByRole('listitem')).toHaveLength(total)

    await userEvent.click(screen.getByRole('button', { name: 'Thu gọn' }))
    expect(screen.getAllByRole('listitem')).toHaveLength(HISTORY_PREVIEW_ROWS)
  })

  it('offers no toggle when the list fits the preview exactly', () => {
    const items = Array.from({ length: HISTORY_PREVIEW_ROWS }, (_, i) =>
      makeRow({ session_id: i + 1 }),
    )
    render(<LoginHistoryList data={makeResult(items)} isLoading={false} days={90} />)
    expect(screen.getAllByRole('listitem')).toHaveLength(HISTORY_PREVIEW_ROWS)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('shows neither rows nor the empty message while loading', () => {
    render(<LoginHistoryList data={undefined} isLoading days={90} />)
    expect(screen.queryByText(/Chưa ghi nhận/)).not.toBeInTheDocument()
    expect(screen.queryByRole('list')).not.toBeInTheDocument()
  })
})
