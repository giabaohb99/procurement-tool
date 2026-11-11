import { act, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { useLocalTableSort } from './use-local-table-sort'

//  duoc-CR-748 — trạng thái xếp cục bộ của bảng con Nhân sự.

describe('useLocalTableSort', () => {
  it('sends nothing to the API while no column is chosen, so the backend keeps its own default order', () => {
    const { result } = renderHook(() => useLocalTableSort())
    expect(result.current.sortBy).toBe('')
    expect(result.current.params).toEqual({})
  })

  it('turns a header click into sort_by / sort_dir for the API', () => {
    const { result } = renderHook(() => useLocalTableSort())
    act(() => result.current.onSortChange('full_name', 'desc'))
    expect(result.current.params).toEqual({ sort_by: 'full_name', sort_dir: 'desc' })
  })

  it('drops both parameters on the third click (empty key) instead of sending an empty sort_by', () => {
    //  Gửi `sort_by=` rỗng thì máy chủ đọc như đang xếp theo một cột không tên.
    const { result } = renderHook(() => useLocalTableSort())
    act(() => result.current.onSortChange('code', 'desc'))
    act(() => result.current.onSortChange('', 'desc'))
    expect(result.current.params).toEqual({})
    expect(result.current.sortDir).toBe('asc')
  })

  it('keeps the same params object between renders while the sort is unchanged', () => {
    //  Đối tượng mới mỗi lần dựng thì khóa query đổi liên tục và bảng tự gọi lại API không lý do.
    const { result, rerender } = renderHook(() => useLocalTableSort())
    act(() => result.current.onSortChange('code', 'asc'))
    const first = result.current.params
    rerender()
    expect(result.current.params).toBe(first)
  })
})
