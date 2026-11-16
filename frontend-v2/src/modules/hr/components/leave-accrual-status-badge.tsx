import { Hourglass, TriangleAlert } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/shared/ui/tooltip'
import { cn } from '@/shared/utils/cn'
import type { LeaveAccrualInfo } from '../types/leave'
import { getAccrualStartHint, getAccrualTone, getContractActionHint } from '../utils/leave-accrual-status'

interface LeaveAccrualStatusBadgeProps {
  info: LeaveAccrualInfo | null | undefined
  /**
   * Chỉ vẽ BIỂU TƯỢNG, chữ dời vào gợi ý rê chuột. Dùng ở cột hẹp (cột Họ tên 200px của ma trận): nhãn chữ đầy đủ
   * ăn mất nửa ô và tên người bị cắt còn ba chữ cái.
   */
  compact?: boolean
  /**
   * Ẩn nhãn hổ phách *chưa đủ HĐLĐ* (mã 3, 4); nhãn tông mờ vẫn hiện. Bảng bật khi quá nửa số người thiếu — xem
   * `summarizeMissingContract`; lúc đó dải đếm đầu bảng nói thay.
   */
  hideContractWarning?: boolean
  className?: string
}

/**
 * Nhãn nhỏ tình trạng tích phép của loại `MONTHLY_AFTER` (duoc-CR-762), đặt cạnh tên người. Chữ là
 * `accrual_status_label` của API (không gõ nhãn ở giao diện); màu theo tông của mã (`getAccrualTone`):
 * mờ cho thử việc / HĐ dịch vụ / chưa tới ngày chính thức, hổ phách cho chưa đủ HĐLĐ.
 *
 * Người đang tích không có nhãn: tô nhãn cho cả công ty là nhãn mất nghĩa — gợi ý *Tích từ …* gắn vào ô bằng
 * `AccrualStartTooltip`. Nhãn dài (vd HĐ dịch vụ / cộng tác viên) bị cắt ở bề ngang cố định, rê chuột ra câu đủ.
 */
export function LeaveAccrualStatusBadge({
  info,
  compact = false,
  hideContractWarning = false,
  className,
}: LeaveAccrualStatusBadgeProps) {
  const tone = getAccrualTone(info?.accrual_status)
  const label = info?.accrual_status_label?.trim()
  if (!label || (tone !== 'muted' && tone !== 'warn')) return null
  const warn = tone === 'warn'
  if (warn && hideContractWarning) return null

  const action = getContractActionHint(info?.accrual_status)
  const fullText = action ? `${label}. ${action}` : label
  const Icon = warn ? TriangleAlert : Hourglass

  return (
    <TooltipProvider delayDuration={150}>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge
            variant="outline"
            //  `tabIndex` để bàn phím cũng mở được gợi ý; `aria-label` đọc trọn câu cho trình đọc màn hình.
            tabIndex={0}
            aria-label={fullText}
            className={cn(
              'max-w-56',
              warn
                ? 'border-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-400'
                : 'font-normal text-muted-foreground',
              compact && 'px-1',
              className,
            )}
          >
            {compact ? <Icon aria-hidden="true" /> : <span className="truncate">{label}</span>}
          </Badge>
        </TooltipTrigger>
        <TooltipContent>{fullText}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

interface AccrualStartTooltipProps {
  info: LeaveAccrualInfo | null | undefined
  /** MỘT phần tử DOM — gợi ý gắn thẳng vào nó qua `asChild`. */
  children: React.ReactElement
}

/**
 * Gắn gợi ý *Tích từ dd/mm/yyyy* vào phần tử con khi người đó ĐANG TÍCH; các trường hợp khác trả nguyên phần tử con,
 * không bọc gì — không thêm chữ nào lên màn, đúng ý "đang tích thì không có gì đặc biệt".
 */
export function AccrualStartTooltip({ info, children }: AccrualStartTooltipProps) {
  const hint = getAccrualStartHint(info)
  if (!hint) return children
  return (
    <TooltipProvider delayDuration={150}>
      <Tooltip>
        <TooltipTrigger asChild>{children}</TooltipTrigger>
        <TooltipContent>{hint}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
