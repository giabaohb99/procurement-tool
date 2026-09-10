import { Progress } from '@/shared/ui/progress'
import { cn } from '@/shared/utils/cn'
import type { WorkMember } from '../types/work'
import { nameInitials } from '../utils/name-initials'

/**
 * Ba mẩu hiển thị dùng chung giữa BẢNG dự án (`project-list-page.tsx`) và THẺ
 * dự án ở khổ hẹp (`project-card.tsx`).
 *
 * Để chung một tệp vì cùng một lý do: hai lối nhìn của đúng một dòng dữ liệu.
 * Chép ra hai bản là hai chỗ hiện khác nhau cho cùng một dự án — mà người dùng
 * xoay ngang cái điện thoại là thấy cả hai trong vòng một giây.
 */

/** Vòng tròn chữ tắt. Luật đặt chữ tắt ở `utils/name-initials.ts`, dùng chung
 *  với hộp Quản lý dự án — chép ra hai bản là hai màn hiện khác nhau cho cùng
 *  một người. */
export function MemberAvatar({ member }: { member: WorkMember }) {
  const initials = nameInitials(member.employee_name)
  return (
    <span
      title={member.employee_name || `Nhân sự #${member.employee_id}`}
      className="grid size-6 shrink-0 place-items-center rounded-full border bg-accent text-[10px] font-medium text-accent-foreground"
    >
      {initials}
    </span>
  )
}

/**
 * Tối đa 4 avatar rồi "+n" — dự án đông người mà xếp hết thì cột nong ra, mà
 * bảng chạy `table-fixed` nên phần thừa bị cắt cụt chứ không xuống dòng.
 */
export function MemberStack({ members }: { members: WorkMember[] }) {
  if (members.length === 0) return <span className="text-muted-foreground">—</span>
  return (
    <span className="flex items-center -space-x-1.5">
      {members.slice(0, 4).map((member) => (
        <MemberAvatar key={member.employee_id} member={member} />
      ))}
      {members.length > 4 && (
        <span className="pl-2.5 text-xs text-muted-foreground">+{members.length - 4}</span>
      )}
    </span>
  )
}

/**
 * Thanh tiến độ của một dự án: việc đã xong / tổng số việc.
 *
 * Dự án CHƯA CÓ VIỆC NÀO hiện 0% chứ không phải 100%: `0/0` mà làm tròn thành
 * "xong hết" thì bảng báo một dự án trắng trơn là đã hoàn tất.
 */
export function ProgressCell({
  done,
  total,
  className,
}: {
  done: number
  total: number
  className?: string
}) {
  const percent = total > 0 ? Math.round((done / total) * 100) : 0
  return (
    <span className={cn('flex items-center gap-2', className)} title={`${done}/${total} việc`}>
      <Progress value={percent} className="h-2 flex-1" />
      <span className="w-10 shrink-0 text-right text-xs tabular-nums text-muted-foreground">
        {percent}%
      </span>
    </span>
  )
}
