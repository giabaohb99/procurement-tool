import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { SettingHistoryPanel } from './setting-history-panel'
import type { SystemAuditLogItem } from '../api/audit-log-api'
import type * as UseSettingsModule from '../hooks/use-settings'

const refetch = vi.fn()
let state: {
  data: SystemAuditLogItem[] | undefined
  isPending: boolean
  isError: boolean
  isFetching: boolean
}

vi.mock('../hooks/use-settings', async () => {
  //  Trải `actual` chứ không trả mỗi `useSettingHistory`: `SETTING_HISTORY_LIMIT`
  //  cũng nằm trong tệp này và chính component đang đọc nó để in ra câu ghi chú.
  const actual = await vi.importActual<typeof UseSettingsModule>('../hooks/use-settings')
  return { ...actual, useSettingHistory: () => ({ ...state, refetch }) }
})

function makeLog(message: string, extra: Partial<SystemAuditLogItem> = {}): SystemAuditLogItem {
  return {
    id: 1,
    entity: 'setting',
    entity_id: 0,
    action: 'update',
    action_label: 'Cập nhật',
    message,
    by: 'Nguyễn Gia Bảo',
    by_id: 7,
    at: '2026-09-22T09:30:00',
    ...extra,
  }
}

function setLogs(logs: SystemAuditLogItem[] | undefined, over: Partial<typeof state> = {}) {
  state = { data: logs, isPending: false, isError: false, isFetching: false, ...over }
}

beforeEach(() => {
  refetch.mockClear()
  setLogs([])
})

describe('SettingHistoryPanel', () => {
  it('bày người sửa và từng ô đổi từ giá trị gì sang giá trị gì', () => {
    setLogs([
      makeLog(
        'Cập nhật cấu hình hệ thống\nSMTP Host: smtp-relay.brevo.com -> smtp.larksuite.com',
      ),
    ])
    render(<SettingHistoryPanel />)

    expect(screen.getByText('Nguyễn Gia Bảo')).toBeInTheDocument()
    expect(screen.getByText('SMTP Host')).toBeInTheDocument()
    expect(screen.getByText('smtp-relay.brevo.com')).toBeInTheDocument()
    expect(screen.getByText('smtp.larksuite.com')).toBeInTheDocument()
  })

  it('giữ nguyên văn dòng của khóa bí mật thay vì nuốt mất nó', () => {
    //  Dòng này không có cặp trước/sau (giá trị mật không bao giờ vào nhật ký).
    //  Bỏ qua nó là giấu mất việc ai đó vừa đổi mật khẩu SMTP.
    setLogs([
      makeLog(
        'Cập nhật cấu hình hệ thống\nMật khẩu SMTP: đã đặt giá trị mới (không ghi giá trị vào nhật ký)',
      ),
    ])
    render(<SettingHistoryPanel />)

    expect(
      screen.getByText('Mật khẩu SMTP: đã đặt giá trị mới (không ghi giá trị vào nhật ký)'),
    ).toBeInTheDocument()
  })

  it('vẫn đọc được bản ghi cũ chỉ có mỗi câu tóm tắt', () => {
    setLogs([makeLog('Cập nhật cấu hình hệ thống')])
    render(<SettingHistoryPanel />)

    expect(screen.getByText('Cập nhật cấu hình hệ thống')).toBeInTheDocument()
  })

  it('lùi về nhãn hành động khi message rỗng, không để dòng trắng không ai hiểu', () => {
    setLogs([makeLog('')])
    render(<SettingHistoryPanel />)

    expect(screen.getByText('Cập nhật')).toBeInTheDocument()
  })

  it('phân biệt lỗi đọc nhật ký với chưa có lần cập nhật nào', () => {
    setLogs(undefined, { isError: true })
    const { unmount } = render(<SettingHistoryPanel />)
    expect(screen.getByText(/Không đọc được nhật ký thay đổi/)).toBeInTheDocument()
    expect(screen.queryByText(/Chưa có lần cập nhật nào/)).not.toBeInTheDocument()
    unmount()

    setLogs([])
    render(<SettingHistoryPanel />)
    expect(screen.getByText(/Chưa có lần cập nhật nào/)).toBeInTheDocument()
  })
})
