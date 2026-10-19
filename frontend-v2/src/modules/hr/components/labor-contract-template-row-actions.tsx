import { Download, FilePenLine, MoreHorizontal, Pencil, Power, Replace, Trash2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
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
 * Nút thao tác của MỘT dòng mẫu hợp đồng (duoc-CR-610, 07/10/2026 — đại ca: «thu gọn chỗ action»).
 *
 * Trước đây sáu nút biểu tượng đứng ngang (cột 240px) và nhìn na ná nhau. Nay chỉ hai việc làm
 * HẰNG NGÀY nằm ngoài: «Soạn / Xem nội dung» và «Tải tệp». Bốn việc quản trị — Sửa thông tin ·
 * Thay tệp · Ngừng / Bật dùng · Xóa — gom vào menu «⋯» có CHỮ, khỏi phải rê chuột đoán biểu tượng.
 * Nút bị ẨN theo quyền ở đây — quyền thật do backend.
 */
export function LaborContractTemplateRowActions({ template, actions }: LaborContractTemplateRowActionsProps) {
  const hasMenu = actions.canWrite || actions.canDelete
  return (
    //  Chặn nổi bọt: bấm nút không được kích `onRowClick` (nếu sau này gắn).
    <div className="flex items-center gap-0.5" onClick={(e) => e.stopPropagation()}>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="size-8"
        title={actions.canWrite ? 'Soạn nội dung' : 'Xem nội dung'}
        aria-label={`${actions.canWrite ? 'Soạn' : 'Xem'} nội dung mẫu ${template.name}`}
        onClick={() => actions.onEditContent(template)}
      >
        <FilePenLine className="size-4" />
      </Button>
      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="size-8"
        title="Tải tệp mẫu"
        aria-label={`Tải tệp mẫu ${template.name}`}
        onClick={() => actions.onDownload(template)}
      >
        <Download className="size-4" />
      </Button>
      {hasMenu && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="size-8"
              title="Thao tác khác"
              aria-label={`Thao tác khác với mẫu ${template.name}`}
            >
              <MoreHorizontal className="size-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            {actions.canWrite && (
              <>
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
            {actions.canDelete && (
              <>
                {actions.canWrite && <DropdownMenuSeparator />}
                <DropdownMenuItem variant="destructive" onSelect={() => actions.onDelete(template)}>
                  <Trash2 />
                  Xóa mẫu
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </div>
  )
}
