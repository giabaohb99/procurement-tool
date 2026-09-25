import { Archive } from 'lucide-react'
import { useState } from 'react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { Separator } from '@/shared/ui/separator'
import { Textarea } from '@/shared/ui/textarea'
import { useArchiveWorkGroup, useUpdateWorkGroup } from '../hooks/use-work-groups'
import { WORK_ROLE, type WorkGroup } from '../types/work'
import { GroupMembersPanel } from './group-members-panel'

/** Trần khớp cột `tab_work_group.name` — `String(200)` ở `model.py`. */
export const GROUP_NAME_MAX = 200
export const GROUP_DESCRIPTION_MAX = 1500

interface GroupManageDialogProps {
  open: boolean
  group: WorkGroup | null
  onClose: () => void
}

/**
 * QUẢN LÝ NHÓM DỰ ÁN — bao-CR-482. Cùng khuôn với hộp Quản lý dự án: Thông tin
 * rồi tới Thành viên, một hộp không tab.
 *
 * Trước CR này nhóm chỉ TẠO được: đặt tên xong là không đổi được, không mời ai,
 * không lưu trữ — trong khi cửa API đã có sẵn từ bao-CR-216. Đại ca muốn phân
 * quyền cho cả cụm «DX» một lần thay vì mời từng người vào từng dự án.
 *
 * Hai ngưỡng quyền, theo backend (`group_service.py`):
 *   · sửa thông tin / lưu trữ → `CAN_OWN` (Chủ sở hữu nhóm);
 *   · mời / gỡ / đổi vai trò  → `CAN_MANAGE` (Quản trị trở lên).
 */
export function GroupManageDialog({ open, group, onClose }: GroupManageDialogProps) {
  const myRole = group?.my_role ?? null
  const canEditInfo = myRole === WORK_ROLE.OWNER
  const updateGroup = useUpdateWorkGroup()
  const archiveGroup = useArchiveWorkGroup()

  const [name, setName] = useState(group?.name ?? '')
  const [description, setDescription] = useState(group?.description ?? '')
  const [confirmArchive, setConfirmArchive] = useState(false)
  //  Nạp lại khi mở sang NHÓM KHÁC — chỉnh state trong lượt dựng (khuôn
  //  `useHasChanged`), cùng lý do với `useListInfoForm`.
  if (useHasChanged(group?.id ?? 0)) {
    setName(group?.name ?? '')
    setDescription(group?.description ?? '')
    setConfirmArchive(false)
  }

  if (!group) return null

  const trimmedName = name.trim()
  const isDirty = trimmedName !== group.name || description.trim() !== (group.description ?? '')
  const canSave = Boolean(trimmedName) && isDirty && !updateGroup.isPending

  function save() {
    if (!canSave || !group) return
    updateGroup.mutate({
      id: group.id,
      values: { name: trimmedName, description: description.trim() },
    })
  }

  function archive() {
    if (!group) return
    archiveGroup.mutate(group.id, { onSuccess: onClose })
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Quản lý nhóm</DialogTitle>
        </DialogHeader>

        <div className="space-y-5">
          <section className="space-y-3">
            <h3 className="text-sm font-semibold text-navy dark:text-foreground">Thông tin</h3>
            {canEditInfo ? (
              <>
                <div className="space-y-2">
                  <Label htmlFor="work-group-name">Tên nhóm</Label>
                  <Input
                    id="work-group-name"
                    value={name}
                    maxLength={GROUP_NAME_MAX}
                    onChange={(e) => setName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.nativeEvent.isComposing) return
                      if (e.key === 'Enter') {
                        e.preventDefault()
                        save()
                      }
                    }}
                  />
                  {!trimmedName && (
                    <p className="text-xs text-destructive">Tên nhóm không được để trống.</p>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="work-group-description">Mô tả</Label>
                  <Textarea
                    id="work-group-description"
                    rows={3}
                    value={description}
                    maxLength={GROUP_DESCRIPTION_MAX}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Nhóm này gom những dự án nào…"
                  />
                </div>
              </>
            ) : (
              <>
                <div className="space-y-2">
                  <Label>Tên nhóm</Label>
                  <ReadOnlyValue>{group.name}</ReadOnlyValue>
                </div>
                <div className="space-y-2">
                  <Label>Mô tả</Label>
                  <ReadOnlyValue multiline>{group.description || '—'}</ReadOnlyValue>
                </div>
              </>
            )}
            <p className="text-xs text-muted-foreground">
              Người trong nhóm tự có cùng vai trò trên mọi dự án bên trong nhóm — mời vào đây
              là cấp quyền cho cả cụm một lần.
            </p>
          </section>

          <Separator />
          <GroupMembersPanel open={open} groupId={group.id} myRole={myRole} />
        </div>

        {canEditInfo && (
          <DialogFooter className="sm:justify-between">
            {/*  Lưu trữ đứng riêng bên trái, xa nút Lưu — một cú bấm nhầm là cả
                 nhóm biến khỏi cây (dù khôi phục được qua «Hiện cả dự án lưu trữ»). */}
            <div>
              {confirmArchive ? (
                <span className="flex items-center gap-2 text-sm">
                  <span className="text-muted-foreground">Lưu trữ nhóm này?</span>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={archive}
                    disabled={archiveGroup.isPending}
                  >
                    Lưu trữ
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setConfirmArchive(false)}>
                    Thôi
                  </Button>
                </span>
              ) : (
                <Button variant="ghost" size="sm" onClick={() => setConfirmArchive(true)}>
                  <Archive className="size-4" />
                  Lưu trữ nhóm
                </Button>
              )}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={onClose}>
                Đóng
              </Button>
              <Button onClick={save} disabled={!canSave}>
                Lưu thông tin
              </Button>
            </div>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  )
}
