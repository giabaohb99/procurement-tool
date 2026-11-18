import { Checkbox } from '@/shared/ui/checkbox'
import { Label } from '@/shared/ui/label'
import { Skeleton } from '@/shared/ui/skeleton'

import { WORK_ROLE, WORK_ROLE_LABELS, type WorkMember } from '../types/work'
import { MemberAvatar } from './project-cells'

interface WorkCreateGroupMembersPickerProps {
  /** Thành viên của nhóm chứa dự án, ĐÃ bỏ chính người tạo (người tạo luôn là chủ dự án). */
  members: WorkMember[]
  isLoading: boolean
  assign: boolean
  onAssignChange: (value: boolean) => void
  /** Người bị BỎ chọn — lưu phần bị bỏ chứ không lưu phần được chọn, để mặc định là chọn hết kể cả khi danh sách tải sau. */
  excluded: ReadonlySet<number>
  onExcludedChange: (value: Set<number>) => void
}

/**
 * Ô tick "Gán thành viên của nhóm vào dự án" + danh sách chọn người trong hộp tạo dự án (duoc-CR-783).
 *
 * Bật sẵn và chọn sẵn mọi người theo yêu cầu anh Được ("có nút check hỏi có muốn gán không và auto = true, có option chọn
 * thành viên"). Vai trò hiện bên phải là vai trò người đó sẽ nhận ở dự án: giữ như ở nhóm, riêng chủ nhóm thành Quản trị
 * vì dự án chỉ có một chủ là người tạo.
 */
export function WorkCreateGroupMembersPicker({
  members,
  isLoading,
  assign,
  onAssignChange,
  excluded,
  onExcludedChange,
}: WorkCreateGroupMembersPickerProps) {
  const chosen = members.filter((m) => !excluded.has(m.employee_id)).length
  const allChosen = members.length > 0 && chosen === members.length

  const toggle = (employeeId: number, on: boolean) => {
    const next = new Set(excluded)
    if (on) next.delete(employeeId)
    else next.add(employeeId)
    onExcludedChange(next)
  }

  return (
    <div className="space-y-2 rounded-lg border bg-muted/30 p-3">
      <div className="flex items-start gap-2">
        <Checkbox
          id="work-create-assign-group"
          checked={assign}
          onCheckedChange={(value) => onAssignChange(value === true)}
          className="mt-0.5"
        />
        <div className="min-w-0">
          <Label htmlFor="work-create-assign-group" className="cursor-pointer">
            Gán thành viên của nhóm vào dự án
          </Label>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Người được chọn thành thành viên của dự án, giữ vai trò như ở nhóm.
          </p>
        </div>
      </div>

      {assign &&
        (isLoading ? (
          <div className="space-y-1.5">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
          </div>
        ) : members.length === 0 ? (
          <p className="py-2 text-center text-xs text-muted-foreground">Nhóm chưa có thành viên nào khác ngoài bạn.</p>
        ) : (
          <div className="rounded-md border bg-background">
            <label className="flex cursor-pointer items-center gap-2 border-b px-2.5 py-1.5 text-xs text-muted-foreground">
              <Checkbox
                checked={allChosen ? true : chosen === 0 ? false : 'indeterminate'}
                onCheckedChange={(value) => onExcludedChange(value === true ? new Set() : new Set(members.map((m) => m.employee_id)))}
                aria-label="Chọn tất cả thành viên nhóm"
              />
              Chọn tất cả
              <span className="ml-auto tabular-nums">
                {chosen}/{members.length} người
              </span>
            </label>
            <ul className="max-h-52 overflow-y-auto py-1">
              {members.map((m) => (
                <li key={m.employee_id}>
                  <label className="flex cursor-pointer items-center gap-2 px-2.5 py-1.5 hover:bg-muted/60">
                    <Checkbox
                      checked={!excluded.has(m.employee_id)}
                      onCheckedChange={(value) => toggle(m.employee_id, value === true)}
                      aria-label={`Gán ${m.employee_name}`}
                    />
                    <MemberAvatar member={m} />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm">{m.employee_name}</span>
                      <span className="block truncate text-xs text-muted-foreground">{m.employee_code}</span>
                    </span>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      {WORK_ROLE_LABELS[Math.max(m.role, WORK_ROLE.ADMIN)]}
                    </span>
                  </label>
                </li>
              ))}
            </ul>
          </div>
        ))}
    </div>
  )
}
