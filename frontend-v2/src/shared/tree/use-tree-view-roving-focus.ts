import { useRef, useState, type KeyboardEvent } from 'react'

import { resolveTreeKeyAction } from './tree-keyboard-nav'
import type { FlatTreeNode, TreeNode } from './tree-types'

interface UseTreeViewRovingFocusOptions<T> {
  flat: FlatTreeNode<T>[]
  selectedId: string | number | null
  expandedIds: ReadonlySet<string | number>
  onToggleExpand: (id: string | number) => void
  onSelect?: (node: TreeNode<T>) => void
  /**
   * Enter/Space (phím "kích hoạt") — mặc định RƠI VỀ `onSelect` khi bỏ trống
   * (mọi nơi dùng `TreeView` cũ, vd `document-file-tree.tsx`, không đổi hành
   * vi). Nơi nào cần TÁCH "chọn" khỏi "mở" (thư mục văn bản kiểu Drive,
   * duoc-CR-476: bấm chọn+xem trước, Enter/bấm đúp mới thật sự MỞ) thì truyền
   * riêng prop này.
   */
  onActivate?: (node: TreeNode<T>) => void
  onFocusChange?: (node: TreeNode<T>) => void
}

/**
 * Trạng thái + điều hướng bàn phím ROVING TABINDEX (chỉ MỘT dòng nhận
 * `tabIndex=0`) của `TreeView` — tách khỏi `tree-view.tsx` để tệp đó giữ dưới
 * 200 dòng (luật modularization). Quy tắc phím THUẦN vẫn nằm ở
 * `resolveTreeKeyAction` (`tree-keyboard-nav.ts`); hook này chỉ giữ state +
 * gọi hàm đó.
 */
export function useTreeViewRovingFocus<T>({
  flat,
  selectedId,
  expandedIds,
  onToggleExpand,
  onSelect,
  onActivate,
  onFocusChange,
}: UseTreeViewRovingFocusOptions<T>) {
  //  Dòng giữ TIÊU ĐIỂM BÀN PHÍM — khác `selectedId`: bấm chuột chọn một dòng
  //  thì tiêu điểm cũng nên theo tới đó, nhưng dòng đang chọn đổi từ chỗ khác
  //  (dán link `?file=…`) không nhất thiết cây đang có bàn phím.
  const [focusedId, setFocusedId] = useState<string | number | null>(
    selectedId ?? flat[0]?.id ?? null,
  )
  const itemRefs = useRef(new Map<string | number, HTMLDivElement>())

  //  `selectedId` đổi từ NGOÀI (props) → tiêu điểm đi theo. Đặt state NGAY
  //  TRONG lúc render (mẫu "Adjusting state based on a prop change" của React)
  //  thay vì trong `useEffect`: effect chạy SAU khi đã vẽ xong một lượt với
  //  tiêu điểm cũ rồi mới vẽ lại — cascading render không cần thiết, và
  //  `react-hooks/set-state-in-effect` cảnh báo đúng chỗ đó.
  const [prevSelectedId, setPrevSelectedId] = useState(selectedId)
  if (selectedId !== prevSelectedId) {
    setPrevSelectedId(selectedId)
    if (selectedId !== null && selectedId !== undefined) setFocusedId(selectedId)
  }

  function toNode(row: FlatTreeNode<T>): TreeNode<T> {
    return { id: row.id, label: row.label, data: row.data }
  }

  function focusRow(id: string | number) {
    setFocusedId(id)
    itemRefs.current.get(id)?.focus()
    //  CHỈ đường bàn phím đi qua đây (click gọi thẳng `onSelect`, xem
    //  `TreeRow.onClick`) — đúng ngữ nghĩa "tiêu điểm vừa DI CHUYỂN", không lặp
    //  lại lượt bấm chuột.
    const row = flat.find((item) => item.id === id)
    if (row) onFocusChange?.(toNode(row))
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>, index: number) {
    const action = resolveTreeKeyAction(event.key, flat, index, expandedIds)
    if (!action) return
    event.preventDefault()
    if (action.type === 'focus') focusRow(action.id)
    else if (action.type === 'toggle') onToggleExpand(action.id)
    else (onActivate ?? onSelect)?.(toNode(action.row))
  }

  /** Ref CALLBACK cho MỘT dòng cụ thể — `TreeRow` cần một hàm mới mỗi dòng, không phải một hàm chung nhận thêm id. */
  function refCallback(id: string | number) {
    return (el: HTMLDivElement | null) => {
      if (el) itemRefs.current.set(id, el)
      else itemRefs.current.delete(id)
    }
  }

  return { focusedId, setFocusedId, toNode, handleKeyDown, refCallback }
}
