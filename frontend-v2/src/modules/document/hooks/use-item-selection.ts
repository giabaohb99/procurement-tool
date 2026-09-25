import { useCallback, useEffect, useRef, useState } from 'react'

/** Phím bổ trợ đọc thẳng từ sự kiện chuột/bàn phím gốc — không đòi cả `MouseEvent`. */
export interface SelectionModifierKeys {
  ctrlKey?: boolean
  metaKey?: boolean
  shiftKey?: boolean
}

/**
 * Con trỏ đang gõ trong ô nhập/vùng soạn thảo — dùng để CHẶN phím tắt toàn
 * trang (Esc/Ctrl+A ở đây, và `Delete` xóa lượt chọn ở
 * `folder-selection-toolbar.tsx`) khi người dùng đang gõ chữ, không phải đang
 * thao tác trên danh sách. Xuất ra ngoài để nơi khác dùng LẠI đúng luật này
 * thay vì tự chép một bản.
 */
export function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false
  return target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable
}

/**
 * CHỌN NHIỀU MỤC kiểu Google Drive — bấm = chọn một, Ctrl/⌘+bấm = thêm/bớt,
 * Shift+bấm = chọn DẢI liên tục theo `orderedIds` hiện tại, Esc = bỏ chọn,
 * Ctrl/⌘+A = chọn hết. Dùng chung cho khung nội dung thư mục — id ở đây là
 * chuỗi vì một dòng chọn được có thể là THƯ MỤC hay VĂN BẢN (khác
 * `useRowSelection`, id số, chỉ một loại đối tượng); nơi gọi tự đặt tiền tố
 * (`folder:5`, `doc:12`) rồi tách ra khi thật sự cần gọi API.
 *
 * `orderedIds` PHẢI là thứ tự HIỂN THỊ hiện tại (đổi trang/đổi bộ lọc thì
 * mảng này đổi theo) — Shift+bấm dò theo đúng mảng đó tại THỜI ĐIỂM bấm, dò
 * trên id không còn trong mảng thì rơi về chọn một (không đoán, không nổ).
 *
 * Phím tắt Esc/Ctrl+A gắn ở `window` (Drive hoạt động dù con trỏ đang ở đâu
 * trong khung nội dung, không cần focus đúng một phần tử) — tự bỏ qua khi con
 * trỏ đang gõ trong ô nhập/vùng soạn thảo, và tự tháo khi `enabled=false`
 * (màn khác đang mở, vd hộp thoại, không nên nuốt Esc/Ctrl+A của nó).
 */
export function useItemSelection(orderedIds: readonly string[], enabled = true) {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  //  Neo của dải Shift — KHÔNG dời theo mỗi lần Shift+bấm, chỉ dời khi bấm
  //  thường/Ctrl+bấm, đúng hành vi Drive (dải luôn tính từ điểm bắt đầu ban đầu).
  const anchorRef = useRef<string | null>(null)

  const clear = useCallback(() => {
    setSelectedIds(new Set())
    anchorRef.current = null
  }, [])

  const selectAll = useCallback(() => {
    setSelectedIds(new Set(orderedIds))
    anchorRef.current = orderedIds[orderedIds.length - 1] ?? null
  }, [orderedIds])

  const selectOnly = useCallback((id: string) => {
    setSelectedIds(new Set([id]))
    anchorRef.current = id
  }, [])

  const toggle = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
    anchorRef.current = id
  }, [])

  const selectRange = useCallback(
    (id: string) => {
      const anchor = anchorRef.current
      const from = anchor ? orderedIds.indexOf(anchor) : -1
      const to = orderedIds.indexOf(id)
      //  Không có neo, hoặc neo/đích không còn trong danh sách hiển thị hiện
      //  tại (đổi trang/bộ lọc giữa hai lần bấm) — rơi về chọn MỘT, không đoán.
      if (from === -1 || to === -1) {
        selectOnly(id)
        return
      }
      const [start, end] = from <= to ? [from, to] : [to, from]
      setSelectedIds(new Set(orderedIds.slice(start, end + 1)))
      //  Neo GIỮ NGUYÊN — không gán lại `anchorRef.current = id`.
    },
    [orderedIds, selectOnly],
  )

  const handleClick = useCallback(
    (id: string, modifiers: SelectionModifierKeys) => {
      if (modifiers.shiftKey) selectRange(id)
      else if (modifiers.ctrlKey || modifiers.metaKey) toggle(id)
      else selectOnly(id)
    },
    [selectRange, toggle, selectOnly],
  )

  useEffect(() => {
    if (!enabled) return
    function onKeyDown(event: KeyboardEvent) {
      if (isEditableTarget(event.target)) return
      if (event.key === 'Escape') {
        clear()
        return
      }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'a') {
        event.preventDefault()
        selectAll()
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [enabled, clear, selectAll])

  return {
    selectedIds,
    isSelected: useCallback((id: string) => selectedIds.has(id), [selectedIds]),
    handleClick,
    toggle,
    selectOnly,
    clear,
    selectAll,
  }
}
