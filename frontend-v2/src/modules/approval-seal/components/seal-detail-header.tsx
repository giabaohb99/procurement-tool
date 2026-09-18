import { ArrowLeft, Calendar, Files, User } from 'lucide-react'
import { useEffect, useRef, type ReactNode } from 'react'

import { Button } from '@/shared/ui/button'
import { formatDateTime } from '@/shared/utils/format-date'
import { CompanyAvatarGroup } from './company-avatar-group'
import { SealStatusBadge } from './status-pill'
import type { SealRequest } from '../types/seal-request'

interface SealDetailHeaderProps {
  request: SealRequest
  onBack: () => void
  actions?: ReactNode
}

/**
 * Tiêu đề trang CHI TIẾT yêu cầu đóng dấu.
 *
 * Tích hợp STICKY SCROLL ở đỉnh trang:
 * - Ghim cố định khi cuộn xuống dưới, kèm hiệu ứng nền canvas mờ (`backdrop-blur-md`).
 * - Tự đo chiều cao thực tế bằng ResizeObserver và gán biến CSS `--seal-header-h`
 *   lên thẻ cha, giúp cột bên phải neo dính chính xác ngay bên dưới.
 * - Hàng 1: Nút Back + Tiêu đề văn bản + Dải nút thao tác nghiệp vụ.
 * - Hàng 2: Dải thông tin tóm tắt (Mã phiếu, Trạng thái, Số bản, Người tạo, Công ty đóng dấu, Ngày tạo).
 */
export function SealDetailHeader({ request, onBack, actions }: SealDetailHeaderProps) {
  const ref = useRef<HTMLElement>(null)

  useEffect(() => {
    const el = ref.current
    const host = el?.parentElement
    if (!el || !host) return

    const observer = new ResizeObserver(() => {
      host.style.setProperty('--seal-header-h', `${el.offsetHeight}px`)
    })
    observer.observe(el)

    return () => observer.disconnect()
  }, [])

  const displayTitle = request.title?.trim() || request.purpose?.trim() || `Yêu cầu đóng dấu ${request.code}`

  return (
    <header
      ref={ref}
      className="static top-0 z-20 -mx-4 -mt-4 mb-5 flex flex-col gap-3.5 border-b border-border/50 bg-canvas/95 px-4 pt-4 pb-3.5 backdrop-blur-md lg:sticky lg:-mx-6 lg:-mt-6 lg:px-6 lg:pt-6"
    >
      {/* Hàng 1: Nút Quay lại + Tiêu đề + Cụm nút thao tác */}
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <div className="flex min-w-0 flex-1 items-center gap-3">
          <Button
            variant="outline"
            size="icon"
            className="size-9 shrink-0 shadow-2xs"
            aria-label="Về danh sách yêu cầu đóng dấu"
            onClick={onBack}
          >
            <ArrowLeft className="size-4" />
          </Button>

          <div className="min-w-0 flex-1">
            <h1
              className="line-clamp-1 text-lg font-bold tracking-tight text-navy sm:text-xl dark:text-foreground"
              title={displayTitle}
            >
              {displayTitle}
            </h1>
            {request.title && request.purpose && (
              <p
                className="line-clamp-1 text-xs text-muted-foreground"
                title={request.purpose}
              >
                Mục đích: {request.purpose}
              </p>
            )}
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
        <div className="flex shrink-0 items-center gap-2">
          <span className="font-mono font-bold text-primary tabular-nums">
            {request.code || '— (Nháp)'}
          </span>
          <SealStatusBadge status={request.status} label={request.status_label} />
        </div>

        <span className="hidden text-border sm:inline" aria-hidden="true">|</span>

        <div className="flex shrink-0 items-center gap-1.5 text-foreground/85">
          <Files className="size-3.5 text-muted-foreground" />
          <span>{request.copies ? `${request.copies} bản` : '—'}</span>
        </div>

        <span className="hidden text-border sm:inline" aria-hidden="true">|</span>

        {request.requester && (
          <div className="flex min-w-0 shrink-0 items-center gap-1.5">
            <User className="size-3.5 text-muted-foreground" />
            <span className="font-medium text-foreground/85">{request.requester}</span>
            {request.requester_role && (
              <span className="text-[11px] text-muted-foreground">
                ({request.requester_role})
              </span>
            )}
          </div>
        )}

        <span className="hidden text-border sm:inline" aria-hidden="true">|</span>

        <div className="flex shrink-0 items-center gap-1.5">
          <CompanyAvatarGroup
            companies={request.companies}
            maxVisible={3}
            showNameWhenSingle={true}
          />
        </div>

        {request.created_at && (
          <>
            <span className="hidden text-border sm:inline" aria-hidden="true">|</span>
            <div className="flex shrink-0 items-center gap-1.5 tabular-nums">
              <Calendar className="size-3.5 text-muted-foreground" />
              <span>{formatDateTime(request.created_at)}</span>
            </div>
          </>
        )}
      </div>
    </header>
  )
}
