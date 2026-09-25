import { act, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { useTreeExpansion } from './use-tree-expansion'

describe('useTreeExpansion', () => {
  it('mặc định KHÔNG mở gì cả khi không truyền defaultExpandedIds', () => {
    const { result } = renderHook(() => useTreeExpansion())
    expect(result.current.isExpanded('a')).toBe(false)
    expect(result.current.expandedIds.size).toBe(0)
  })

  it('nhận defaultExpandedIds lúc dựng', () => {
    const { result } = renderHook(() => useTreeExpansion({ defaultExpandedIds: ['a', 'b'] }))
    expect(result.current.isExpanded('a')).toBe(true)
    expect(result.current.isExpanded('c')).toBe(false)
  })

  it('toggle đảo trạng thái một id, không đụng id khác', () => {
    const { result } = renderHook(() => useTreeExpansion())
    act(() => result.current.toggle('a'))
    expect(result.current.isExpanded('a')).toBe(true)
    act(() => result.current.toggle('a'))
    expect(result.current.isExpanded('a')).toBe(false)
  })

  it('expand/collapse riêng lẻ không nổ khi gọi lặp lại (đã mở lại expand, đã đóng lại collapse)', () => {
    const { result } = renderHook(() => useTreeExpansion())
    act(() => result.current.expand('a'))
    act(() => result.current.expand('a'))
    expect(result.current.isExpanded('a')).toBe(true)
    act(() => result.current.collapse('a'))
    act(() => result.current.collapse('a'))
    expect(result.current.isExpanded('a')).toBe(false)
  })

  it('expandAncestors mở đủ mọi id truyền vào, giữ nguyên id đã mở trước đó', () => {
    const { result } = renderHook(() => useTreeExpansion({ defaultExpandedIds: ['x'] }))
    act(() => result.current.expandAncestors(['a', 'b', 'c']))
    expect(result.current.isExpanded('x')).toBe(true)
    expect(result.current.isExpanded('a')).toBe(true)
    expect(result.current.isExpanded('b')).toBe(true)
    expect(result.current.isExpanded('c')).toBe(true)
  })

  it('expandAncestors với mảng rỗng không đổi gì', () => {
    const { result } = renderHook(() => useTreeExpansion({ defaultExpandedIds: ['x'] }))
    const before = result.current.expandedIds
    act(() => result.current.expandAncestors([]))
    expect(result.current.expandedIds).toBe(before)
  })

  it('expandAll thay TOÀN BỘ tập mở bằng danh sách mới, không cộng dồn', () => {
    const { result } = renderHook(() => useTreeExpansion({ defaultExpandedIds: ['x'] }))
    act(() => result.current.expandAll(['a', 'b']))
    expect(result.current.isExpanded('x')).toBe(false)
    expect(result.current.isExpanded('a')).toBe(true)
    expect(result.current.isExpanded('b')).toBe(true)
  })

  it('collapseAll đóng hết, kể cả id truyền lúc dựng', () => {
    const { result } = renderHook(() => useTreeExpansion({ defaultExpandedIds: ['x', 'y'] }))
    act(() => result.current.collapseAll())
    expect(result.current.expandedIds.size).toBe(0)
  })

  it('id số và id chuỗi trùng ký tự (1 và "1") là HAI id khác nhau — Set không tự gộp', () => {
    const { result } = renderHook(() => useTreeExpansion())
    act(() => result.current.expand(1))
    expect(result.current.isExpanded(1)).toBe(true)
    expect(result.current.isExpanded('1')).toBe(false)
  })
})
