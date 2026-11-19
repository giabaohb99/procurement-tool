import { useState, type DragEvent } from 'react'

import { WORK_ROLE, type WorkList } from '../types/work'
import { useUpdateWorkList } from './use-work-lists'

/** Đích thả: id nhóm, hoặc `0` = khu "Chưa thuộc nhóm" (đưa dự án ra khỏi nhóm). */
export type SidebarDropTarget = number

/**
 * KÉO THẢ dự án giữa các nhóm ở cây bên trái (duoc-CR-783, anh Được 19/11/2026: "cho chức năng kéo thả đổi nhóm dự án ở
 * menu bên trái").
 *
 * Dùng kéo thả GỐC của trình duyệt chứ không `@dnd-kit` như bảng kanban: ở đây chỉ đổi NHÓM (thả lên tên nhóm), không sắp
 * thứ tự, nên không cần cảm biến / lớp phủ / vùng cuộn tự động. Điện thoại không kéo được — vẫn có menu "…" › Chuyển sang
 * nhóm.
 *
 * Luật giống hệt menu "…": chỉ CHỦ dự án kéo được (`update_list` gác `CAN_OWN`); chỉ thả được lên nhóm mình QUẢN TRỊ
 * (`CAN_MANAGE` ở nhóm đích) và chưa lưu trữ; thả vào nhóm đang ở thì bỏ qua. Trạng thái "đang kéo cái gì" giữ ở đây vì
 * lúc `dragover` trình duyệt không cho đọc dữ liệu kéo.
 */
export function useSidebarListDrag() {
  const update = useUpdateWorkList()
  const [dragging, setDragging] = useState<WorkList | null>(null)
  const [over, setOver] = useState<SidebarDropTarget | null>(null)

  const reset = () => {
    setDragging(null)
    setOver(null)
  }

  const accepts = (target: SidebarDropTarget, allowed: boolean) =>
    allowed && dragging !== null && (dragging.group_id ?? 0) !== target

  /** Thuộc tính cho DÒNG dự án — rỗng khi mình không phải chủ (không kéo được). */
  function dragProps(item: WorkList) {
    if (item.my_role !== WORK_ROLE.OWNER) return {}
    return {
      draggable: true,
      onDragStart: (e: DragEvent) => {
        e.dataTransfer.effectAllowed = 'move'
        e.dataTransfer.setData('text/plain', String(item.id))
        setDragging(item)
      },
      onDragEnd: reset,
    }
  }

  /** Thuộc tính cho ĐÍCH thả (dòng tên nhóm, khu "Chưa thuộc nhóm"). `allowed` = mình có quyền đưa dự án vào đích này. */
  function dropProps(target: SidebarDropTarget, allowed: boolean) {
    return {
      onDragOver: (e: DragEvent) => {
        if (!accepts(target, allowed)) return
        e.preventDefault()
        e.dataTransfer.dropEffect = 'move'
        if (over !== target) setOver(target)
      },
      onDragLeave: (e: DragEvent) => {
        //  Rời sang phần tử con của chính đích thì không tính là rời.
        if (e.currentTarget.contains(e.relatedTarget as Node | null)) return
        setOver((cur) => (cur === target ? null : cur))
      },
      onDrop: (e: DragEvent) => {
        e.preventDefault()
        if (dragging && accepts(target, allowed)) {
          update.mutate({ id: dragging.id, values: { group_id: target } })
        }
        reset()
      },
    }
  }

  return { dragging, over, dragProps, dropProps }
}

export type SidebarListDrag = ReturnType<typeof useSidebarListDrag>
