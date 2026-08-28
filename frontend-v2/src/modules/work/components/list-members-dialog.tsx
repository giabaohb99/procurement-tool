import { Crown, UserMinus } from 'lucide-react'
import { useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { EmployeeMultiSelect } from '@/shared/ui/employee-multi-select'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import {
  useAddWorkMember,
  useRemoveWorkMember,
  useTransferWorkList,
  useWorkMembers,
} from '../hooks/use-work-config'
import { WORK_ROLE, WORK_ROLE_LABELS } from '../types/work'

interface ListMembersDialogProps {
  open: boolean
  listId: number
  /** Vai trò của CHÍNH mình trên list — quyết định hiện nút gì (04 §3). */
  myRole: number | null
  onClose: () => void
}

/**
 * Mời / gỡ / đổi vai trò thành viên của một danh sách (A-02, A-03, A-04).
 *
 * Nút chuyển quyền sở hữu chỉ hiện với CHỦ list: ma trận §3 cho đúng một người
 * làm việc đó, và backend cũng chặn — đây chỉ là lớp đỡ mắt.
 */
export function ListMembersDialog({ open, listId, myRole, onClose }: ListMembersDialogProps) {
  const { data: members = [] } = useWorkMembers(open ? listId : undefined)
  const addMember = useAddWorkMember(listId)
  const removeMember = useRemoveWorkMember(listId)
  const transfer = useTransferWorkList(listId)

  const [chon, setChon] = useState<number[]>([])
  const [vaiTro, setVaiTro] = useState(String(WORK_ROLE.MEMBER))

  const laChu = myRole === WORK_ROLE.OWNER
  const quanTri = myRole !== null && myRole <= WORK_ROLE.ADMIN

  //  ⚠️ Danh bạ nhân sự là dữ liệu của phân hệ khác. Không có `employee.read`
  //  mà cứ gọi thì người dùng ăn toast 403 ngay lúc mở hộp thoại — đúng cái bẫy
  //  đã dính ở tab «Công nợ» của màn Nhà cung cấp. Thiếu quyền thì ẩn hàng mời,
  //  phần xem danh sách thành viên vẫn chạy vì nó là dữ liệu của chính phân hệ.
  const { can } = usePermission()
  const docDuocDanhBa = can('employee', 'read')
  const { data: danhBa } = useEmployees(
    { page_size: 1000, is_active: true },
    { enabled: open && quanTri && docDuocDanhBa },
  )

  function moi() {
    chon.forEach((employeeId) =>
      addMember.mutate({ employee_id: employeeId, role: Number(vaiTro) }),
    )
    setChon([])
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Thành viên danh sách</DialogTitle>
        </DialogHeader>

        {quanTri && docDuocDanhBa && (
          <div className="flex items-end gap-2">
            <div className="flex-1">
              <EmployeeMultiSelect
                value={chon}
                onChange={setChon}
                employees={danhBa?.items ?? []}
                placeholder="Chọn nhân sự"
              />
            </div>
            <Select value={vaiTro} onValueChange={setVaiTro}>
              <SelectTrigger className="w-36">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {/* Không có OWNER trong danh sách: chủ sở hữu chỉ đổi bằng thao
                    tác chuyển quyền, không gán trực tiếp (backend chặn). */}
                <SelectItem value={String(WORK_ROLE.ADMIN)}>Quản trị</SelectItem>
                <SelectItem value={String(WORK_ROLE.MEMBER)}>Thành viên</SelectItem>
                <SelectItem value={String(WORK_ROLE.VIEWER)}>Khách xem</SelectItem>
              </SelectContent>
            </Select>
            <Button onClick={moi} disabled={chon.length === 0}>
              Mời
            </Button>
          </div>
        )}

        <ul className="divide-y rounded-lg border">
          {members.map((m) => (
            <li key={m.id} className="flex items-center gap-2 px-3 py-2">
              <span className="flex-1 truncate text-sm">
                {m.employee_name || `Nhân sự #${m.employee_id}`}
                {m.employee_code && (
                  <span className="ml-2 text-xs text-muted-foreground">{m.employee_code}</span>
                )}
              </span>
              <span className="text-xs text-muted-foreground">{WORK_ROLE_LABELS[m.role]}</span>

              {laChu && m.role !== WORK_ROLE.OWNER && (
                <Button
                  variant="ghost"
                  size="icon"
                  title="Chuyển quyền sở hữu cho người này"
                  onClick={() => transfer.mutate(m.employee_id)}
                >
                  <Crown className="size-4" />
                </Button>
              )}
              {quanTri && m.role !== WORK_ROLE.OWNER && (
                <Button
                  variant="ghost"
                  size="icon"
                  title="Gỡ khỏi danh sách"
                  onClick={() => removeMember.mutate(m.id)}
                >
                  <UserMinus className="size-4 text-destructive" />
                </Button>
              )}
            </li>
          ))}
          {members.length === 0 && (
            <li className="px-3 py-6 text-center text-sm text-muted-foreground">
              Chưa có ai được mời riêng vào danh sách này.
            </li>
          )}
        </ul>
      </DialogContent>
    </Dialog>
  )
}
