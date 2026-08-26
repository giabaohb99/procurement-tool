import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical } from 'lucide-react'

import { cn } from '@/shared/utils/cn'
import type { Role } from '../types/role'

interface RoleListItemProps {
  role: Role
  selected: boolean
  onSelect: (roleId: number) => void
  /**
   * Cho kéo. Tách khỏi `canWrite` vì còn tắt lúc đang lọc theo từ khóa: thứ tự
   * kéo ra trên một danh sách đã lọc không nói lên thứ tự thật.
   */
  canDrag: boolean
}

/**
 * MỘT DÒNG vai trò ở cột trái màn Phân quyền: kéo để đổi chỗ, bấm để chọn.
 *
 * ⚠️ Dòng KHÔNG còn là một `<button>` bọc tất cả như bản cũ. Nút lồng trong nút
 * là HTML không hợp lệ, và trình duyệt sẽ dựng lại cây DOM theo cách của nó —
 * tay cầm kéo rơi ra ngoài dòng. Nay dòng là một `<div>` chứa hai phần tử bấm
 * được riêng biệt.
 *
 * ⚠️ KHÔNG có nút đổi tên ở đây. Cột này rộng 260px, nhét thêm ô nhập vào là
 * còn ~150px cho chữ và tên dài bị cắt lúc đang gõ. Việc đổi tên nằm ở tiêu đề
 * khung bên phải — xem `role-name-inline-edit.tsx`.
 */
export function RoleListItem({
  role,
  selected,
  onSelect,
  canDrag,
}: RoleListItemProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: role.id,
    disabled: !canDrag,
  })

  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className={cn(
        'group flex items-center gap-1 rounded-lg pr-1 transition-colors',
        selected ? 'bg-primary/10' : 'hover:bg-accent',
        isDragging && 'relative z-10 opacity-80 shadow-sm',
      )}
    >
      {canDrag && (
        <button
          type="button"
          //  `touch-none`: không có nó thì trên máy có cảm ứng, thao tác kéo bị
          //  trình duyệt hiểu là cuộn trang và không kéo được dòng nào.
          className="cursor-grab touch-none px-1 py-2 text-muted-foreground opacity-0 group-hover:opacity-100 focus-visible:opacity-100"
          aria-label={`Kéo để đổi chỗ vai trò ${role.name}`}
          {...attributes}
          {...listeners}
        >
          <GripVertical className="size-4" />
        </button>
      )}

      <button
        type="button"
        onClick={() => onSelect(role.id)}
        //  Nhãn rõ ràng thay vì để trình đọc màn hình tự ghép hai dòng chữ —
        //  ghép ra "Nhân sựemployee", dính liền, không có chỗ ngắt.
        aria-label={`Chọn vai trò ${role.name}`}
        aria-current={selected}
        className={cn(
          'min-w-0 flex-1 rounded-lg py-2 text-left text-sm',
          !canDrag && 'pl-3',
          selected && 'font-semibold text-primary',
        )}
      >
        <span className="block truncate">{role.name}</span>
        <span className="block truncate text-xs font-normal text-muted-foreground">
          {role.code}
        </span>
      </button>

    </div>
  )
}
