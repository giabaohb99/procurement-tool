import { useRef, useState } from 'react'

import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import type { WorkRosterInteraction, WorkRosterItem } from '../types/work-roster'
import type { WorkShiftTarget } from '../types/work-shift'
import {
  canArrangeShifts,
  pickArrangeableEmployeeIds,
  pickCopyWeekDefaultIds,
  viewerDepartmentIds,
} from '../utils/work-shift-access'

/**
 * Sau khi hộp xếp ca đóng, bỏ qua lượt mở ô trong khoảng này. Lỗi đã gặp khi thử trên trình duyệt (16/11): hộp đóng
 * xong thì một cú bấm / sự kiện con trỏ còn dư rơi xuống ô lưới ngay dưới chỗ nút vừa bấm → hộp của NGƯỜI KHÁC tự mở.
 */
export const REOPEN_GUARD_MS = 400

/** Đồng hồ tách ra ngoài hook: chỉ gọi trong trình xử lý sự kiện, không bao giờ trong lúc render. */
function nowMs(): number {
  return Date.now()
}

/**
 * Trạng thái XẾP CA trên màn Xem lịch (duoc-CR-761): ô đang mở hộp xếp ca, dòng đang chọn cho Chép tuần trước.
 * Người không có khóa xếp ca nào → `interaction` rỗng, lưới chỉ xem như trước.
 *
 * Dòng chọn giữ theo id; đổi trang / bộ lọc thì id không còn trên trang tự rơi khỏi `selectedIds` (giao với các dòng
 * sửa được đang hiện), không cần effect dọn.
 */
export function useRosterShiftEditing(items: readonly WorkRosterItem[], options: { selectable: boolean }) {
  const { user } = useAuth()
  const { can } = usePermission()
  const canArrange = canArrangeShifts(can)
  const viewer = { employeeId: user?.employee_id }

  const [target, setTarget] = useState<WorkShiftTarget | null>(null)
  const [picked, setPicked] = useState<Set<number>>(new Set())
  const [copyOpen, setCopyOpen] = useState(false)
  const closedAt = useRef(0)

  const arrangeableIds = pickArrangeableEmployeeIds(
    can,
    items.map((i) => i.employee_id),
    viewer,
  )
  const arrangeable = new Set(arrangeableIds)
  const selectedIds = arrangeableIds.filter((id) => picked.has(id))

  const toggle = (id: number) =>
    setPicked((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })

  //  Chạy trong trình xử lý sự kiện (không trong lúc render) nên đọc đồng hồ / ref ở đây là đúng luật hook.
  const openCell = (item: WorkRosterItem, date: string) => {
    if (nowMs() - closedAt.current < REOPEN_GUARD_MS) return
    setTarget({ item, date })
  }
  const closeCell = () => {
    closedAt.current = nowMs()
    setTarget(null)
  }

  const interaction: WorkRosterInteraction | undefined = canArrange
    ? {
        onEditCell: openCell,
        selection: options.selectable
          ? { selectedIds: new Set(selectedIds), canSelect: (id) => arrangeable.has(id), onToggle: toggle }
          : undefined,
      }
    : undefined

  return {
    canArrange,
    interaction,
    target,
    openCell,
    closeCell,
    arrangeableIds,
    /** Không tick dòng nào: chép cho các dòng này (Trưởng phòng: chỉ người phòng mình). */
    copyDefaultIds: pickCopyWeekDefaultIds(can, items, viewer, viewerDepartmentIds(user)),
    selectedIds,
    clearSelection: () => setPicked(new Set()),
    copyOpen,
    setCopyOpen,
  }
}
