import { Check, Pencil, Users, X } from 'lucide-react'
import { useState } from 'react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import type { Role } from '@/modules/hr/types/role'

/** Trần độ dài khớp cột `tab_role.name` — backend chặn ở 100 (CR-173). */
const MAX_LENGTH = 100
/** Trần mô tả khớp cột `tab_role.description` (`String(255)`). */
const MAX_DESCRIPTION_LENGTH = 255

interface RoleNameInlineEditProps {
  role: Role
  canWrite: boolean
  pending: boolean
  onRename: (roleId: number, name: string) => void
  /**
   * Sửa câu mô tả. Không truyền thì phần mô tả chỉ đọc (màn cũ, test cũ vẫn
   * chạy nguyên).
   */
  onDescribe?: (roleId: number, description: string) => void
}

/**
 * Tên + mô tả vai trò ở ĐẦU KHUNG MA TRẬN, sửa ngay tại chỗ.
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
 * Mô tả (bao-CR-428) đi cùng cách: một câu ngắn nói vai trò này lo việc gì,
 * bấm vào là sửa, cùng luật Enter lưu / Esc bỏ. Hai ô sửa là HAI trạng thái
 * riêng — đang sửa tên thì mô tả vẫn đọc bình thường và ngược lại.
 *
 * Enter lưu, Esc bỏ. KHÔNG lưu khi rời ô (blur): rời ô là thao tác quá dễ xảy ra
 * ngoài ý muốn, mà đây là thứ mọi người trong hệ đều nhìn thấy.
 */
export function RoleNameInlineEdit({
  role,
  canWrite,
  pending,
  onRename,
  onDescribe,
}: RoleNameInlineEditProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [ten, setTen] = useState(role.name)
  const [isEditingDescription, setIsEditingDescription] = useState(false)
  const [description, setDescription] = useState(role.description)

  //  Đổi sang vai trò khác thì bỏ dở việc sửa và nạp lại tên của vai trò mới.
  if (useHasChanged(role.id)) {
    setIsEditing(false)
    setTen(role.name)
    setIsEditingDescription(false)
    setDescription(role.description)
  }

  const sach = ten.trim()
  const canSave = sach.length > 0 && sach !== role.name
  const cleanDescription = description.trim()
  const canSaveDescription = cleanDescription !== role.description

  function luu() {
    if (!canSave) return
    onRename(role.id, sach)
    setIsEditing(false)
  }

  function cancel() {
    setTen(role.name)
    setIsEditing(false)
  }

  function saveDescription() {
    if (!canSaveDescription || !onDescribe) return
    onDescribe(role.id, cleanDescription)
    setIsEditingDescription(false)
  }

  function cancelDescription() {
    setDescription(role.description)
    setIsEditingDescription(false)
  }

  const userCount =
    typeof role.user_count === 'number' ? (
      <span
        className="inline-flex items-center gap-1 text-xs tabular-nums text-muted-foreground"
        title="Số tài khoản đang giữ vai trò này"
      >
        <Users className="size-3.5" aria-hidden />
        {role.user_count} người đang giữ
      </span>
    ) : null

  const descriptionBlock = isEditingDescription ? (
    <div className="mt-1.5 flex items-center gap-1.5">
      <Input
        autoFocus
        value={description}
        maxLength={MAX_DESCRIPTION_LENGTH}
        placeholder="Một câu: vai trò này lo việc gì?"
        aria-label={`Mô tả vai trò ${role.code}`}
        disabled={pending}
        onChange={(e) => setDescription(e.target.value)}
        onKeyDown={(e) => {
          if (e.nativeEvent.isComposing) return
          if (e.key === 'Enter') {
            e.preventDefault()
            saveDescription()
          }
          if (e.key === 'Escape') cancelDescription()
        }}
        className="h-8 w-full max-w-xl text-sm"
      />
      <Button
        type="button"
        size="icon-sm"
        variant="ghost"
        title="Lưu mô tả"
        aria-label="Lưu mô tả"
        disabled={!canSaveDescription || pending}
        onClick={saveDescription}
      >
        <Check className="text-emerald-600" />
      </Button>
      <Button
        type="button"
        size="icon-sm"
        variant="ghost"
        title="Bỏ qua"
        aria-label="Bỏ qua sửa mô tả"
        onClick={cancelDescription}
      >
        <X />
      </Button>
    </div>
  ) : canWrite && onDescribe ? (
    <button
      type="button"
      title="Sửa mô tả vai trò"
      aria-label={`Sửa mô tả vai trò ${role.name}`}
      className="group mt-1 flex max-w-xl items-start gap-1.5 rounded-md px-1.5 py-0.5 text-left text-sm text-muted-foreground outline-none transition-colors hover:bg-accent focus-visible:ring-[3px] focus-visible:ring-ring/50"
      onClick={() => {
        setDescription(role.description)
        setIsEditingDescription(true)
      }}
    >
      <span className={role.description ? undefined : 'italic'}>
        {role.description || 'Chưa có mô tả — bấm để viết một câu vai trò này lo việc gì.'}
      </span>
      <Pencil className="mt-1 size-3 shrink-0 transition-colors group-hover:text-foreground" />
    </button>
  ) : role.description ? (
    <p className="mt-1 max-w-xl px-1.5 text-sm text-muted-foreground">{role.description}</p>
  ) : null

  if (isEditing) {
    return (
      <div>
        <div className="flex items-center gap-1.5">
          <Input
            autoFocus
            value={ten}
            maxLength={MAX_LENGTH}
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
              if (e.key === 'Escape') cancel()
            }}
            className="h-8 w-72 font-semibold"
          />
          <Button
            type="button"
            size="icon-sm"
            variant="ghost"
            title="Lưu tên"
            aria-label="Lưu tên"
            disabled={!canSave || pending}
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
            onClick={cancel}
          >
            <X />
          </Button>
        </div>

        {/*  Mã vai trò ở nguyên chỗ cũ, không nhúc nhích trong lúc sửa — đây
             chính là thứ bản sửa-tại-dòng ở cột trái làm mất. */}
        <p className="mt-1 flex flex-wrap items-center gap-x-3 font-mono text-xs text-muted-foreground">
          {role.code}
          {userCount}
        </p>

        {sach.length === 0 && (
          <p className="mt-1 text-xs text-destructive">
            Tên không được để trống — vai trò không tên là một dòng trắng trong danh sách.
          </p>
        )}
        {descriptionBlock}
      </div>
    )
  }

  //  Thụt trái 6px để bù `px-1.5` của nút, nhờ vậy chữ "Nhân sự" và mã vai trò
  //  vẫn thẳng hàng với mép khung như khi không có nút.
  if (!canWrite) {
    return (
      <div>
        <p className="font-semibold text-navy dark:text-foreground">{role.name}</p>
        <p className="flex flex-wrap items-center gap-x-3 font-mono text-xs text-muted-foreground">
          {role.code}
          {userCount}
        </p>
        {role.description && (
          <p className="mt-1 max-w-xl text-sm text-muted-foreground">{role.description}</p>
        )}
      </div>
    )
  }

  return (
    <div className="-ml-1.5">
      <button
        type="button"
        title="Đổi tên vai trò"
        aria-label={`Đổi tên vai trò ${role.name}`}
        className="group flex items-center gap-1.5 rounded-md px-1.5 py-0.5 text-left outline-none transition-colors hover:bg-accent focus-visible:ring-[3px] focus-visible:ring-ring/50"
        onClick={() => {
          setTen(role.name)
          setIsEditing(true)
        }}
      >
        <span className="font-semibold text-navy dark:text-foreground">{role.name}</span>
        {/*  Cây bút hiện SẴN, không chờ hover: hover-mới-hiện thì trên máy cảm ứng
             không ai biết tên sửa được, mà cái ô nút 32px của bản cũ còn đội cao
             hàng tiêu đề làm chữ bị canh giữa, nhìn như tụt xuống (khách báo
             26/08/2026). Icon trần 14px nằm gọn trong dòng chữ, không đội gì cả. */}
        <Pencil className="size-3.5 shrink-0 text-muted-foreground transition-colors group-hover:text-foreground" />
      </button>
      <p className="flex flex-wrap items-center gap-x-3 px-1.5 font-mono text-xs text-muted-foreground">
        {role.code}
        {userCount}
      </p>
      {descriptionBlock}
    </div>
  )
}
