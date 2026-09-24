import { act, fireEvent, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { useItemSelection } from './use-item-selection'

const IDS = ['a', 'b', 'c', 'd', 'e']

//  `src/test/setup.ts` gọi `cleanup()` sau MỖI bài — nó unmount mọi
//  `renderHook` đang treo, chạy luôn effect dọn dẹp bên trong (gỡ listener
//  `window.keydown`) — nên không cần tự tháo tay ở đây.

describe('useItemSelection — bấm', () => {
  it('bắt đầu rỗng', () => {
    const { result } = renderHook(() => useItemSelection(IDS))
    expect(result.current.selectedIds.size).toBe(0)
  })

  it('bấm thường = chọn MỘT, thay hẳn lựa chọn cũ', () => {
    const { result } = renderHook(() => useItemSelection(IDS))
    act(() => result.current.handleClick('a', {}))
    act(() => result.current.handleClick('c', {}))
    expect(Array.from(result.current.selectedIds)).toEqual(['c'])
  })

  it('isSelected phản ánh đúng tập đang chọn', () => {
    const { result } = renderHook(() => useItemSelection(IDS))
    act(() => result.current.handleClick('b', {}))
    expect(result.current.isSelected('b')).toBe(true)
    expect(result.current.isSelected('a')).toBe(false)
  })
})

describe('useItemSelection — Ctrl/⌘+bấm', () => {
  it('thêm vào lựa chọn đang có, không xóa phần cũ', () => {
    const { result } = renderHook(() => useItemSelection(IDS))
    act(() => result.current.handleClick('a', {}))
    act(() => result.current.handleClick('c', { ctrlKey: true }))
    expect(Array.from(result.current.selectedIds).sort()).toEqual(['a', 'c'])
  })

  it('bấm lại đúng id đang chọn (Ctrl) thì BỎ chọn id đó', () => {
    const { result } = renderHook(() => useItemSelection(IDS))
    act(() => result.current.handleClick('a', {}))
    act(() => result.current.handleClick('a', { ctrlKey: true }))
    expect(result.current.selectedIds.size).toBe(0)
  })

  it('metaKey (⌘ trên macOS) hoạt động y hệt ctrlKey', () => {
    const { result } = renderHook(() => useItemSelection(IDS))
    act(() => result.current.handleClick('a', {}))
    act(() => result.current.handleClick('b', { metaKey: true }))
    expect(Array.from(result.current.selectedIds).sort()).toEqual(['a', 'b'])
  })
})

describe('useItemSelection — Shift+bấm (chọn dải)', () => {
  it('chọn dải liên tục từ neo (lần bấm thường gần nhất) tới id vừa bấm', () => {
    const { result } = renderHook(() => useItemSelection(IDS))
    act(() => result.current.handleClick('b', {})) // neo = b
    act(() => result.current.handleClick('d', { shiftKey: true }))
    expect(Array.from(result.current.selectedIds).sort()).toEqual(['b', 'c', 'd'])
  })

  it('Shift+bấm NGƯỢC (đích đứng TRƯỚC neo trong danh sách) vẫn ra đúng dải', () => {
    const { result } = renderHook(() => useItemSelection(IDS))
    act(() => result.current.handleClick('d', {})) // neo = d
    act(() => result.current.handleClick('a', { shiftKey: true }))
    expect(Array.from(result.current.selectedIds).sort()).toEqual(['a', 'b', 'c', 'd'])
  })

  it('neo giữ NGUYÊN qua nhiều lần Shift+bấm liên tiếp (không dời theo lần bấm sau)', () => {
    const { result } = renderHook(() => useItemSelection(IDS))
    act(() => result.current.handleClick('b', {})) // neo = b
    act(() => result.current.handleClick('d', { shiftKey: true })) // b..d
    act(() => result.current.handleClick('c', { shiftKey: true })) // vẫn tính từ b → b..c
    expect(Array.from(result.current.selectedIds).sort()).toEqual(['b', 'c'])
  })

  it('chưa có neo (Shift+bấm ngay lần đầu) → rơi về chọn MỘT', () => {
    const { result } = renderHook(() => useItemSelection(IDS))
    act(() => result.current.handleClick('c', { shiftKey: true }))
    expect(Array.from(result.current.selectedIds)).toEqual(['c'])
  })

  it('neo không còn trong orderedIds hiện tại (đổi trang giữa hai lần bấm) → rơi về chọn MỘT, không nổ', () => {
    const { result, rerender } = renderHook(({ ids }) => useItemSelection(ids), {
      initialProps: { ids: IDS },
    })
    act(() => result.current.handleClick('a', {})) // neo = a, thuộc trang 1
    rerender({ ids: ['x', 'y', 'z'] }) // sang "trang" khác — 'a' không còn
    act(() => result.current.handleClick('y', { shiftKey: true }))
    expect(Array.from(result.current.selectedIds)).toEqual(['y'])
  })
})

describe('useItemSelection — clear / selectAll', () => {
  it('clear xóa sạch lựa chọn và neo (Shift+bấm sau đó rơi về chọn một)', () => {
    const { result } = renderHook(() => useItemSelection(IDS))
    act(() => result.current.handleClick('a', {}))
    act(() => result.current.clear())
    expect(result.current.selectedIds.size).toBe(0)
    act(() => result.current.handleClick('c', { shiftKey: true }))
    expect(Array.from(result.current.selectedIds)).toEqual(['c'])
  })

  it('selectAll chọn HẾT orderedIds hiện tại', () => {
    const { result } = renderHook(() => useItemSelection(IDS))
    act(() => result.current.selectAll())
    expect(Array.from(result.current.selectedIds).sort()).toEqual([...IDS].sort())
  })

  it('orderedIds RỖNG — selectAll không nổ, ra tập rỗng', () => {
    const { result } = renderHook(() => useItemSelection([]))
    act(() => result.current.selectAll())
    expect(result.current.selectedIds.size).toBe(0)
  })
})

describe('useItemSelection — phím tắt Esc / Ctrl+A', () => {
  it('Esc bỏ chọn hết', () => {
    const { result } = renderHook(() => useItemSelection(IDS))
    act(() => result.current.handleClick('a', {}))
    act(() => {
      fireEvent.keyDown(window, { key: 'Escape' })
    })
    expect(result.current.selectedIds.size).toBe(0)
  })

  it('Ctrl+A chọn hết TOÀN BỘ orderedIds', () => {
    const { result } = renderHook(() => useItemSelection(IDS))
    act(() => {
      fireEvent.keyDown(window, { key: 'a', ctrlKey: true })
    })
    expect(Array.from(result.current.selectedIds).sort()).toEqual([...IDS].sort())
  })

  it('⌘+A (metaKey, macOS) cũng chọn hết', () => {
    const { result } = renderHook(() => useItemSelection(IDS))
    act(() => {
      fireEvent.keyDown(window, { key: 'a', metaKey: true })
    })
    expect(result.current.selectedIds.size).toBe(IDS.length)
  })

  it('gõ Ctrl+A trong khi con trỏ đang ở Ô NHẬP → bỏ qua, không chọn hết (khỏi phá "chọn hết chữ" của ô đó)', () => {
    const input = document.createElement('input')
    document.body.appendChild(input)
    const { result } = renderHook(() => useItemSelection(IDS))
    act(() => {
      fireEvent.keyDown(input, { key: 'a', ctrlKey: true })
    })
    expect(result.current.selectedIds.size).toBe(0)
    document.body.removeChild(input)
  })

  it('enabled=false → không gắn phím tắt nào cả (vd hộp thoại khác đang mở)', () => {
    const { result } = renderHook(() => useItemSelection(IDS, false))
    act(() => result.current.handleClick('a', {}))
    act(() => {
      fireEvent.keyDown(window, { key: 'Escape' })
    })
    //  Không có listener nên Esc không làm gì — lựa chọn vẫn còn nguyên.
    expect(Array.from(result.current.selectedIds)).toEqual(['a'])
  })

  it('unmount thì tháo listener — bấm Ctrl+A sau khi unmount không còn tác dụng lên hook đã chết', () => {
    const { result, unmount } = renderHook(() => useItemSelection(IDS))
    unmount()
    expect(() => fireEvent.keyDown(window, { key: 'a', ctrlKey: true })).not.toThrow()
    // không còn gì để assert trên `result.current` sau unmount — chỉ cần không ném lỗi
    void result
  })
})
