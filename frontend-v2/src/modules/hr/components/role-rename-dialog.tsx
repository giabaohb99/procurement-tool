import { useState } from 'react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import type { Role } from '../types/role'

/** Trần độ dài khớp cột `tab_role.name` — backend chặn ở 100 (CR-173). */
const DAI_NHAT = 100

interface RoleRenameDialogProps {
  /** Vai trò đang đổi tên. `null` = đóng hộp. */
  role: Role | null
  onOpenChange: (open: boolean) => void
  onSubmit: (roleId: number, name: string) => void
  pending: boolean
}

/**
 * Đổi tên vai trò trong một HỘP THOẠI riêng.
 *
 * Bản đầu (CR-172) sửa ngay tại dòng: ô nhập chen với hai nút ✓ / ✕ trong cột
 * trái rộng 260px, nên còn chừng 150px cho chữ — tên dài bị cắt ngay lúc đang gõ,
 * và **mã vai trò biến mất** khỏi dòng nên người dùng không còn biết mình đang
 * sửa dòng nào (khách báo 26/08/2026).
 *
 * Hộp thoại giải quyết cả hai: ô nhập rộng cả hàng, mã vai trò hiện nguyên bên
 * trên làm mốc, và không phải bóp gì cho vừa cột.
 */
export function RoleRenameDialog({
  role,
  onOpenChange,
  onSubmit,
  pending,
}: RoleRenameDialogProps) {
  const [ten, setTen] = useState('')

  //  Mở hộp cho một vai trò khác thì nạp lại tên của đúng vai trò đó — gán ngay
  //  trong lúc render, không qua `useEffect` (xem `use-has-changed.ts`).
  if (useHasChanged(role?.id)) setTen(role?.name ?? '')

  const sach = ten.trim()
  const luuDuoc = sach.length > 0 && sach.length <= DAI_NHAT && sach !== role?.name

  function luu() {
    if (!role || !luuDuoc) return
    onSubmit(role.id, sach)
  }

  return (
    <Dialog open={role !== null} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Đổi tên vai trò</DialogTitle>
          <DialogDescription>
            Chỉ đổi TÊN HIỂN THỊ. Mã vai trò là khóa của ma trận phân quyền nên không sửa được.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">Mã vai trò</Label>
            {/*  Hiện mã để biết đang sửa dòng nào — thứ bản sửa-tại-dòng làm mất. */}
            <p className="rounded-lg border bg-muted/35 px-3 py-2 font-mono text-sm">
              {role?.code}
            </p>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="ten-vai-tro">
              Tên vai trò <span className="text-destructive">*</span>
            </Label>
            <Input
              id="ten-vai-tro"
              autoFocus
              value={ten}
              maxLength={DAI_NHAT}
              onChange={(e) => setTen(e.target.value)}
              onKeyDown={(e) => {
                if (e.nativeEvent.isComposing) return
                if (e.key === 'Enter') {
                  e.preventDefault()
                  luu()
                }
              }}
            />
            {sach.length === 0 && (
              <p className="text-xs text-destructive">
                Tên không được để trống — vai trò không tên là một dòng trắng trong danh sách.
              </p>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button type="button" onClick={luu} disabled={!luuDuoc || pending}>
            Lưu tên
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
