import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Check, GripVertical, Pencil, X } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
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
  onRename: (roleId: number, name: string) => void
  renaming: boolean
}

/**
 * MỘT DÒNG vai trò ở cột trái màn Phân quyền: kéo để đổi chỗ, bấm để chọn, bút
 * chì để đổi tên tại chỗ.
 *
 * ⚠️ Dòng KHÔNG còn là một `<button>` bọc tất cả như bản cũ. Nút lồng trong nút
 * là HTML không hợp lệ, và trình duyệt sẽ dựng lại cây DOM theo cách của nó —
 * tay cầm kéo cùng nút bút chì rơi ra ngoài dòng. Nay dòng là một `<div>`, bên
 * trong có ba phần tử bấm được riêng biệt.
 */
export function RoleListItem({
  role,
  selected,
  onSelect,
  canWrite,
  canDrag,
  onRename,
  renaming,
}: RoleListItemProps) {
  const [dangSua, setDangSua] = useState(false)
  const [ten, setTen] = useState(role.name)

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: role.id,
    disabled: !canDrag,
  })

  function batDauSua() {
    setTen(role.name) //  lấy lại tên hiện tại, không giữ bản nháp dở của lần trước
    setDangSua(true)
  }

  function luu() {
    const sach = ten.trim()
    //  Tên rỗng thì thôi, coi như bỏ qua: vai trò không tên thì cả cột trái lẫn
    //  ô chọn vai trò ở tab Người dùng đều hiện một dòng trống.
    if (sach && sach !== role.name) onRename(role.id, sach)
    setDangSua(false)
  }

  if (dangSua) {
    return (
      <div className="flex items-center gap-1 rounded-lg border border-dashed p-2">
        <Input
          autoFocus
          value={ten}
          onChange={(event) => setTen(event.target.value)}
          onKeyDown={(event) => {
            //  Enter lưu, Esc bỏ — và phải chặn nổi bọt: ô này nằm trong `<form>`
            //  của trang, Enter trần là gửi cả form đi.
            if (event.key === 'Enter') {
              event.preventDefault()
              luu()
            }
            if (event.key === 'Escape') setDangSua(false)
          }}
          className="h-8"
          aria-label={`Tên vai trò ${role.code}`}
        />
        <Button
          type="button"
          size="icon-sm"
          variant="ghost"
          title="Lưu tên"
          aria-label="Lưu tên"
          disabled={renaming}
          onClick={luu}
        >
          <Check className="text-emerald-600" />
        </Button>
        <Button
          type="button"
          size="icon-sm"
          variant="ghost"
          title="Bỏ qua"
          aria-label="Bỏ qua"
          onClick={() => setDangSua(false)}
        >
          <X />
        </Button>
      </div>
    )
  }

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
          onClick={batDauSua}
        >
          <Pencil />
        </Button>
      )}
    </div>
  )
}
