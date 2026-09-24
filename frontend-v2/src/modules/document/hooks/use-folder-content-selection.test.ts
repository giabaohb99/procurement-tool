import { act, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { useFolderContentSelection } from './use-folder-content-selection'

const FOLDER_KEYS = ['folder:1', 'folder:2']
const DOC_KEYS_PAGE_1 = ['document:10', 'document:11']
const DOC_KEYS_PAGE_2 = ['document:20', 'document:21']

describe('useFolderContentSelection', () => {
  it('bấm chọn hoạt động bình thường qua handleClick (đúng hành vi useItemSelection)', () => {
    const { result } = renderHook(() =>
      useFolderContentSelection({
        folderKeys: FOLDER_KEYS,
        documentKeys: DOC_KEYS_PAGE_1,
        resetSignal: ['folder-A', 1],
      }),
    )
    act(() => result.current.handleClick('document:10', {}))
    expect(Array.from(result.current.selectedIds)).toEqual(['document:10'])
  })

  it('đổi resetSignal (vd chuyển sang thư mục khác) → xóa sạch lựa chọn cũ', () => {
    const { result, rerender } = renderHook(
      ({ resetSignal, documentKeys }) =>
        useFolderContentSelection({ folderKeys: FOLDER_KEYS, documentKeys, resetSignal }),
      { initialProps: { resetSignal: ['folder-A', 1], documentKeys: DOC_KEYS_PAGE_1 } },
    )
    act(() => result.current.handleClick('document:10', {}))
    expect(result.current.selectedIds.size).toBe(1)

    //  Mô phỏng ĐÚNG kịch bản bug đã vá: chọn 2 văn bản ở thư mục A rồi
    //  chuyển sang thư mục B — «Chuyển tới…» không được còn động tới id cũ.
    rerender({ resetSignal: ['folder-B', 1], documentKeys: DOC_KEYS_PAGE_2 })
    expect(result.current.selectedIds.size).toBe(0)
  })

  it('đổi TRANG (cùng thư mục, cùng bộ lọc) cũng xóa lựa chọn — id trang cũ không còn hiển thị', () => {
    const { result, rerender } = renderHook(
      ({ resetSignal, documentKeys }) =>
        useFolderContentSelection({ folderKeys: FOLDER_KEYS, documentKeys, resetSignal }),
      { initialProps: { resetSignal: ['folder-A', 1], documentKeys: DOC_KEYS_PAGE_1 } },
    )
    act(() => result.current.handleClick('document:10', {}))
    expect(result.current.selectedIds.size).toBe(1)

    rerender({ resetSignal: ['folder-A', 2], documentKeys: DOC_KEYS_PAGE_2 })
    expect(result.current.selectedIds.size).toBe(0)
  })

  it('resetSignal KHÔNG đổi (render lại vì lý do khác) → giữ nguyên lựa chọn', () => {
    const { result, rerender } = renderHook(
      ({ resetSignal, documentKeys }) =>
        useFolderContentSelection({ folderKeys: FOLDER_KEYS, documentKeys, resetSignal: resetSignal }),
      { initialProps: { resetSignal: ['folder-A', 1], documentKeys: DOC_KEYS_PAGE_1 } },
    )
    act(() => result.current.handleClick('document:10', {}))
    //  Cùng NỘI DUNG nhưng object mới — so bằng JSON.stringify nên vẫn coi là
    //  KHÔNG đổi (đúng chủ đích: tránh mất chọn oan vì tham chiếu đổi giữa
    //  các lượt render không liên quan).
    rerender({ resetSignal: ['folder-A', 1], documentKeys: DOC_KEYS_PAGE_1 })
    expect(result.current.selectedIds.size).toBe(1)
  })

  it('chưa chọn gì mà resetSignal đổi — không nổ, vẫn rỗng', () => {
    const { result, rerender } = renderHook(
      ({ resetSignal }) =>
        useFolderContentSelection({ folderKeys: FOLDER_KEYS, documentKeys: DOC_KEYS_PAGE_1, resetSignal }),
      { initialProps: { resetSignal: ['folder-A', 1] } },
    )
    rerender({ resetSignal: ['folder-B', 1] })
    expect(result.current.selectedIds.size).toBe(0)
  })

  it('chọn dải (Shift) vẫn hoạt động trên tập khóa GỘP (thư mục trước, văn bản sau)', () => {
    const { result } = renderHook(() =>
      useFolderContentSelection({
        folderKeys: FOLDER_KEYS,
        documentKeys: DOC_KEYS_PAGE_1,
        resetSignal: ['folder-A', 1],
      }),
    )
    act(() => result.current.handleClick('folder:2', {})) // neo
    act(() => result.current.handleClick('document:10', { shiftKey: true }))
    //  Dải từ folder:2 (chỉ số 1) tới document:10 (chỉ số 2) trong mảng gộp
    //  [folder:1, folder:2, document:10, document:11].
    expect(Array.from(result.current.selectedIds).sort()).toEqual(['document:10', 'folder:2'].sort())
  })
})
