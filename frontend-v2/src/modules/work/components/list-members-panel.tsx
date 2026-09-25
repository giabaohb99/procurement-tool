import {
  useAddWorkMember,
  useRemoveWorkMember,
  useSetWorkMemberRole,
  useWorkMembers,
} from '../hooks/use-work-config'
import { MembersPanel } from './members-panel'

interface ListMembersPanelProps {
  open: boolean
  listId: number
  /** Vai trò của CHÍNH mình trên dự án — quyết định hiện nút gì (04 §3). */
  myRole: number | null
}

/**
 * Khối THÀNH VIÊN của hộp Quản lý dự án: mời · đổi vai trò · gỡ (A-02, A-03).
 *
 * Phần thân nằm ở `MembersPanel` (bao-CR-482 tách ra để dùng chung với nhóm);
 * ở đây chỉ nối bốn hook của DỰ ÁN vào.
 *
 * Là phần thân, không tự bọc `Dialog` — nó nằm dưới khối Thông tin trong cùng một
 * hộp, KHÔNG phải một thẻ tab. Quản trị hay phải làm cả hai việc trong một lượt
 * mở, mà tab thì bắt họ nhớ mình đang đứng ở đâu.
 */
export function ListMembersPanel({ open, listId, myRole }: ListMembersPanelProps) {
  const { data: members = [] } = useWorkMembers(open ? listId : undefined)
  const addMember = useAddWorkMember(listId)
  const removeMember = useRemoveWorkMember(listId)
  const setRole = useSetWorkMemberRole(listId)

  return (
    <MembersPanel
      open={open}
      members={members}
      myRole={myRole}
      subject="dự án này"
      isInviting={addMember.isPending}
      onInvite={(employee_id, role) => addMember.mutate({ employee_id, role })}
      onChangeRole={(employee_id, role) => setRole.mutate({ employee_id, role })}
      onRemove={(memberId) => removeMember.mutate(memberId)}
    />
  )
}
