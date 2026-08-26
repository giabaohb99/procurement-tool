import { Check, Pencil, X } from 'lucide-react'
import { useState } from 'react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import type { Role } from '../types/role'

/** Trần độ dài khớp cột `tab_role.name` — backend chặn ở 100 (CR-173). */
const DAI_NHAT = 100

interface RoleNameInlineEditProps {
  role: Role
  canWrite: boolean
  pending: boolean
  onRename: (roleId: number, name: string) => void
}

/**
 * Tên vai trò ở ĐẦU KHUNG MA TRẬN, sửa ngay tại chỗ.
 *
 * Đây là lần thứ ba bố trí chỗ sửa tên, nên ghi lại cho khỏi quay vòng:
 *
 *  1. Sửa tại dòng trong CỘT TRÁI (CR-172) — hỏng: cột rộng 260px, ô nhập chen
 *     với hai nút nên còn ~150px, tên dài bị cắt lúc đang gõ, và **mã vai trò
 *     biến mất** nên không biết đang sửa dòng nào.
 *  2. Hộp thoại (CR-179) — rộng rãi nhưng khách không muốn bật popup cho một
 *     việc nhỏ.
 *  3. **Tại đây** — đúng chỗ: tiêu đề của khung bên phải chiếm gần trọn bề ngang
 *     màn, và **mã vai trò nằm ngay dưới, không bao giờ mất**. Không phải bóp gì
 *     cho vừa, cũng không phải mở lớp che.
 *
 * Enter lưu, Esc bỏ. KHÔNG lưu khi rời ô (blur): rời ô là thao tác quá dễ xảy ra
 * ngoài ý muốn, mà đây là thứ mọi người trong hệ đều nhìn thấy.
 */
export function RoleNameInlineEdit({
  role,
  canWrite,
  pending,
  onRename,
}: RoleNameInlineEditProps) {
  const [dangSua, setDangSua] = useState(false)
  const [ten, setTen] = useState(role.name)

  //  Đổi sang vai trò khác thì bỏ dở việc sửa và nạp lại tên của vai trò mới.
  if (useHasChanged(role.id)) {
    setDangSua(false)
    setTen(role.name)
  }

  const sach = ten.trim()
  const luuDuoc = sach.length > 0 && sach !== role.name

  function luu() {
    if (!luuDuoc) return
    onRename(role.id, sach)
    setDangSua(false)
  }

  function boQua() {
    setTen(role.name)
    setDangSua(false)
  }

  if (dangSua) {
    return (
      <div>
        <div className="flex items-center gap-1.5">
          <Input
            autoFocus
            value={ten}
            maxLength={DAI_NHAT}
            aria-label={`Tên vai trò ${role.code}`}
            disabled={pending}
            onChange={(e) => setTen(e.target.value)}
            onKeyDown={(e) => {
              //  Bỏ qua khi bộ gõ tiếng Việt đang ghép chữ: Enter lúc đó là
              //  "chốt chữ", không phải "lưu".
              if (e.nativeEvent.isComposing) return
              if (e.key === 'Enter') {
                e.preventDefault()
                luu()
              }
              if (e.key === 'Escape') boQua()
            }}
            className="h-8 w-72 font-semibold"
          />
          <Button
            type="button"
            size="icon-sm"
            variant="ghost"
            title="Lưu tên"
            aria-label="Lưu tên"
            disabled={!luuDuoc || pending}
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
            onClick={boQua}
          >
            <X />
          </Button>
        </div>

        {/*  Mã vai trò ở nguyên chỗ cũ, không nhúc nhích trong lúc sửa — đây
             chính là thứ bản sửa-tại-dòng ở cột trái làm mất. */}
        <p className="mt-1 font-mono text-xs text-muted-foreground">{role.code}</p>

        {sach.length === 0 && (
          <p className="mt-1 text-xs text-destructive">
            Tên không được để trống — vai trò không tên là một dòng trắng trong danh sách.
          </p>
        )}
      </div>
    )
  }

  return (
    <div className="group">
      <div className="flex items-center gap-1.5">
        <p className="font-semibold text-navy dark:text-foreground">{role.name}</p>
        {canWrite && (
          <Button
            type="button"
            size="icon-sm"
            variant="ghost"
            title="Đổi tên vai trò"
            aria-label={`Đổi tên vai trò ${role.name}`}
            className="opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100"
            onClick={() => {
              setTen(role.name)
              setDangSua(true)
            }}
          >
            <Pencil />
          </Button>
        )}
      </div>
      <p className="font-mono text-xs text-muted-foreground">{role.code}</p>
    </div>
  )
}
