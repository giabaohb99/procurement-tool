import { Archive, FolderInput, FolderMinus, FolderKanban, MoreHorizontal, Trash2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { cn } from '@/shared/utils/cn'

import { useProjectRemoveActions } from '../hooks/use-project-remove-actions'
import { useUpdateWorkList } from '../hooks/use-work-lists'
import { WORK_ROLE, type WorkList } from '../types/work'
import type { FlatWorkGroup } from '../utils/work-groups'

interface ListRowMenuProps {
  item: WorkList
  /** Mọi nhóm trong cây (đã duỗi phẳng) — nguồn cho mục "Chuyển sang nhóm". */
  groups: FlatWorkGroup[]
  className?: string
}

/**
 * Nút "…" của một dòng dự án ở cây bên trái: *Chuyển sang nhóm*, *Đưa vào lưu trữ* và *Xóa vĩnh viễn* (duoc-CR-783).
 *
 * Anh Được: "làm chỗ xóa ở bên này, nhấn vào icon … hiện ra rồi xóa" và "có 2 chức năng là xóa vĩnh viễn và đưa vào lưu
 * trữ", "có chức năng di chuyển nhóm luôn". Chỉ CHỦ dự án thấy nút (backend gác cả ba bằng `CAN_OWN`); người khác không có
 * gì để làm ở menu này nên không vẽ.
 *
 * Chuyển nhóm chỉ liệt kê nhóm mình QUẢN TRỊ được (backend đòi `CAN_MANAGE` ở nhóm đích — liệt kê nhóm khác là mời bấm để
 * ăn 403), bỏ nhóm đang ở và nhóm đã lưu trữ. Dự án đang trong nhóm thì có thêm *Bỏ khỏi nhóm* (gửi `group_id = 0`).
 */
export function ListRowMenu({ item, groups, className }: ListRowMenuProps) {
  const { archiveProject, purgeProject } = useProjectRemoveActions(item)
  const update = useUpdateWorkList()

  if (item.my_role !== WORK_ROLE.OWNER) return null

  const targets = groups.filter(
    (g) => g.is_archived !== 1 && g.my_role !== null && g.my_role <= WORK_ROLE.ADMIN && g.id !== item.group_id,
  )
  const moveTo = (groupId: number) => update.mutate({ id: item.id, values: { group_id: groupId } })

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          title="Thao tác với dự án"
          aria-label={`Thao tác với dự án ${item.name}`}
          className={cn('size-6 data-[state=open]:opacity-100', className)}
        >
          <MoreHorizontal className="size-3.5" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start">
        {(targets.length > 0 || Boolean(item.group_id)) && (
          <>
            <DropdownMenuSub>
              <DropdownMenuSubTrigger>
                <FolderInput className="size-4" />
                Chuyển sang nhóm
              </DropdownMenuSubTrigger>
              <DropdownMenuSubContent className="max-h-72 overflow-y-auto">
                {targets.map((g) => (
                  <DropdownMenuItem key={g.id} onSelect={() => moveTo(g.id)}>
                    <FolderKanban className="size-4" />
                    <span style={{ paddingLeft: g.depth * 12 }}>{g.name}</span>
                  </DropdownMenuItem>
                ))}
                {Boolean(item.group_id) && (
                  <>
                    {targets.length > 0 && <DropdownMenuSeparator />}
                    <DropdownMenuItem onSelect={() => moveTo(0)}>
                      <FolderMinus className="size-4" />
                      Bỏ khỏi nhóm
                    </DropdownMenuItem>
                  </>
                )}
              </DropdownMenuSubContent>
            </DropdownMenuSub>
            <DropdownMenuSeparator />
          </>
        )}
        <DropdownMenuItem onSelect={() => void archiveProject()}>
          <Archive className="size-4" />
          Đưa vào lưu trữ
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem className="text-destructive focus:text-destructive" onSelect={() => void purgeProject()}>
          <Trash2 className="size-4" />
          Xóa vĩnh viễn
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
