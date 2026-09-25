import {
  useAddWorkGroupMember,
  useRemoveWorkGroupMember,
  useWorkGroupMembers,
} from '../hooks/use-work-groups'
import { MembersPanel } from './members-panel'

interface GroupMembersPanelProps {
  open: boolean
  groupId: number
  /** Vai trò của CHÍNH mình trên nhóm. */
  myRole: number | null
}

/**
 * Khối THÀNH VIÊN của hộp Quản lý nhóm — bao-CR-482.
 *
 * Người trong nhóm kế thừa vai trò xuống MỌI dự án bên trong nhóm (A-09), nên
 * mời một người vào đây là cấp quyền cho cả cụm một lần. Đổi vai trò đi cùng cửa
 * «mời» (backend cập nhật tại chỗ khi đã có), không có endpoint riêng như dự án.
 */
export function GroupMembersPanel({ open, groupId, myRole }: GroupMembersPanelProps) {
  const { data: members = [] } = useWorkGroupMembers(open ? groupId : undefined)
  const addMember = useAddWorkGroupMember(groupId)
  const removeMember = useRemoveWorkGroupMember(groupId)

  return (
    <MembersPanel
      open={open}
      members={members}
      myRole={myRole}
      subject="nhóm này"
      isInviting={addMember.isPending}
      onInvite={(employee_id, role) => addMember.mutate({ employee_id, role })}
      onChangeRole={(employee_id, role) => addMember.mutate({ employee_id, role })}
      onRemove={(memberId) => removeMember.mutate(memberId)}
    />
  )
}
