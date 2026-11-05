import { ArrowRight } from 'lucide-react'

import type { LeaveCloseYearReviewRow } from '../types/leave'
import { formatCloseYearDays } from '../utils/format-close-year-days'

interface LeaveCloseYearReviewCardProps {
  row: LeaveCloseYearReviewRow
}

/**
 * Một dòng của hộp Đối chiếu kết sổ phép ở khổ điện thoại (duoc-CR-721) — xem `DataTableProps.mobileCard`.
 *
 * ⚠️ **Số cũ → số mới đứng CHUNG một dòng có mũi tên**, chênh lệch ngay sau trong ngoặc. Hộp này chỉ để
 * trả lời *"kết sổ đã làm gì với quỹ của người này"*, nên cặp trước / sau là thứ phải đọc được trong một
 * lần nhìn; tách ba ô xếp dọc thì mắt phải tự ghép lại phép so sánh.
 *
 * Phần sang năm sau là dòng RIÊNG có nhãn: nó là câu trả lời cho câu hỏi khác (*"năm sau được cộng gì"*)
 * và loại đích có thể khác loại nguồn. Thẻ không bấm được — bảng cũng không có thao tác nào trên dòng.
 */
export function LeaveCloseYearReviewCard({ row }: LeaveCloseYearReviewCardProps) {
  return (
    <div className="min-w-0 space-y-1.5 text-sm">
      <div className="flex items-start justify-between gap-2">
        <span className="min-w-0">
          <span className="block truncate font-medium text-foreground">{row.employee_name}</span>
          <span className="block text-xs font-medium text-sky-600 tabular-nums dark:text-sky-400">
            {row.employee_code}
          </span>
        </span>
        <span className="shrink-0 rounded border px-1.5 py-0.5 text-xs break-words text-foreground">
          {row.source_type_name}
        </span>
      </div>

      {/*  Chữ liền dòng có khoảng trắng THẬT giữa các vế (không dùng `gap` của flex): trình đọc màn hình và
           bôi đen sao chép đều ra "Số cũ 8 → số mới 3", không dính chữ thành "Số cũ8số mới3". */}
      <p className="tabular-nums">
        <span className="text-muted-foreground">Số cũ</span> {formatCloseYearDays(row.before_days)}{' '}
        <ArrowRight className="inline size-3.5 align-[-2px] text-muted-foreground" aria-label="thành" />{' '}
        <span className="text-muted-foreground">số mới</span>{' '}
        <span className="font-semibold text-primary">{formatCloseYearDays(row.after_days)}</span>{' '}
        <span className="text-muted-foreground">(chênh {formatCloseYearDays(row.diff_days)})</span>
      </p>

      <p className="text-muted-foreground">
        Sang <span className="text-foreground">{row.dest_type_name || 'Chưa khai'}</span>, cộng vào năm sau{' '}
        <span className="font-medium text-foreground tabular-nums">{formatCloseYearDays(row.credited_days)}</span>{' '}
        ngày
      </p>
    </div>
  )
}
