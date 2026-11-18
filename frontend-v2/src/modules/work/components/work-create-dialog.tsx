import { useState } from 'react'

import { useAuth } from '@/core/auth/use-auth'
import { Button } from '@/shared/ui/button'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { useWorkGroupMembers } from '../hooks/use-work-groups'
import { useCreateWorkGroup, useCreateWorkList } from '../hooks/use-work-lists'
import { WorkCreateGroupMembersPicker } from './work-create-group-members-picker'

interface WorkCreateDialogProps {
  /** `list` = tạo dự án · `group` = tạo nhóm dự án (trên dữ liệu là NHÓM, `WorkGroup`). */
  mode: 'list' | 'group' | null
  /** Nhóm dự án đang chứa (tạo dự án, hoặc nhóm con). `null` = đứng ngoài. */
  parentGroupId: number | null
  onClose: () => void
}

/**
 * Hộp thoại tạo nhanh nhóm dự án hoặc dự án (A-01, A-08).
 *
 * Một hộp thoại cho cả hai vì chúng chỉ khác đúng cái tên: ép thành hai tệp là
 * chép hai lần cùng một biểu mẫu một ô.
 */
export function WorkCreateDialog({ mode, parentGroupId, onClose }: WorkCreateDialogProps) {
  const [ten, setTen] = useState('')
  const createList = useCreateWorkList()
  const createGroup = useCreateWorkGroup()

  //  Nhớ kiểu của lần MỞ gần nhất: tạo xong thì `mode` về `null` NGAY, trong lúc
  //  hộp thoại còn đang mờ dần — đọc thẳng `mode` thì tiêu đề nháy sang "Tạo
  //  dự án" ở hộp vừa tạo nhóm dự án.
  const [shownMode, setShownMode] = useState(mode)
  if (mode !== null && mode !== shownMode) setShownMode(mode)

  const laNhom = shownMode === 'group'
  const dangLuu = createList.isPending || createGroup.isPending
  const tieuDe = laNhom ? (parentGroupId ? 'Tạo nhóm con' : 'Tạo nhóm dự án') : 'Tạo dự án'

  //  duoc-CR-783: tạo dự án TRONG một nhóm thì hỏi có gán thành viên nhóm vào dự án không (bật sẵn, chọn sẵn hết).
  const groupForMembers = !laNhom && mode !== null && parentGroupId ? parentGroupId : undefined
  const groupMembers = useWorkGroupMembers(groupForMembers)
  const { user } = useAuth()
  const [assign, setAssign] = useState(true)
  const [excluded, setExcluded] = useState<Set<number>>(() => new Set())
  //  Người tạo luôn là chủ dự án — không đưa vào danh sách chọn.
  const pickable = (groupMembers.data ?? []).filter((m) => m.employee_id !== user?.employee_id)

  function dong() {
    setTen('')
    setAssign(true)
    setExcluded(new Set())
    onClose()
  }

  const waitingMembers = Boolean(groupForMembers) && assign && groupMembers.isLoading

  function luu() {
    const value = ten.trim()
    //  Enter trong ô tên cũng gọi vào đây — nút Tạo bị khóa chưa đủ chặn lúc danh sách thành viên nhóm còn đang tải.
    if (!value || dangLuu || waitingMembers) return
    if (laNhom) {
      createGroup.mutate({ name: value, parent_id: parentGroupId }, { onSuccess: dong })
      return
    }
    const memberIds =
      groupForMembers && assign
        ? pickable.filter((m) => !excluded.has(m.employee_id)).map((m) => m.employee_id)
        : undefined
    createList.mutate(
      { name: value, group_id: parentGroupId, member_employee_ids: memberIds },
      { onSuccess: dong },
    )
  }

  return (
    <Dialog open={mode !== null} onOpenChange={(open) => !open && dong()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{tieuDe}</DialogTitle>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="work-create-name">Tên</Label>
          <Input
            id="work-create-name"
            autoFocus
            value={ten}
            onChange={(e) => setTen(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && luu()}
            placeholder={laNhom ? 'Ví dụ: Chuyển đổi số' : 'Ví dụ: Triển khai ERP v2'}
          />
        </div>

        {groupForMembers && (
          <WorkCreateGroupMembersPicker
            members={pickable}
            isLoading={groupMembers.isLoading}
            assign={assign}
            onAssignChange={setAssign}
            excluded={excluded}
            onExcludedChange={setExcluded}
          />
        )}

        <DialogFooter>
          <Button variant="outline" onClick={dong}>
            Hủy
          </Button>
          {/*  Chờ danh sách thành viên nhóm tải xong mới cho tạo: bấm sớm là gửi danh sách rỗng, dự án ra đời thiếu người. */}
          <Button onClick={luu} disabled={!ten.trim() || dangLuu || waitingMembers}>
            Tạo
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
