import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { useAuthStore } from '@/core/auth/auth-store'
import { COLLAPSE_STORAGE_KEY, MAX_REMEMBERED_SCOPES, useRememberedCollapse } from './use-remembered-collapse'

function signIn(id: number) {
  useAuthStore.setState({ user: { id, email: `u${id}@dego.vn`, full_name: `U${id}`, permissions: {} } })
}

beforeEach(() => {
  localStorage.clear()
  signIn(1)
})

afterEach(() => {
  useAuthStore.setState({ user: null })
})

describe('useRememberedCollapse', () => {
  it('starts with nothing collapsed the first time a report is opened', () => {
    const { result } = renderHook(() => useRememberedCollapse<number>('survey-report:survey_request:5'))
    expect(result.current[0].size).toBe(0)
  })

  it('brings back the collapsed phases when the same report is opened again', () => {
    const first = renderHook(() => useRememberedCollapse<number>('survey-report:survey_request:5'))
    act(() => first.result.current[1](new Set([11, 12])))
    first.unmount()

    const again = renderHook(() => useRememberedCollapse<number>('survey-report:survey_request:5'))
    expect([...again.result.current[0]].sort()).toEqual([11, 12])
  })

  it('accepts an updater function, like useState', () => {
    const { result } = renderHook(() => useRememberedCollapse<number>('r:1'))
    act(() => result.current[1](new Set([1])))
    act(() => result.current[1]((current) => new Set([...current, 2])))
    expect([...result.current[0]].sort()).toEqual([1, 2])
  })

  it('keeps each report on its own — collapsing in one does not collapse the other', () => {
    //  Id giai đoạn là số tự tăng của CẢ bảng nên không trùng giữa hai phiếu, nhưng
    //  khóa nhóm của bảng hồ sơ (chuỗi tên giai đoạn) thì trùng — phải tách theo phiếu.
    const a = renderHook(() => useRememberedCollapse<string>('dossier:1'))
    act(() => a.result.current[1](new Set(['Pháp lý'])))

    const b = renderHook(() => useRememberedCollapse<string>('dossier:2'))
    expect(b.result.current[0].size).toBe(0)
  })

  it('reloads from memory when the SAME mount switches to another report', () => {
    //  Lỗi A2 bắt (kh-TM2-1): route `/:id` giữ component khi đổi phiếu; bản đầu chỉ đọc
    //  bộ nhớ lúc mount nên phiếu mới hiện tập của phiếu cũ.
    const view = renderHook(({ scope }) => useRememberedCollapse<number>(scope), {
      initialProps: { scope: 'r:1' },
    })
    act(() => view.result.current[1](new Set([1, 2])))

    view.rerender({ scope: 'r:2' })
    expect(view.result.current[0].size).toBe(0)

    view.rerender({ scope: 'r:1' })
    expect([...view.result.current[0]].sort()).toEqual([1, 2])
  })

  it('writes a click after a report switch into the NEW report only', () => {
    const view = renderHook(({ scope }) => useRememberedCollapse<number>(scope), {
      initialProps: { scope: 'r:1' },
    })
    act(() => view.result.current[1](new Set([1])))
    view.rerender({ scope: 'r:2' })
    act(() => view.result.current[1]((current) => new Set([...current, 9])))

    const stored = JSON.parse(localStorage.getItem(COLLAPSE_STORAGE_KEY) ?? '{}')
    expect(stored['1:r:1']).toEqual([1])
    expect(stored['1:r:2']).toEqual([9])
  })

  it('does not hand one account the layout another account left on the same browser', () => {
    const first = renderHook(() => useRememberedCollapse<number>('r:1'))
    act(() => first.result.current[1](new Set([7])))
    first.unmount()

    signIn(2)
    const other = renderHook(() => useRememberedCollapse<number>('r:1'))
    expect(other.result.current[0].size).toBe(0)
  })

  it('still collapses, without remembering, when there is no scope or no user', () => {
    useAuthStore.setState({ user: null })
    const { result } = renderHook(() => useRememberedCollapse<number>('r:1'))
    act(() => result.current[1](new Set([3])))

    expect(result.current[0].has(3)).toBe(true)
    expect(localStorage.getItem(COLLAPSE_STORAGE_KEY)).toBeNull()
  })

  it('opens cleanly when the stored value is broken', () => {
    localStorage.setItem(COLLAPSE_STORAGE_KEY, '{không phải json')
    const { result } = renderHook(() => useRememberedCollapse<number>('r:1'))
    expect(result.current[0].size).toBe(0)

    act(() => result.current[1](new Set([1])))
    expect(result.current[0].has(1)).toBe(true)
  })

  it('ignores a stored entry of the wrong shape instead of crashing', () => {
    localStorage.setItem(COLLAPSE_STORAGE_KEY, JSON.stringify({ '1:r:1': 'oops', '1:r:2': { ids: 5 } }))
    expect(renderHook(() => useRememberedCollapse<number>('r:1')).result.current[0].size).toBe(0)
    expect(renderHook(() => useRememberedCollapse<number>('r:2')).result.current[0].size).toBe(0)
  })

  it('forgets a report once everything in it is open again', () => {
    const { result } = renderHook(() => useRememberedCollapse<number>('r:1'))
    act(() => result.current[1](new Set([1])))
    act(() => result.current[1](new Set()))

    expect(JSON.parse(localStorage.getItem(COLLAPSE_STORAGE_KEY) ?? '{}')).toEqual({})
  })

  it('keeps only the most recent reports so the store cannot grow without bound', () => {
    for (let i = 0; i <= MAX_REMEMBERED_SCOPES; i += 1) {
      const { result, unmount } = renderHook(() => useRememberedCollapse<number>(`r:${i}`))
      act(() => result.current[1](new Set([i])))
      unmount()
    }

    const stored = JSON.parse(localStorage.getItem(COLLAPSE_STORAGE_KEY) ?? '{}')
    expect(Object.keys(stored)).toHaveLength(MAX_REMEMBERED_SCOPES)
    //  Phiếu cũ nhất bị đẩy ra, phiếu mới nhất còn.
    expect(stored['1:r:0']).toBeUndefined()
    expect(stored[`1:r:${MAX_REMEMBERED_SCOPES}`]).toBeDefined()
  })
})
