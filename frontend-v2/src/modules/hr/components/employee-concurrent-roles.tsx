import { Building2, Users } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/shared/ui/tooltip'
import { CONCURRENT_KIND_COMPANY } from '../types/employee-concurrent'
import type { EmployeeConcurrentRole } from '../types/employee'

/** Biểu tượng nhỏ theo loại: Công ty = tòa nhà, Phòng ban = nhóm người. */
function KindIcon({ kind, className = 'text-muted-foreground' }: { kind: number; className?: string }) {
  const Icon = kind === CONCURRENT_KIND_COMPANY ? Building2 : Users
  return <Icon className={`size-3.5 shrink-0 ${className}`} aria-hidden="true" />
}

/** Danh sách ĐỦ các dòng, mỗi dòng một hàng kèm biểu tượng loại, không cắt chữ. */
function FullList({ roles }: { roles: EmployeeConcurrentRole[] }) {
  return (
    <ul className="space-y-1">
      {roles.map((role, index) => (
        <li key={`${role.kind}-${role.text}-${index}`} className="flex items-start gap-1.5">
          {/*  Tooltip nền đậm / Popover nền sáng: icon theo màu chữ của khung, không dùng màu "muted". */}
          <KindIcon kind={role.kind} className="mt-0.5 opacity-70" />
          <span>{role.text}</span>
        </li>
      ))}
    </ul>
  )
}

/** Mục đầu (thứ tự backend) một dòng, cắt "…" nếu dài, kèm huy hiệu "+N" khi còn nhiều hơn một mục. */
function Summary({ roles }: { roles: EmployeeConcurrentRole[] }) {
  const [first, ...rest] = roles
  return (
    <>
      <KindIcon kind={first.kind} />
      <span className="min-w-0 truncate">{first.text}</span>
      {rest.length > 0 && (
        <Badge variant="outline" className="shrink-0 px-1.5 py-0 text-[11px]">
          +{rest.length}
        </Badge>
      )}
    </>
  )
}

/**
 * Ô "Kiêm nhiệm" của BẢNG danh sách nhân sự (duoc-CR-756): chỉ mục đầu + "+N"; rê chuột / tab tới ô thì
 * Tooltip liệt kê đủ. Rỗng → KHÔNG vẽ gì (ô trống để trống). `sideOffset` + `pointer-events-none` chống
 * giật như `HelpHint` (mũi tooltip đè lên ô làm con trỏ bị tính là rời đi).
 */
export function EmployeeConcurrentRolesCell({ roles }: { roles?: EmployeeConcurrentRole[] }) {
  if (!roles || roles.length === 0) return null
  return (
    <TooltipProvider delayDuration={150}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            tabIndex={0}
            className="flex min-w-0 items-center gap-1.5"
            aria-label={`Kiêm nhiệm: ${roles.map((role) => role.text).join('; ')}`}
          >
            <Summary roles={roles} />
          </span>
        </TooltipTrigger>
        <TooltipContent sideOffset={6} className="pointer-events-none max-w-sm text-pretty">
          <FullList roles={roles} />
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

/**
 * Dòng "Kiêm nhiệm" của THẺ điện thoại: `Kiêm nhiệm: <mục đầu> +N` — chữ thường, KHÔNG tương tác.
 * ⚠️ Cả thẻ là một `<button>` (`DataTableMobileCards` khi có `onRowClick`), nên bên trong tuyệt đối không đặt nút /
 * Popover: `<button>` lồng `<button>` là HTML sai (React báo `validateDOMNesting`, trình đọc màn hình đọc hai nút).
 * Danh sách đủ nằm ở tab Kiêm nhiệm của hồ sơ — chạm thẻ là tới đó; `title` chỉ là tiện cho chuột.
 */
export function EmployeeConcurrentRolesCardLine({ roles }: { roles?: EmployeeConcurrentRole[] }) {
  if (!roles || roles.length === 0) return null
  return (
    <span
      className="flex w-full min-w-0 items-center gap-1.5 text-xs text-muted-foreground"
      title={roles.map((role) => role.text).join('; ')}
    >
      <span className="shrink-0">Kiêm nhiệm:</span>
      <Summary roles={roles} />
    </span>
  )
}
