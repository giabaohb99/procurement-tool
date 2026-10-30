import { Download, Eye, FilePenLine, MoreHorizontal, Pencil, Power, Replace, Trash2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import type { LaborContractTemplateColumnActions } from '../config/labor-contract-template-columns'
import type { LaborContractTemplate } from '../types/labor-contract'

interface LaborContractTemplateRowActionsProps {
  template: LaborContractTemplate
  actions: LaborContractTemplateColumnActions
}

/**
 * Thao tác của MỘT dòng mẫu hợp đồng: MỘT nút icon "⋯" mở menu, mỗi mục có ICON + CHỮ, chia nhóm
 * "Nội dung" (Soạn / Xem · Tải tệp) và "Quản lý" (Sửa thông tin · Thay tệp · Ngừng / Bật dùng), Xóa
 * tách riêng cuối. Cùng kiểu với cột thao tác bảng hợp đồng (duoc-CR-633) — trước đây hai icon trơn
 * đứng ngoài + menu "⋯" (CR-610) nhìn lệch với bảng bên cạnh. Mục bị ẨN theo quyền — quyền thật do BE.
 */
export function LaborContractTemplateRowActions({ template, actions }: LaborContractTemplateRowActionsProps) {
  const { canWrite, canDelete } = actions
  return (
    //  Chặn nổi bọt: bấm nút không được kích `onRowClick` (nếu sau này gắn).
    <div className="flex items-center" onClick={(e) => e.stopPropagation()}>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="size-8"
            title="Thao tác"
            aria-label={`Thao tác với mẫu ${template.name}`}
          >
            <MoreHorizontal className="size-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-52">
          <DropdownMenuLabel className="text-xs font-normal text-muted-foreground">Nội dung</DropdownMenuLabel>
          <DropdownMenuItem onSelect={() => actions.onEditContent(template)}>
            {canWrite ? <FilePenLine /> : <Eye />}
            {canWrite ? 'Soạn nội dung' : 'Xem nội dung'}
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={() => actions.onDownload(template)}>
            <Download />
            Tải tệp mẫu
          </DropdownMenuItem>
          {canWrite && (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuLabel className="text-xs font-normal text-muted-foreground">Quản lý</DropdownMenuLabel>
              <DropdownMenuItem onSelect={() => actions.onEditInfo(template)}>
                <Pencil />
                Sửa thông tin
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={() => actions.onReplaceFile(template)}>
                <Replace />
                Thay tệp mẫu
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={() => actions.onToggleActive(template)}>
                <Power />
                {template.is_active ? 'Ngừng dùng' : 'Bật dùng'}
              </DropdownMenuItem>
            </>
          )}
          {canDelete && (
            <>
              <DropdownMenuSeparator />
              <DropdownMenuItem variant="destructive" onSelect={() => actions.onDelete(template)}>
                <Trash2 />
                Xóa mẫu
              </DropdownMenuItem>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  )
}
