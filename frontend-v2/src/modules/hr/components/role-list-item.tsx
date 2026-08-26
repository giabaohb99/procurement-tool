import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical, Pencil } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import type { Role } from '../types/role'

interface RoleListItemProps {
  role: Role
  selected: boolean
  onSelect: (roleId: number) => void
  /** Cho sửa tên + kéo thả. Tắt khi thiếu quyền `role.write`. */
  canWrite: boolean
  /**
   * Cho kéo. Tách khỏi `canWrite` vì còn tắt lúc đang lọc theo từ khóa: thứ tự
   * kéo ra trên một danh sách đã lọc không nói lên thứ tự thật.
   */
  canDrag: boolean
  /** Mở hộp đổi tên cho dòng này. */
  onRename: (role: Role) => void
}

/**
 * MỘT DÒNG vai trò ở cột trái màn Phân quyền: kéo để đổi chỗ, bấm để chọn, bút
 * chì để mở hộp đổi tên.
 *
 * ⚠️ Dòng KHÔNG còn là một `<button>` bọc tất cả như bản cũ. Nút lồng trong nút
 * là HTML không hợp lệ, và trình duyệt sẽ dựng lại cây DOM theo cách của nó —
 * tay cầm kéo cùng nút bút chì rơi ra ngoài dòng. Nay dòng là một `<div>`, bên
 * trong có ba phần tử bấm được riêng biệt.
 *
 * ⚠️ Bút chì MỞ HỘP THOẠI chứ không đổi dòng thành ô nhập. Bản đầu sửa tại dòng
 * thì ô nhập phải chen với hai nút ✓ / ✕ trong cột 260px — còn chừng 150px cho
 * chữ, tên dài bị cắt ngay lúc đang gõ, mà mã vai trò cũng biến mất nên không
 * còn biết đang sửa dòng nào (khách báo 26/08/2026).
 */
export function RoleListItem({
  role,
  selected,
  onSelect,
  canWrite,
  canDrag,
  onRename,
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

      {canWrite && (
        <Button
          type="button"
          size="icon-sm"
          variant="ghost"
          title="Đổi tên vai trò"
          aria-label={`Đổi tên vai trò ${role.name}`}
          className="opacity-0 group-hover:opacity-100 focus-visible:opacity-100"
          onClick={() => onRename(role)}
        >
          <Pencil />
        </Button>
      )}
    </div>
  )
}
