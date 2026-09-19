import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical, Users } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { cn } from '@/shared/utils/cn'
import type { Role } from '@/modules/hr/types/role'

/** Số chip phân hệ in ra; phần dư gom thành "+n". */
const MAX_MODULE_CHIPS = 3

interface RoleListItemProps {
  role: Role
  selected: boolean
  onSelect: (roleId: number) => void
  /**
   * Cho kéo. Tách khỏi `canWrite` vì còn tắt lúc đang lọc theo từ khóa: thứ tự
   * kéo ra trên một danh sách đã lọc không nói lên thứ tự thật.
   */
  canDrag: boolean
  /**
   * Tên phân hệ suy từ ô đã tick (`utils/role-module-summary.ts`), nhiều ô
   * nhất đứng đầu. Rỗng = vai trò chưa tick ô nào.
   */
  modules: string[]
  /**
   * Dòng lẻ tô nền mờ để mắt tách được dòng này với dòng kế (đại ca 19/09/2026:
   * "chia màu xen kẽ cho dễ nhìn"). Tính ở cha theo thứ tự ĐANG HIỆN chứ không
   * dùng `even:` của CSS — lọc xong hay kéo đổi chỗ thì sọc vẫn đều.
   */
  striped: boolean
}

/**
 * MỘT DÒNG vai trò ở cột trái màn Phân quyền: kéo để đổi chỗ, bấm để chọn.
 *
 * Dòng in đủ bốn thứ để không phải mở vai trò ra mới biết nó là gì (bao-CR-428,
 * đại ca 19/09/2026: "ở vai trò thì nó nhỏ, cũng không có giải thích gọn vai
 * trò đó là gì, đọc cũng hơi khó hiểu, dài quá nó còn bị ẩn thông tin"):
 *   • tên — XUỐNG DÒNG chứ không cắt "..."; cột đã nới lên 320px;
 *   • câu mô tả một dòng (seed điền sẵn, sửa được ở tiêu đề khung bên phải);
 *   • số tài khoản đang giữ;
 *   • chip phân hệ suy từ ô đã tick.
 *
 * ⚠️ Dòng KHÔNG còn là một `<button>` bọc tất cả như bản cũ. Nút lồng trong nút
 * là HTML không hợp lệ, và trình duyệt sẽ dựng lại cây DOM theo cách của nó —
 * tay cầm kéo rơi ra ngoài dòng. Nay dòng là một `<div>` chứa hai phần tử bấm
 * được riêng biệt.
 *
 * ⚠️ KHÔNG có nút đổi tên ở đây. Việc đổi tên và sửa mô tả nằm ở tiêu đề khung
 * bên phải — xem `role-name-inline-edit.tsx`.
 */
export function RoleListItem({
  role,
  selected,
  onSelect,
  canDrag,
  modules,
  striped,
}: RoleListItemProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: role.id,
    disabled: !canDrag,
  })
  const shownModules = modules.slice(0, MAX_MODULE_CHIPS)
  const hiddenModules = modules.slice(MAX_MODULE_CHIPS)

  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className={cn(
        'group flex items-start gap-1 rounded-lg pr-1 transition-colors',
        //  Thứ tự ưu tiên nền: đang chọn > rê chuột > sọc xen kẽ > trắng.
        //  Sọc dùng đúng token `row-stripe` của bảng ma trận bên phải cho đồng
        //  bộ — `bg-muted/50` nhạt tới mức nhìn như trắng (đại ca soi ra 19/09).
        selected ? 'bg-primary/10' : cn('hover:bg-accent', striped && 'bg-row-stripe'),
        isDragging && 'relative z-10 opacity-80 shadow-sm',
      )}
    >
      {canDrag && (
        <button
          type="button"
          //  `touch-none`: không có nó thì trên máy có cảm ứng, thao tác kéo bị
          //  trình duyệt hiểu là cuộn trang và không kéo được dòng nào.
          className="cursor-grab touch-none px-1 py-2.5 text-muted-foreground opacity-0 group-hover:opacity-100 focus-visible:opacity-100"
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
        //  Nhãn rõ ràng thay vì để trình đọc màn hình tự ghép mấy dòng chữ —
        //  ghép ra "Nhân sựemployee3 người", dính liền, không có chỗ ngắt.
        aria-label={`Chọn vai trò ${role.name}`}
        aria-current={selected}
        className={cn(
          'min-w-0 flex-1 rounded-lg py-2 text-left text-sm',
          !canDrag && 'pl-3',
        )}
      >
        <span className="flex items-baseline justify-between gap-2">
          <span
            className={cn(
              'min-w-0 break-words font-medium leading-snug',
              selected && 'font-semibold text-primary',
            )}
          >
            {role.name}
          </span>
          {/*  Số người là thứ người quản trị dùng để đoán "xóa vai trò này
               ảnh hưởng ai" — chỉ in khi API có trả (`GET /api/roles`). */}
          {typeof role.user_count === 'number' && (
            <span
              className="flex shrink-0 items-center gap-0.5 text-[11px] tabular-nums text-muted-foreground"
              title={`${role.user_count} tài khoản đang giữ vai trò này`}
            >
              <Users className="size-3" aria-hidden />
              {role.user_count}
            </span>
          )}
        </span>
        <span className="block font-mono text-[11px] font-normal text-muted-foreground">
          {role.code}
        </span>
        {role.description && (
          <span className="mt-0.5 block text-xs font-normal leading-snug text-muted-foreground">
            {role.description}
          </span>
        )}
        <span className="mt-1.5 flex flex-wrap gap-1">
          {modules.length === 0 ? (
            <Badge variant="outline" className="font-normal text-muted-foreground">
              Chưa cấp quyền
            </Badge>
          ) : (
            <>
              {shownModules.map((title) => (
                <Badge key={title} variant="secondary" className="font-normal">
                  {title}
                </Badge>
              ))}
              {hiddenModules.length > 0 && (
                <Badge
                  variant="outline"
                  className="font-normal text-muted-foreground"
                  title={hiddenModules.join(', ')}
                >
                  +{hiddenModules.length}
                </Badge>
              )}
            </>
          )}
        </span>
      </button>
    </div>
  )
}
