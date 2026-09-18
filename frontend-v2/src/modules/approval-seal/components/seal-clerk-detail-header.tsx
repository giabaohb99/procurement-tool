import { ArrowLeft, Building2, Briefcase, Hash, ShieldCheck, Stamp } from 'lucide-react'
import { useEffect, useRef, type ReactNode } from 'react'

import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Button } from '@/shared/ui/button'
import { CompanyAvatarGroup, type CompanyAvatarItem } from './company-avatar-group'
import { ClerkStatusBadge } from './status-pill'

export interface SealClerkDetailHeaderProps {
  employeeName: string
  employeeCode?: string | null
  departmentName?: string | null
  position?: string | null
  avatar?: string | null
  status: number
  isHead: boolean
  companies: CompanyAvatarItem[]
  isDirty?: boolean
  onBack: () => void
  actions?: ReactNode
}

function initialsOf(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean)
  const picked = words.slice(-2).map((w) => w[0])
  return picked.join('').toUpperCase() || '?'
}

/**
 * Tiêu đề trang CHI TIẾT phân công văn thư đóng dấu.
 *
 * Tích hợp STICKY SCROLL ở đỉnh trang:
 * - Ghim cố định khi cuộn xuống dưới, kèm hiệu ứng nền canvas mờ (`backdrop-blur-md`).
 * - Tự đo chiều cao thực tế bằng ResizeObserver và gán biến CSS `--clerk-header-h`
 *   lên thẻ cha, giúp cột bên phải neo dính chính xác ngay bên dưới.
 * - Hàng 1: Nút Back + Avatar/Tên văn thư + Cụm nút thao tác nghiệp vụ (Lưu, Xóa).
 * - Hàng 2: Dải thông tin tóm tắt (Mã nhân viên, Phòng ban, Chức vụ, Trạng thái, Văn thư tổng/đơn vị, Nhóm công ty).
 */
export function SealClerkDetailHeader({
  employeeName,
  employeeCode,
  departmentName,
  position,
  avatar,
  status,
  isHead,
  companies,
  isDirty,
  onBack,
  actions,
}: SealClerkDetailHeaderProps) {
  const ref = useRef<HTMLElement>(null)

  useEffect(() => {
    const el = ref.current
    const host = el?.parentElement
    if (!el || !host) return

    const observer = new ResizeObserver(() => {
      host.style.setProperty('--clerk-header-h', `${el.offsetHeight}px`)
    })
    observer.observe(el)

    return () => observer.disconnect()
  }, [])

  return (
    <header
      ref={ref}
      className="static top-0 z-20 -mx-4 -mt-4 mb-5 flex flex-col gap-3.5 border-b border-border/50 bg-canvas/95 px-4 pt-4 pb-3.5 backdrop-blur-md lg:sticky lg:-mx-6 lg:-mt-6 lg:px-6 lg:pt-6"
    >
      {/* Hàng 1: Nút Quay lại + Avatar & Tên văn thư + Cụm nút thao tác */}
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <div className="flex min-w-0 flex-1 items-center gap-3">
          <Button
            variant="outline"
            size="icon"
            className="size-9 shrink-0 shadow-2xs"
            aria-label="Về danh sách phân công văn thư"
            onClick={onBack}
          >
            <ArrowLeft className="size-4" />
          </Button>

          <Avatar className="size-10 shrink-0 border border-primary/20 shadow-2xs">
            {avatar && <AvatarImage src={avatar} alt={employeeName} />}
            <AvatarFallback className="bg-primary/10 font-bold text-primary">
              {initialsOf(employeeName)}
            </AvatarFallback>
          </Avatar>

          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h1
                className="line-clamp-1 text-lg font-bold tracking-tight text-navy sm:text-xl dark:text-foreground"
                title={employeeName}
              >
                {employeeName}
              </h1>
              {isDirty && (
                <span className="hidden shrink-0 rounded-full bg-amber-500/10 px-2 py-0.5 text-[11px] font-medium text-amber-600 sm:inline-flex dark:bg-amber-500/20 dark:text-amber-400">
                  Chưa lưu thay đổi
                </span>
              )}
            </div>
            <p className="line-clamp-1 text-xs text-muted-foreground">
              Phân công văn thư đóng dấu {isHead ? '• Văn thư tổng (Đa pháp nhân)' : '• Văn thư đơn vị'}
            </p>
          </div>
        </div>

        {actions && (
          <div className="flex flex-wrap items-center justify-end gap-2">
            {actions}
          </div>
        )}
      </div>

      {/* Hàng 2: Dải thông tin tóm tắt (Metadata Ribbon) */}
      <div className="flex min-w-0 flex-wrap items-center gap-x-4 gap-y-2 text-xs text-muted-foreground">
        {employeeCode && (
          <div className="flex shrink-0 items-center gap-1.5 font-mono font-bold text-primary tabular-nums">
            <Hash className="size-3.5 text-muted-foreground" />
            <span>{employeeCode}</span>
          </div>
        )}

        {employeeCode && <span className="hidden text-border sm:inline" aria-hidden="true">|</span>}

        {departmentName && (
          <>
            <div className="flex shrink-0 items-center gap-1.5 text-foreground/85">
              <Building2 className="size-3.5 text-muted-foreground" />
              <span>{departmentName}</span>
            </div>
            <span className="hidden text-border sm:inline" aria-hidden="true">|</span>
          </>
        )}

        {position && (
          <>
            <div className="flex shrink-0 items-center gap-1.5 text-foreground/85">
              <Briefcase className="size-3.5 text-muted-foreground" />
              <span>{position}</span>
            </div>
            <span className="hidden text-border sm:inline" aria-hidden="true">|</span>
          </>
        )}

        <div className="flex shrink-0 items-center gap-2">
          <ClerkStatusBadge status={status} />
        </div>

        <span className="hidden text-border sm:inline" aria-hidden="true">|</span>

        <div className="flex shrink-0 items-center gap-1.5">
          {isHead ? (
            <span className="inline-flex items-center gap-1 rounded-md bg-purple-500/10 px-2 py-0.5 text-xs font-semibold text-purple-600 dark:bg-purple-500/20 dark:text-purple-300">
              <ShieldCheck className="size-3.5" />
              Văn thư tổng
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 rounded-md bg-muted px-2 py-0.5 text-xs font-medium text-muted-foreground">
              <Stamp className="size-3.5" />
              Văn thư đơn vị
            </span>
          )}
        </div>

        <span className="hidden text-border sm:inline" aria-hidden="true">|</span>

        <div className="flex shrink-0 items-center gap-1.5">
          <CompanyAvatarGroup
            companies={companies}
            maxVisible={3}
            showNameWhenSingle={true}
          />
        </div>
      </div>
    </header>
  )
}
