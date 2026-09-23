import { Copy, MoreHorizontal, Printer, Trash2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { confirm } from '@/shared/ui/confirm-dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { cn } from '@/shared/utils/cn'
import { useDeleteSealRequest } from '../hooks/use-seal-requests'
import type { SealRequest } from '../types/seal-request'
import { SEAL_OUTLINE_BTN } from '../utils/action-button-class'

interface SealRequestMoreMenuProps {
  request: SealRequest
  canCreate: boolean
  canDelete: boolean
}

/**
 * Menu **THAO TÁC KHÁC** của tiêu đề phiếu đóng dấu — In phiếu · Nhân bản · Xóa.
 *
 * ⚠️ Ba việc này cố ý KHÔNG bày thành nút rời (gom lại 22/09/2026). Trước đó
 * tiêu đề có sáu nút một hàng, và hai hạng việc khác hẳn nhau bị trộn chung:
 * *quyết định luồng* (Duyệt · Yêu cầu chỉnh sửa · Từ chối — mỗi phiếu chỉ bấm
 * một lần, đúng người đúng lúc) đứng cạnh *tiện ích* (in, chép, xóa — bấm lúc
 * nào cũng được). Sáu nút ngang còn bóp tiêu đề văn bản xuống còn "Quyết định
 * bổ nhiệm…" — mà tên văn bản mới là thứ người duyệt cần đọc TRƯỚC KHI bấm.
 *
 * Ba việc này ở trong menu vẫn đúng một cú bấm để mở, trong khi cụm quyết định
 * ngoài kia được trả lại chỗ và trọng lượng thị giác.
 */
export function SealRequestMoreMenu({
  request,
  canCreate,
  canDelete,
}: SealRequestMoreMenuProps) {
  const navigate = useNavigate()
  const deleteMutation = useDeleteSealRequest()

  const handleDelete = async () => {
    const ok = await confirm({
      title: 'Xóa phiếu đóng dấu?',
      message:
        `Xóa "${request.title || request.purpose || request.code}". ` +
        'Phiếu và chứng từ đính kèm sẽ bị gỡ, không khôi phục được.',
      confirmLabel: 'Xóa phiếu',
    })
    if (!ok) return

    await deleteMutation.mutateAsync(request.id)
    navigate(appRoutes.approvalSeal.requests)
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="icon"
          className={cn('size-9', SEAL_OUTLINE_BTN)}
          aria-label="Thao tác khác"
          title="Thao tác khác"
          disabled={deleteMutation.isPending}
        >
          <MoreHorizontal className="size-4" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-52">
        <DropdownMenuItem onSelect={() => navigate(appRoutes.approvalSeal.print(request.id))}>
          <Printer />
          In phiếu
        </DropdownMenuItem>

        {canCreate && (
          <DropdownMenuItem
            onSelect={() => navigate(`${appRoutes.approvalSeal.new}?from=${request.id}`)}
          >
            <Copy />
            Nhân bản
          </DropdownMenuItem>
        )}

        {canDelete && (
          <>
            <DropdownMenuSeparator />
            {/*  `onSelect` phải chặn đóng menu: Radix đóng menu ngay khi chọn,
                mà hộp xác nhận lại mở SAU đó — đóng menu trong lúc đang chờ
                `confirm()` làm tiêu điểm nhảy về nút mở menu, người dùng bấm
                Enter là trúng nút đó chứ không trúng hộp thoại. */}
            <DropdownMenuItem
              variant="destructive"
              onSelect={(e) => {
                e.preventDefault()
                void handleDelete()
              }}
            >
              <Trash2 />
              Xóa phiếu
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
