import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import { rosterCell, rosterItem } from '../components/work-roster-fixture'
import { REOPEN_GUARD_MS, useRosterShiftEditing } from './use-roster-shift-editing'

/*  Lỗi đã gặp trên trình duyệt (16/11): đóng hộp xếp ca xong thì một sự kiện con trỏ còn dư rơi xuống ô lưới ngay dưới
    chỗ vừa bấm → hộp của NGƯỜI KHÁC tự mở. Hook bỏ qua lượt mở ô trong REOPEN_GUARD_MS sau khi đóng. */

const IT = { id: 4, name: 'IT' }
const items = [rosterItem(5, 'An', IT, [rosterCell('2026-10-05')]), rosterItem(6, 'Bình', IT, [rosterCell('2026-10-05')])]

let now = 1_000_000
beforeEach(() => {
  vi.spyOn(Date, 'now').mockImplementation(() => now)
  useAuthStore.setState({
    user: { id: 9, email: 'a@b.com', full_name: 'HR', employee_id: 1, permissions: { work_schedule: { read: true, write: true } } },
  })
})
afterEach(() => vi.restoreAllMocks())

describe('useRosterShiftEditing', () => {
  it('ignores a cell click that lands right after the dialog closed, accepts it once the guard has passed', () => {
    const { result } = renderHook(() => useRosterShiftEditing(items, { selectable: true }))
    act(() => result.current.openCell(items[0], '2026-10-05'))
    expect(result.current.target?.item.employee_id).toBe(5)

    act(() => result.current.closeCell())
    now += 50
    act(() => result.current.interaction?.onEditCell?.(items[1], '2026-10-05'))
    expect(result.current.target).toBeNull()

    now += REOPEN_GUARD_MS
    act(() => result.current.interaction?.onEditCell?.(items[1], '2026-10-05'))
    expect(result.current.target?.item.employee_id).toBe(6)
  })

  it('a viewer without an arranging key gets no interaction at all', () => {
    useAuthStore.setState({ user: { id: 9, email: 'a@b.com', full_name: 'X', employee_id: 1, permissions: { employee: { read: true } } } })
    const { result } = renderHook(() => useRosterShiftEditing(items, { selectable: true }))
    expect(result.current.interaction).toBeUndefined()
  })
})
