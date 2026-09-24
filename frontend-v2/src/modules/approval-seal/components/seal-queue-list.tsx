import { ChevronRight, type LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Card } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import type { SealRequest } from '../types/seal-request'
import { CompanyAvatarGroup } from './company-avatar-group'
import { SealStatusBadge } from './status-pill'

/** Số dòng bày tối đa; phần còn lại đẩy sang liên kết ở chân thẻ. */
const MAX_ROWS = 5

interface SealQueueListProps {
  title: string
  description: string
  icon: LucideIcon
  /** Tông của icon + viền trái mỗi dòng — phân biệt các hàng đợi cạnh nhau. */
  tone?: 'amber' | 'blue' | 'slate'
  rows: SealRequest[]
  /** Tổng số phiếu của hàng đợi (có thể lớn hơn số dòng máy chủ trả về). */
  total?: number
  isLoading?: boolean
  emptyMessage: string
  /** Bày huy hiệu trạng thái — chỉ bật cho danh sách TRỘN nhiều trạng thái. */
  showStatus?: boolean
  /** Đường dẫn của liên kết "Xem tất cả". */
  viewAllTo: string
}

const TONES = {
  amber: { icon: 'text-amber-600 dark:text-amber-400', bar: 'bg-amber-500/70' },
  blue: { icon: 'text-sky-600 dark:text-sky-400', bar: 'bg-sky-500/70' },
  slate: { icon: 'text-muted-foreground', bar: 'bg-border' },
} as const

/**
 * Một HÀNG ĐỢI công việc trên trang Tổng quan Duyệt dấu (Chờ phê duyệt · Chờ
 * đóng dấu · Phiếu gần đây của tôi).
 *
 * ⚠️ Cố ý KHÔNG dùng `DataTable` ở đây, dù `docs/ui/table.md` bắt buộc dùng nó
 * cho màn DANH SÁCH. Đây không phải màn danh sách mà là một ô tóm tắt nằm trong
 * lưới hai cột: khung rộng ~600px, mà bảng cũ có sáu cột. Đo thật trên máy:
 * cột "Công ty đóng dấu" cụt thành «CÔNG TY TNHH DE…» ở cả bốn dòng — bốn ô
 * giống hệt nhau, không phân biệt được dòng nào với dòng nào; tiêu đề văn bản
 * đứt giữa chữ; hai cột cuối (Ngày tạo, Trạng thái) bị đẩy khuất. Cùng lượng
 * dữ liệu đó xếp theo DÒNG thì đọc được hết mà không cần cuộn ngang.
 *
 * Bảng đầy đủ vẫn còn nguyên ở màn danh sách `/approval-seal/requests`, nơi nó
 * có cả chiều ngang trang.
 */
export function SealQueueList({
  title,
  description,
  icon: Icon,
  tone = 'slate',
  rows,
  total,
  isLoading,
  emptyMessage,
  showStatus,
  viewAllTo,
}: SealQueueListProps) {
  const shown = rows.slice(0, MAX_ROWS)
  const count = total ?? rows.length
  const rest = count - shown.length
  const t = TONES[tone]

  return (
    //  KHÔNG `h-full`: thẻ cao theo số dòng của chính nó. Kéo bằng nhau thì
    //  hàng đợi một dòng nằm cạnh hàng đợi bốn dòng chừa một mảng trắng lớn.
    //
    //  `min-w-0`: ô lưới mặc định KHÔNG co xuống dưới bề rộng nội dung, mà tên
    //  pháp nhân ở đây dài 25-45 ký tự — thiếu chữ này thì ở khổ điện thoại cả
    //  TRANG sinh thanh cuộn ngang và liên kết "Xem tất cả" bị đẩy ra ngoài mép.
    <Card className="flex min-w-0 flex-col gap-0 p-0">
      <div className="flex items-start justify-between gap-3 border-b px-4 py-3">
        <div className="flex min-w-0 items-start gap-2.5">
          <Icon className={cn('mt-0.5 size-4.5 shrink-0', t.icon)} />
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="truncate text-sm font-semibold text-navy dark:text-foreground">
                {title}
              </span>
              {count > 0 && (
                <span className="shrink-0 rounded-full bg-muted px-1.5 py-0.5 text-[11px] font-semibold tabular-nums text-muted-foreground">
                  {count}
                </span>
              )}
            </div>
            <p className="truncate text-xs text-muted-foreground">{description}</p>
          </div>
        </div>
        <Link
          to={viewAllTo}
          className="flex shrink-0 items-center gap-0.5 text-xs font-medium text-muted-foreground hover:text-primary"
        >
          Xem tất cả
          <ChevronRight className="size-3.5" />
        </Link>
      </div>

      {isLoading ? (
        <div className="flex flex-col gap-3 p-4">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-11 w-full" />
          ))}
        </div>
      ) : shown.length === 0 ? (
        <p className="px-4 py-8 text-center text-sm text-muted-foreground">{emptyMessage}</p>
      ) : (
        <ul className="flex flex-col divide-y">
          {shown.map((row) => (
            <li key={row.id}>
              <QueueRow row={row} bar={t.bar} showStatus={showStatus} />
            </li>
          ))}
        </ul>
      )}

      {/*  Chỉ nói "còn n phiếu nữa" khi THẬT SỰ còn — câu này là lời hứa có thêm
          dữ liệu ở đường dẫn kia, bày khi rest = 0 là hứa suông. */}
      {rest > 0 && (
        <Link
          to={viewAllTo}
          className="border-t px-4 py-2.5 text-center text-xs font-medium text-muted-foreground hover:text-primary"
        >
          Còn {rest} phiếu nữa
        </Link>
      )}
    </Card>
  )
}

/**
 * Một dòng phiếu: mã + tiêu đề văn bản ở hàng trên, công ty · người tạo · ngày ở
 * hàng dưới. Cả dòng là một liên kết nên bấm chỗ nào cũng mở được chi tiết —
 * khác bảng cũ bắt bấm đúng ô.
 */
function QueueRow({
  row,
  bar,
  showStatus,
}: {
  row: SealRequest
  bar: string
  showStatus?: boolean
}) {
  return (
    <Link
      to={appRoutes.approvalSeal.detail(row.id)}
      className="group flex items-start gap-3 px-4 py-2.5 transition-colors hover:bg-accent/50"
    >
      <span className={cn('mt-1 h-8 w-0.5 shrink-0 rounded-full', bar)} aria-hidden="true" />
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <div className="flex min-w-0 items-baseline gap-2">
          <span className="shrink-0 text-xs font-semibold tabular-nums text-primary">
            {row.code}
          </span>
          {/*  Tiêu đề văn bản trước, mục đích chỉ là đường lui: phiếu nào cũng có
              mục đích nhưng nó hay mở đầu bằng "Đóng dấu " nên bốn dòng liền
              nhau trông giống hệt nhau. */}
          <span className="truncate text-sm font-medium text-foreground group-hover:text-primary">
            {row.title || row.purpose || '—'}
          </span>
        </div>
        <div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted-foreground">
          {/*  `flex` + `overflow-hidden` chứ không phải `truncate` trên một thẻ
              inline: bên trong là một khối flex (ảnh + tên), mà `truncate` chỉ
              cắt được chữ nằm THẲNG trong chính nó. Thiếu khung chặn này thì
              tên pháp nhân đẩy cả dòng tràn ra ngoài thẻ. */}
          <span className="flex min-w-0 max-w-[15rem] items-center overflow-hidden">
            <CompanyAvatarGroup companies={row.companies} maxVisible={3} />
          </span>
          {row.requester && (
            <>
              <span aria-hidden="true">·</span>
              <span className="truncate">{row.requester}</span>
            </>
          )}
          {row.created_at && (
            <>
              <span aria-hidden="true">·</span>
              <span className="shrink-0 tabular-nums">{formatShortDate(row.created_at)}</span>
            </>
          )}
        </div>
      </div>
      {showStatus && (
        <span className="mt-0.5 shrink-0">
          <SealStatusBadge status={row.status} label={row.status_label} />
        </span>
      )}
    </Link>
  )
}

/** '2026-09-18T09:00' -> '18/09'; cùng năm nên bỏ năm cho đỡ chật dòng. */
function formatShortDate(value: string): string {
  const [date] = value.replace(' ', 'T').split('T')
  const [, m, d] = date.split('-')
  return m && d ? `${d}/${m}` : value
}
