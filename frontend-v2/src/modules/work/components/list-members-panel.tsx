import { Search, UserPlus } from 'lucide-react'
import { useMemo, useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { EmployeeMultiSelect } from '@/shared/ui/employee-multi-select'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import {
  useAddWorkMember,
  useRemoveWorkMember,
  useSetWorkMemberRole,
  useWorkMembers,
} from '../hooks/use-work-config'
import { WORK_ROLE } from '../types/work'
import { MemberRoleSelect } from './member-role-select'
import { MemberRow } from './member-row'

/** Từ số người này trở lên mới hiện ô lọc — dưới đó nó chỉ tổ chiếm chỗ. */
const FILTER_THRESHOLD = 8

interface ListMembersPanelProps {
  open: boolean
  listId: number
  /** Vai trò của CHÍNH mình trên dự án — quyết định hiện nút gì (04 §3). */
  myRole: number | null
}

/**
 * Khối THÀNH VIÊN của hộp Quản lý dự án: mời · đổi vai trò · gỡ (A-02, A-03).
 *
 * KHÔNG có chuyển quyền sở hữu — chủ đầu tư chốt 03/09/2026: chủ sở hữu chỉ hiện
 * dạng huy hiệu để nhìn, không đổi được từ giao diện.
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

  const [picked, setPicked] = useState<number[]>([])
  const [inviteRole, setInviteRole] = useState<number>(WORK_ROLE.MEMBER)
  const [keyword, setKeyword] = useState('')

  const canManage = myRole !== null && myRole <= WORK_ROLE.ADMIN

  //  ⚠️ Danh bạ nhân sự là dữ liệu của phân hệ khác. Không có `employee.read` mà
  //  cứ gọi thì người dùng ăn toast 403 ngay lúc mở hộp thoại — đúng cái bẫy đã
  //  dính ở tab «Công nợ» của màn Nhà cung cấp. Thiếu quyền thì ẩn hàng mời, phần
  //  xem danh sách thành viên vẫn chạy vì nó là dữ liệu của chính phân hệ.
  const { can } = usePermission()
  const canReadDirectory = can('employee', 'read')
  const { data: directory } = useEmployees(
    { page_size: 1000, is_active: true },
    { enabled: open && canManage && canReadDirectory },
  )

  //  Chủ sở hữu luôn đứng đầu, rồi tới quyền lớn hơn, cuối cùng theo tên. Backend
  //  đã sắp theo `role, id` nhưng thứ tự trong cùng một vai là thứ tự MỜI — nhìn
  //  như ngẫu nhiên khi dự án đông người.
  const rows = useMemo(() => {
    const kw = keyword.trim().toLowerCase()
    return members
      .filter(
        (m) =>
          !kw ||
          (m.employee_name || '').toLowerCase().includes(kw) ||
          (m.employee_code || '').toLowerCase().includes(kw),
      )
      .slice()
      .sort(
        (a, b) =>
          a.role - b.role || (a.employee_name || '').localeCompare(b.employee_name || '', 'vi'),
      )
  }, [members, keyword])

  function invite() {
    picked.forEach((employeeId) => addMember.mutate({ employee_id: employeeId, role: inviteRole }))
    setPicked([])
  }

  return (
    <section className="space-y-3">
      <header className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-navy dark:text-foreground">
          Thành viên
          <span className="ml-1.5 font-normal text-muted-foreground">({members.length})</span>
        </h3>
        {members.length >= FILTER_THRESHOLD && (
          <div className="relative w-52">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="Lọc theo tên, mã"
              aria-label="Lọc danh sách thành viên"
              className="h-8 pl-8"
            />
          </div>
        )}
      </header>

      {canManage && canReadDirectory && (
        //  Hàng mời nằm trong khung nền mờ để tách hẳn khỏi danh sách bên dưới:
        //  trước đây ô chọn nhân sự dính liền bảng, nhìn như dòng đầu của bảng.
        <div className="flex items-end gap-2 rounded-lg border bg-muted/30 p-2.5">
          <div className="min-w-0 flex-1">
            <EmployeeMultiSelect
              value={picked}
              onChange={setPicked}
              employees={directory?.items ?? []}
              placeholder="Chọn nhân sự để mời"
            />
          </div>
          <MemberRoleSelect
            value={inviteRole}
            onChange={setInviteRole}
            ariaLabel="Vai trò cho người được mời"
            className="w-36 shrink-0"
          />
          <Button onClick={invite} disabled={picked.length === 0 || addMember.isPending}>
            <UserPlus className="size-4" />
            Mời{picked.length > 1 ? ` (${picked.length})` : ''}
          </Button>
        </div>
      )}

      {/*  KHÔNG tự cuộn trong khung. Cả hộp thoại đã cuộn được (overlay lo), và
           khung cuộn lồng trong khung cuộn là thứ làm con lăn chuột chết
           (03/09/2026). Dự án đông người thì hộp dài ra và cuộn một mạch — cũng
           đúng hơn: hàng mời nằm ngay trên, không bị kẹt ngoài vùng cuộn. */}
      <ul className="divide-y rounded-lg border">
        {rows.map((m) => (
          <MemberRow
            key={m.id}
            member={m}
            canManage={canManage}
            onChangeRole={(employeeId, role) => setRole.mutate({ employee_id: employeeId, role })}
            onRemove={(memberId) => removeMember.mutate(memberId)}
          />
        ))}
        {rows.length === 0 && (
          <li className="px-3 py-6 text-center text-sm text-muted-foreground">
            {members.length === 0
              ? 'Chưa có ai được mời riêng vào dự án này.'
              : 'Không có ai khớp từ khóa.'}
          </li>
        )}
      </ul>
    </section>
  )
}
